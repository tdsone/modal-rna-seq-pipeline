from modal import (
    App,
    Image,
    Secret,
    method,
    build,
    enter,
    Cls,
    Volume,
    Function,
    functions,
)
from typing import Tuple, List
from config import vol

app = App("rna-seq")

pipeline_img = Image.debian_slim().pip_install("azure-storage-blob", "tqdm")


@app.function(
    image=pipeline_img,
    volumes={"/data": vol},
    secrets=[Secret.from_name("azure-connect-str")],
)
def run_pipeline(sample_id: Tuple[str, List[str]], no_cache: bool = False):
    """
    Example Input:
        sample_id example paired: ("DRR023784", ["DRR023784_1.fastq.gz", "DRR023784_2.fastq.gz"])
        sample_id example unpaired: ("DRR023784", ["DRR023784.fastq.gz"])
    """

    # Create a pipeline ID
    plid = f"pl-{sample_id[0]}"

    print(f"Running pipeline for {plid} with input {sample_id}...")

    import os
    from azure.storage.blob import BlobServiceClient

    connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    # Get the client for the container
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    # Name of the container
    container_name = "rna-seq-reads"

    # Get the client for the container
    container_client = blob_service_client.get_container_client(container_name)

    # Download the blob(s)
    import os

    print(f"\n{plid}: Downloading files...")

    os.makedirs(f"/data/{plid}/reads", exist_ok=True)
    for file in sample_id[1]:
        file_empty = False
        if os.path.exists(f"/data/{plid}/reads/{file}"):
            file_empty = os.stat(f"/data/{plid}/reads/{file}").st_size == 0

        if not os.path.exists(f"/data/{plid}/reads/{file}") or no_cache or file_empty:
            if os.path.exists(f"/data/{plid}/reads/{file}") and file_empty:
                os.remove(f"/data/{plid}/reads/{file}")

            blob_client = container_client.get_blob_client(file)
            print(f"{plid}: Downloading {file}...")
            with open(f"/data/{plid}/reads/{file}", "wb") as f:
                f.write(blob_client.download_blob().readall())
                vol.commit()

        else:
            print(f"File {file} already exists. Skipping download.")

    print(f"{plid}: Files downloaded successfully!")

    """
    In parallel, run: 
    - Read Quality Check: FastQC
    - Inferring Strandednes: fq and salmon
    - Read Trimming: Trim Galore!
    """

    vol.reload()

    FASTQC = "fastqc"
    INFER_STRANDEDNESS = "infer_strandedness"
    TRIM_GALORE = "trimgalore"

    fastqc = Function.lookup("rnaseq-fastqc", FASTQC)
    infer_strandedness = Function.lookup("rnaseq-strandedness", INFER_STRANDEDNESS)
    trimgalore = Function.lookup("rnaseq-trim-galore", TRIM_GALORE)

    fastqc_handle = fastqc.spawn(
        plid=plid, read_files=[f"/data/{plid}/reads/{name}" for name in sample_id[1]]
    )

    infer_strandedness_handle = infer_strandedness.spawn(
        plid=plid,
        read_files=[f"/data/{plid}/reads/{read_file}" for read_file in sample_id[1]],
        assembly_name="R64-1-1",
    )

    trimgalore_handle = trimgalore.spawn(
        plid=plid, read_files=[f"/data/{plid}/reads/{name}" for name in sample_id[1]]
    )

    import time

    results = {
        FASTQC: "running",
        INFER_STRANDEDNESS: "running",
        TRIM_GALORE: "running",
    }

    while True:
        print(
            f"{plid}: Waiting for {FASTQC}, {INFER_STRANDEDNESS} and {TRIM_GALORE} to finish..."
        )
        try:
            result_fqc = fastqc_handle.get(timeout=10)
            result_inf_str = infer_strandedness_handle.get(timeout=10)
            result_trimg = trimgalore_handle.get(timeout=10)

            if results[FASTQC] == "running" and type(result_fqc) == bool:
                print(f"{plid}:{FASTQC}: Completed successfully!")
                results[FASTQC] = "completed"

            if (
                results[INFER_STRANDEDNESS] == "running"
                and type(result_inf_str) == bool
            ):
                print(f"{plid}:{INFER_STRANDEDNESS}: Completed successfully!")
                results[INFER_STRANDEDNESS] = "completed"

            if results[TRIM_GALORE] == "running" and type(result_trimg) == bool:
                print(f"{plid}:{TRIM_GALORE}: Completed successfully!")
                results[TRIM_GALORE] = "completed"

            if all([v == "completed" for v in results.values()]):
                break

        except TimeoutError as e:
            print(e)
        time.sleep(3)

    # Run the alignment
    STARAlign = Cls.lookup("rnaseq-staralign", "STARAlign")

    print(f"{plid}: Spawned STARAlign...")

    align_handle = STARAlign().align.spawn(
        plid=plid,
        read_files=[
            f"/data/{plid}/trimgalore/{name.split('.')[0]}_trimmed.fq.gz"
            for name in sample_id[1]
        ],
    )

    while True:
        result_staralign = align_handle.get(timeout=10)

        if type(result_staralign) == bool:
            print(f"{plid}: STARAlign: Completed successfully!")
            break

    print("Pipeline completed successfully!")


distr_img = Image.debian_slim().pip_install("azure-storage-blob")


@app.function(image=distr_img, secrets=[Secret.from_name("azure-connect-str")])
def distribute_tasks():
    import os
    from azure.storage.blob import BlobServiceClient

    connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    # Get the client for the container
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    # Name of the container
    container_name = "rna-seq-reads"

    # Get the client for the container
    container_client = blob_service_client.get_container_client(container_name)

    # List all blobs in the container and print their names
    blob_list = container_client.list_blobs()
    blob_names = []
    for blob in blob_list:
        if blob.name.endswith(".fastq.gz"):
            blob_names.append(blob.name)

    # Group files by prefix
    task_groups = {}
    for file in blob_names:
        split = file.split("_")

        if len(split) == 1:
            task_groups[file.split(".")[0]] = [file]
            continue

        prefix = split[0]
        if prefix not in task_groups:
            task_groups[prefix] = []
        task_groups[prefix].append(file)

    # Distribute tasks
    tasks = list(task_groups.items())[:3]

    print(tasks)

    result = list(run_pipeline.map(tasks, return_exceptions=True))

    pass


@app.local_entrypoint()
def main():
    distribute_tasks.remote()
    pass
