from modal import Image, App
from typing import List

from config import vol

app = App("rnaseq-fastqc")
fastqc_img = Image.debian_slim().pip_install("azure-storage-blob")


@app.function(
    image=fastqc_img,
    volumes={"/data": vol},
)
def fastqc(plid: str, read_files: List[str]):
    """Run FastQC on the read files.

    Args:
        plid (str): pipeline ID
        read_files (List[str]): list of read files (2 max for paired reads)
    """

    import subprocess

    cmd = [
        "fastqc",
        *read_files,
        "-o",
        "/data/fastqc",
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Succeeded: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to run FastQC: {e.stderr}")
        raise
