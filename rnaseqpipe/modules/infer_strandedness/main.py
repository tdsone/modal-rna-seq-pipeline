"""
Infers the strandedness of the reads to determine, if the reads can be mapped to the correct strand.

This is done in two steps:
1. Subsample X% of the reads from the fastq file to reduce computation time.
2. Run salmon to infer the strandedness of the reads.

Step 1: Subsample reads to reduce compute

Step 2: Run Salmon to infer strandedness

Open Question
1. What to do with multiple files? E.g. paired RNA-seq
"""

from modal import App, Image, Secret, method, build, enter, Cls, Volume
from typing import List

from rnaseqpipe.config import vol, salmon_image
from rnaseqpipe.modules.utils import PLID

app = App("rnaseq-strandedness")

CPUS = 8

image = (
    Image.from_dockerfile("rnaseqpipe/modules/infer_strandedness/Dockerfile")
    .apt_install("wget", "tar", "libc6")
    .run_commands(
        "wget https://github.com/stjude-rust-labs/fq/releases/download/v0.11.0/fq-0.11.0-x86_64-unknown-linux-gnu.tar.gz"
    )
    .run_commands("tar -xvf fq-0.11.0-x86_64-unknown-linux-gnu.tar.gz")
    .run_commands(
        "wget https://github.com/COMBINE-lab/salmon/releases/download/v1.10.0/salmon-1.10.0_linux_x86_64.tar.gz"
    )
    .run_commands("tar -xzf salmon-1.10.0_linux_x86_64.tar.gz")
)


@app.function(image=image, volumes={"/data": vol}, cpu=CPUS, timeout=60 * 10)
def infer_strandedness(
    plid: PLID, read_files: List[str], assembly_name: str, force_recompute: bool = False
):
    """
    Run salmon to infer strandedness
    - can be infered from produced lib_format_counts.json

    Library type meaning is explained here:
    - https://salmon.readthedocs.io/en/latest/library_type.html
    """

    import subprocess
    import os

    vol.reload()

    # Create the directory for subsampled reads
    subsampled_path = f"/data/{plid}/reads/subsampled"
    result_path = f"/data/{plid}/strandedness/"

    # Check if lib_format_counts.json already exists. If so infer_strandedness was already run and we can return
    if os.path.exists(f"{result_path}/lib_format_counts.json") and not force_recompute:
        print(
            f"{plid}:infer_strandedness: lib_format_counts.json already exists! Skipping.\nIf you want to recompute, set force_recompute=True."
        )
        return True

    os.makedirs(subsampled_path, exist_ok=True)

    subsampled_files = [
        os.path.join(subsampled_path, os.path.basename(f)) for f in read_files
    ]

    subsample_cmd = f"""/fq-0.11.0-x86_64-unknown-linux-gnu/fq subsample {' '.join(read_files)} \
        --record-count 60000 \
        --r1-dst {subsampled_files[0]} {f'--r2-dst {subsampled_files[1]}' if len(read_files) == 2 else ''}"""

    print(f"Subsampling reads: \n\t{subsample_cmd}")

    subprocess.run(subsample_cmd, check=True, shell=True)

    vol.commit()

    os.makedirs(result_path, exist_ok=True)

    vol.commit()

    # Configure salmon command based on the number of input files (single vs. paired)
    if len(read_files) == 1:
        salmon_lib_spec = ["-r", subsampled_files[0]]
    elif len(read_files) == 2:
        salmon_lib_spec = ["-1", subsampled_files[0], "-2", subsampled_files[1]]
    else:
        raise ValueError("Unsupported number of read files. Expected 1 or 2.")

    prefix = result_path  # Output directory for Salmon

    salmon_cmd = (
        [
            "/salmon-latest_linux_x86_64/bin/salmon",
            "quant",
            "-i",
            f"/data/salmon_index/{assembly_name}/transcripts_index",
            "--libType",
            "A",  # 'Auto' determining of library type
            "--threads",
            str(CPUS),
        ]
        + salmon_lib_spec
        + ["--validateMappings", "-o", prefix, prefix]
    )

    # Execute Salmon quantification
    process = subprocess.Popen(
        salmon_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()

    # Check for errors
    if process.returncode != 0:
        raise Exception(f"Salmon quantification failed: {stderr.decode('utf-8')}")

    print(f"Output of salmon quant: {stdout.decode('utf-8')}")

    # Return path to results for further processing
    return True


@app.local_entrypoint()
def run():
    from rnaseqpipe.modules.utils import PLID
    from pathlib import Path

    plid = PLID("pl-SRR22857020")

    res = infer_strandedness.remote(
        plid,
        read_files=[f"/data/{plid}/reads/SRR22857020.fastq"],
        assembly_name="R64-1-1",
        force_recompute=True,
    )

    pass
