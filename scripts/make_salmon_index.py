"""
Script that generates the salmon index and stores is in a shared modal volume

./bin/salmon index -t transcripts.fa -i transcripts_index --decoys decoys.txt -k 31
"""

from modal import App, Volume, Image
from rnaseqpipe.config import vol, salmon_image

app = App("salmon-index")

salmon_image = salmon_image.run_commands(
    "chmod +x /salmon-latest_linux_x86_64/bin/salmon"
)


@app.function(image=salmon_image, volumes={"/data": vol})
def make_salmon_index(assembly_name: str, transcriptome: str):
    import subprocess
    import os

    salmon_index_dir = f"/data/salmon_index/{assembly_name}"
    os.makedirs(salmon_index_dir, exist_ok=True)

    cmd = [
        "/salmon-latest_linux_x86_64/bin/salmon",
        "index",
        "-t",
        f"{salmon_index_dir}/decoy/gentrome.fa.gz",
        "-i",
        f"{salmon_index_dir}/transcripts_index",
        "--decoys",
        f"{salmon_index_dir}/decoy/decoys.txt",
        "-k",
        "31",
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        vol.commit()
        print(f"Succeeded: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to run Salmon index: {e.stderr}")
        raise e


@app.local_entrypoint()
def run():
    assembly_name = "R64-1-1"
    transcriptome_url = "https://ftp.ensembl.org/pub/release-112/fasta/saccharomyces_cerevisiae/cdna/Saccharomyces_cerevisiae.R64-1-1.cdna.all.fa.gz"

    make_salmon_index.remote(
        assembly_name=assembly_name,
        transcriptome=transcriptome_url,
    )
    pass
