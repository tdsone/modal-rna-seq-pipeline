from modal import App, Image, Secret, method, build, enter, Cls, Volume
from typing import Tuple, List

app = App("rna-seq")
vol = Volume.from_name("rna-seq-data", create_if_missing=True)

pipeline_img = Image.debian_slim().pip_install("azure-storage-blob", "tqdm")


@app.function(
    image=pipeline_img,
    volumes={"/data": vol},
    secrets=[Secret.from_name("azure-connect-str")],
)
def run_pipeline(sample_id: Tuple[str, List[str]]):
    """
    sample_id example paired: ("DRR023784", ["DRR023784_1.fastq", "DRR023784_2.fastq"])
    sample_id example unpaired: ("DRR023784", ["DRR023784.fastq"])
    """

    # Create a pipeline ID
    pipeline_id = f"pl-{sample_id[0]}"

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
    for file in sample_id[1]:
        blob_client = container_client.get_blob_client(file)
        with open(f"data/{pipeline_id}/{file}", "wb") as f:
            f.write(blob_client.download_blob().readall())

    # Run FastQC


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
    tasks = list(task_groups.items())[:2]

    print(tasks)

    result = list(run_pipeline.map(tasks, return_exceptions=True))

    pass


@app.local_entrypoint()
def main():
    distribute_tasks.remote()
    pass
