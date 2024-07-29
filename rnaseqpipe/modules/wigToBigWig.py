"""
Module to convert wig to bigwig

Main command: wigToBigWig <in.wig> <chrom.sizes> <out.bw>

Run this on modal with: modal run rnaseqpipe/modules/wigToBigWig.py
"""

from modal import Image, App
from rnaseqpipe.config import vol

app = App("rnaseq-wigToBigWig")

image = (
    Image.debian_slim()
    .apt_install("wget")
    .run_commands(
        "wget https://hgdownload.cse.ucsc.edu/admin/exe/linux.x86_64/wigToBigWig",
        "chmod +x wigToBigWig",
        "mv wigToBigWig /usr/local/bin/",
    )
    .apt_install("libcurl4-openssl-dev")
)

CHROM_SIZES = """I	230218
II	813184
III	316620
IV	1531933
IX	439888
V	576874
VI	270161
VII	1090940
VIII	562643
X	745751
XI	666816
XII	1078177
XIII	924431
XIV	784333
XV	1091291
XVI	948066"""


@app.function(image=image, volumes={"/data": vol})
def wigToBigWig(
    wig_file: str,
    chrom_sizes: str = "/data/chrom.sizes",
    output_file: str = "",
    force_recompute: bool = False,
):

    print(
        "wigToBigWig args =====\n",
        wig_file,
        chrom_sizes,
        output_file,
        force_recompute,
        "\n",
        "====================",
    )

    import subprocess
    import os

    # Check if output file is provided
    if not output_file:
        output_file = wig_file.replace(".wig", ".bw")

    # Check if conversion has already been done
    if os.path.exists(output_file) and not force_recompute:
        print(f"{output_file} already exists! Skipping conversion.")
        return True

    if not os.path.exists(chrom_sizes):
        with open(chrom_sizes, "w") as f:
            f.write(CHROM_SIZES)
            vol.commit()

    command = f"wigToBigWig {wig_file} {chrom_sizes} {output_file}"

    try:
        subprocess.run(
            command,
            check=True,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"Successfully converted {wig_file} to {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error converting {wig_file} to bigwig: {e.stderr.decode()}")
        return False


@app.local_entrypoint()
def main():

    plid = "pl-ERR11502246"

    data = f"/data/{plid}/staralign"

    chrom_sizes = f"/data/chrom.sizes"

    wig1 = f"{data}/Signal.Unique.str1.out.wig"
    bigwig1 = wig1.replace(".wig", ".bw")

    wig2 = f"{data}/Signal.Unique.str2.out.wig"
    bigwig2 = wig2.replace(".wig", ".bw")

    result = list(
        wigToBigWig.starmap(
            [(wig1, chrom_sizes, bigwig1), (wig2, chrom_sizes, bigwig2)]
        )
    )
    print(f"Conversion result: {result}")
