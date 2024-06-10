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


@app.function(image=salmon_image, volumes={"/data": vol}, cpu=CPUS)
def infer_strandedness(plid: PLID, read_files: List[str], assembly_name: str):
    """
    Run salmon to infer strandedness
    - can be infered from produced lib_format_counts.json

    Library type meaning is explained here:
    - https://salmon.readthedocs.io/en/latest/library_type.html
    """

    import subprocess
    import os

    # Subsample reads before mapping to be faster

    # Ensure the result directory exists
    result_path = f"/data/{plid}/strandedness/"

    os.makedirs(result_path, exist_ok=True)

    # Construct command for Salmon quantification

    """

    """

    prefix = result_path  # TODO: does it work this way?

    read_files = (
        [
            "-r",
            read_files[0],
        ]
        if len(read_files) == 1
        else [
            "-1",
            read_files[0],
            "-2",
            read_files[1],
        ]
    )

    salmon_cmd = (
        [
            "/salmon-latest_linux_x86_64/bin/salmon",
            "quant",
            "-i",
            f"/data/salmon_index/{assembly_name}/transcripts_index",
            "--libType",
            "A",  # stands for "auto"
            "--threads",
            str(CPUS),
        ]
        + read_files
        + [
            "--validateMappings",
            "-o",
            prefix,
        ]
    )

    # Execute the constructed command
    process = subprocess.Popen(
        salmon_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()

    # Handle process output and errors
    if process.returncode != 0:
        raise Exception(f"Salmon quantification failed: {stderr.decode('utf-8')}")

    print(f"Output of salmon quant: {stdout.decode('utf-8')}")

    # Standard practice to return the path to result, allowing subsequent steps in a pipeline to access results
    return result_path


@app.local_entrypoint()
def run():
    from rnaseqpipe.modules.utils import PLID
    from pathlib import Path

    plid = PLID("pl-9e233179-57c0-43fb-b514-1f98745ceacb")

    res = infer_strandedness.remote(
        plid, [f"/data/{plid}/reads/DRR023796.fastq"], "R64-1-1"
    )

    pass
