"""
Adapter and Quality Trimming using Trim Galore
"""

from modal import App, Image
from typing import List

from rnaseqpipe.modules.utils import PLID
from rnaseqpipe.config import vol, fastqc_img

app = App("rnaseq-trim-galore")

CPUS = 8.0

trimgalore_img = (
    fastqc_img(Image.debian_slim())
    .apt_install("cutadapt", "curl")
    .run_commands(
        "curl -fsSL https://github.com/FelixKrueger/TrimGalore/archive/0.6.10.tar.gz -o trim_galore.tar.gz",
        "tar xvzf trim_galore.tar.gz",
    )
)


@app.function(cpu=CPUS, volumes={"/data": vol}, image=trimgalore_img, timeout=600)
def trimgalore(plid: str, read_files: List[str], force_recompute: bool = False):
    print(f"Running TrimGalore! for plid {plid}...")

    assert len(read_files) in [1, 2], "TrimGalore!: Invalid number of read files"

    vol.reload()

    # Check if trimgalore result files already exist
    import os

    if os.path.exists(f"/data/{plid}/trimgalore") and not force_recompute:
        files = os.listdir(f"/data/{plid}/trimgalore")
        print(f"{plid}:trim-galore: Files in trimgalore directory: {files}")
        sample_id = str(read_files[0]).split("/")[-1].split(".")[0]

        if len(read_files) == 2:
            if (
                (f"{sample_id}_val_1.fq" in files)
                and f"{sample_id}_val_2.fq" in files
                and f"{sample_id}_1.fastq.gz_trimming_report.txt" in files
                and f"{sample_id}_2.fastq.gz_trimming_report.txt" in files
            ):
                print(
                    f"{plid}:trim-galore: Trimgalore results already exist! Returning without action."
                )
                return True
        elif len(read_files) == 1:
            if (
                f"{sample_id}_trimmed.fq.gz" in files
            ) and f"{sample_id}.fastq.gz_trimming_report.txt" in files:
                print(
                    f"{plid}:trim-galore: Trimgalore results already exist! Returning without action."
                )
                return True

    trimgalore_cmd = f"""/TrimGalore-0.6.10/trim_galore {' '.join(map(str, read_files))} \
        --cores {int(CPUS)} \
        {"--paired" if len(read_files) == 2 else ''} \
        -o /data/{plid}/trimgalore \
        --dont_gzip
        """

    print(f"Running TrimGalore: \n\t{trimgalore_cmd}")

    import subprocess

    subprocess.run(trimgalore_cmd, check=True, shell=True)

    vol.commit()

    print("TrimGalore completed successfully!")

    return True


@app.local_entrypoint()
def run():
    from pathlib import Path

    plid = PLID("pl-ERR11502248")

    trimgalore.remote(plid, [f"/data/{plid}/reads"])
