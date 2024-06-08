from modal import App, Image, Secret
from rnaseqpipe.config import vol
from rnaseqpipe.modules.utils import PLID
from pathlib import Path

app = App("rnaseq-downloader")

downloader_img = Image.debian_slim().pip_install("azure-storage-blob")


@app.function(
    image=downloader_img,
    volumes={"/data": vol},
    secrets=[Secret.from_name("azure-connect-str")],
)
def download_from_azure(
    plid: PLID, container_name: str, blob_name: str, dest_dir: Path
):
    # Check if the blob was already downloaded
    if Path(f"/data/{plid}/{dest_dir}") / Path(blob_name):
        print(f"{blob_name} already exists in {dest_dir}")
        return dest_dir

    import os
    from azure.storage.blob import BlobServiceClient

    connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    # Get the client for the container
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    # Get the client for the container
    container_client = blob_service_client.get_container_client(container_name)

    blob_client = container_client.get_blob_client(blob_name)

    os.makedirs(f"/data/{plid}/{dest_dir}", exist_ok=True)

    dest_path = Path(f"/data/{plid}") / Path(dest_dir) / Path(blob_name)

    with open(dest_path, "wb") as f:
        f.write(blob_client.download_blob().readall())

    vol.commit()

    print(f"Downloaded {blob_name} to {dest_dir}")

    return dest_dir


@app.local_entrypoint()
def download():
    download_from_azure.remote(PLID(), "rna-seq-reads", "DRR023796.fastq", "reads")
