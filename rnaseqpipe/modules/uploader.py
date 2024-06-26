"""
This module is used to upload the results of the pipeline to Azure Blob Storage.
"""

from modal import Image, App, Secret
from rnaseqpipe.config import vol

app = App("rnaseq-uploader")
uploader_img = Image.debian_slim().pip_install("azure-storage-blob", "tqdm")

with uploader_img.imports():
    import os
    from azure.storage.blob import BlobServiceClient
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from tqdm import tqdm


@app.function(
    image=uploader_img,
    volumes={"/data": vol},
    secrets=[Secret.from_name("azure-connect-str")],
    timeout=1200,
)
def upload_results(plid: str):
    """Function that uploads all results to Azure Blob Storage.
    Args:
        plid (str): pipeline id for which results are to be uploaded.
    """
    RES_CONTAINER = "rna-seq-pipeline-results"
    connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    # Get the client for the container
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    # Get the client for the container
    container_client = blob_service_client.get_container_client(RES_CONTAINER)
    base_path = f"/data/{plid}/"

    def should_upload(file_path, blob_name):
        blob_client = container_client.get_blob_client(blob_name)
        try:
            blob_properties = blob_client.get_blob_properties()
            azure_size = blob_properties.size
            local_size = os.path.getsize(file_path)
            return local_size != azure_size
        except ResourceNotFoundError:
            return True

    def upload_file(file_path, blob_name):
        if should_upload(file_path, blob_name):
            blob_client = container_client.get_blob_client(blob_name)
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            return blob_name
        return None

    files_to_upload = []
    for root, _, files in os.walk(base_path):
        for file in files:
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, base_path)
            blob_name = f"{plid}/{relative_path}"
            files_to_upload.append((full_path, blob_name))

    print(f"Found {len(files_to_upload)} files to check for upload.")

    # Use ThreadPoolExecutor for parallel uploads
    with ThreadPoolExecutor(max_workers=30) as executor:
        future_to_file = {
            executor.submit(upload_file, file_path, blob_name): (file_path, blob_name)
            for file_path, blob_name in files_to_upload
        }
        uploaded_count = 0
        for future in tqdm(
            as_completed(future_to_file),
            total=len(files_to_upload),
            desc="Processing files",
        ):
            file_path, blob_name = future_to_file[future]
            try:
                result = future.result()
                if result:
                    uploaded_count += 1
            except Exception as exc:
                print(f"{file_path} generated an exception: {exc}")

    print(f"Upload completed. {uploaded_count} files were uploaded or updated.")


@app.local_entrypoint()
def main():
    plid = (
        "pl-ERR11502248"  # Replace with actual PLID or add as a command-line argument
    )
    upload_results.remote(plid)
