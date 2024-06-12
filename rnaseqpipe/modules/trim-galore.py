"""
Adapter and Quality Trimming using Trim Galore
"""

from modal import App, Image
from typing import List

from rnaseqpipe.modules.utils import PLID
from rnaseqpipe.config import vol, fastqc_img

app = App("rnaseq-trimgalore")

CPUS = 8.0

trimgalore_img = (
    fastqc_img(Image.debian_slim())
    .apt_install("cutadapt", "curl")
    .run_commands(
        "curl -fsSL https://github.com/FelixKrueger/TrimGalore/archive/0.6.10.tar.gz -o trim_galore.tar.gz",
        "tar xvzf trim_galore.tar.gz",
    )
)


@app.function(cpu=CPUS, volumes={"/data": vol}, image=trimgalore_img)
def trimgalore(plid: str, read_files: List[str]):

    assert len(read_files) in [1, 2], "TrimGalore!: Invalid number of read files"

    trimgalore_cmd = f"""/TrimGalore-0.6.10/trim_galore {' '.join(map(str, read_files))} \
        --cores {int(CPUS)} \
        --gzip {"--paired" if len(read_files) == 2 else ''}"""

    print(f"Running TrimGalore: \n\t{trimgalore_cmd}")

    import subprocess

    subprocess.run(trimgalore_cmd, check=True, shell=True)

    vol.commit()

    print("TrimGalore completed successfully!")

    return


@app.local_entrypoint()
def run():
    from pathlib import Path

    plid = PLID("pl-9e233179-57c0-43fb-b514-1f98745ceacb")
    read_dir = Path("reads")

    trimgalore.remote(
        plid, [Path(f"/data/{plid}") / read_dir / Path("DRR023796.fastq")]
    )
