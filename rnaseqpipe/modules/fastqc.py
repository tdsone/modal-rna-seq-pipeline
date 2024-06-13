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
)
def fastqc(plid: str, read_files: List[str]):
    """Run FastQC on the read files.

    Args:
        plid (str): pipeline ID
        read_files (List[str]): list of read files (2 max for paired reads)
    """

    print(f"{plid}:rnaseq-fastqc:fastqc: Running FastQC!")
    vol.reload()

    import subprocess
    import os

    result_path = f"/data/{plid}/fastqc/"

    os.makedirs(result_path, exist_ok=True)

    read_files_str = " ".join(map(str, read_files))

    print("read files: ", read_files_str)
    print("result path: ", result_path)

    cmd = ["/FastQC/fastqc", read_files_str, "--outdir", result_path]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

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

    plid = PLID("pl-9e233179-57c0-43fb-b514-1f98745ceacb")
    read_dir = Path("reads")

    fastqc.remote(plid, [Path(f"/data/{plid}") / read_dir / Path("DRR023796.fastq")])
