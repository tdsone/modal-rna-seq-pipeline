"""
This files checks the quality of the reads and creates a report using FastQC.

Usage doc for FastQC here: https://www.bioinformatics.babraham.ac.uk/projects/fastqc/INSTALL.txt
"""

from modal import Image, App
from typing import List

from rnaseqpipe.config import vol

app = App("rnaseq-fastqc")
fastqc_img = (
    Image.debian_slim()
    .apt_install("default-jre")
    .run_commands("java -version")
    .apt_install("wget", "unzip")
    .run_commands(
        "wget https://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v0.12.1.zip",
        "unzip fastqc_v0.12.1.zip",
    )
)


@app.function(
    image=fastqc_img,
    volumes={"/data": vol},
    timeout=60 * 100,
)
def fastqc(plid: str, read_files: List[str], force_recompute: bool = False):
    """Run FastQC on the read files.

    Args:
        plid (str): pipeline ID
        read_files (List[str]): list of (un-)zipped read files (2 max for paired reads)
    """

    print(f"{plid}:rnaseq-fastqc:fastqc: Running FastQC!")
    vol.reload()

    import subprocess
    import os

    result_path = f"/data/{plid}/fastqc/"

    sample_id = None
    if len(read_files) == 1:
        sample_id = read_files[0].split("/")[-1].split(".")[0]
    elif len(read_files) == 2:
        sample_id = read_files[0].split("/")[-1].split("_")[0]
    else:
        raise Exception(f"{plid}:fastqc: Invalid number of read files")

    # Check if the results files can already be skipped
    if os.path.exists(f"{result_path}stdin_fastqc.html") and not force_recompute:
        print(f"{plid}:fastqc: FastQC results already exist! Skipping.")
        return True

    os.makedirs(result_path, exist_ok=True)

    read_files_str = " ".join(map(str, read_files))

    print("read files: ", read_files_str)
    print("result path: ", result_path)

    cmd = f"zcat {read_files_str} | /FastQC/fastqc stdin --outdir {result_path}"

    try:
        result = subprocess.run(cmd, shell=True)

        vol.commit()

        print(f"Succeeded: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to run FastQC: {e.stderr}")
        raise e

    return True


@app.local_entrypoint()
def run():
    from rnaseqpipe.modules.utils import PLID
    from pathlib import Path

    plid = PLID("pl-DRR023785")

    fastqc.remote(
        plid, [f"/data/{plid}/reads/DRR023785.fastq.gz"], force_recompute=False
    )
