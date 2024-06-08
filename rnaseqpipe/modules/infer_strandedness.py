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

CPUS = 8.0


@app.function(image=salmon_image, volumes={"/data": vol}, cpu=CPUS)
def infer_strandedness(plid: PLID, read_files: List[str]):
    # Run salmon to infer strandedness using subprocess for command execution
    import subprocess
    import os

    # Assert that the index file is available

    # Ensure the result directory exists
    result_path = f"/data/{plid}/strandedness/"
    os.makedirs(result_path, exist_ok=True)

    # Construct command for Salmon quantification

    """
    From nf: 

    salmon quant \\
    --geneMap $gtf \\
    --threads $task.cpus \\
    --libType=$strandedness \\
    $reference \\
    $input_reads \\
    $args \\
    -o $prefix

    
    ./bin/salmon quant -i transcripts_index -l <LIBTYPE> -1 reads1.fq -2 reads2.fq --validateMappings -o transcripts_quant
    ./bin/salmon quant -i transcripts_index -l <LIBTYPE> -r reads.fq --validateMappings -o transcripts_quant
    """

    gtf_path = None
    reference = None
    input_reads = None
    args = None  # TODO what args?
    prefix = result_path  # TODO: does it work this way?

    salmon_cmd = [
        "/salmon-latest_linux_x86_64/bin/salmon",
        "quant",
        "--geneMap",
        gtf_path,
        "--threads",
        CPUS,
        "--libType",
        "A",  # stands for "auto"
        reference,
        input_reads,
        args,
        "-o",
        prefix,
    ]

    # Execute the constructed command
    process = subprocess.Popen(
        salmon_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
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

    res = infer_strandedness.remote(plid, ["file1", "file2"])

    pass
