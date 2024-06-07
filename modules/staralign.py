from modal import App, Secret, Image, build, enter, method
from typing import List

from config import vol

app = App("rnaseq-staraligner")
aligner_img = Image.debian_slim()


@app.cls(
    image=aligner_img,
    volumes={"/data": vol},
    secrets=[Secret.from_name("azure-connect-str")],
)
class STARAlign:

    @build()
    def build(self):
        # Download genome index from azure
        import os
        from azure.storage.blob import BlobServiceClient

        connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

        # Get the client for the container
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)

        # Download the genome index
        container_name = "pipeline"

        # Get the client for the container
        container_client = blob_service_client.get_container_client(container_name)

        blob_client = container_client.get_blob_client("genome-index.zip")

        with open("genome-index.zip", "wb") as f:
            f.write(blob_client.download_blob().readall())

        # Unzip the genome index
        import zipfile

        with zipfile.ZipFile("genome-index.zip", "r") as zip_ref:
            zip_ref.extractall("genome-index")

        pass

    @enter()
    def enter(self):
        pass

    def align(self, plid: str, read_files: List[str]):
        import subprocess  # Ensure this import is added to the module where this class and method are defined.

        assert len(read_files) in (1, 2), "Only 1 or 2 read files supported."

        print("Downloading files from Azure...")

        # Download the read files from Azure
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
        for file in read_files:
            blob_client = container_client.get_blob_client(file)
            with open(file, "wb") as f:
                f.write(blob_client.download_blob().readall())

        print("Aligning reads...")
        threads = 8
        genome_idx_dir = "genome-index"

        # Construct the basic command for STAR alignment
        if len(read_files) == 2:  # Paired-end reads
            read_files_cmd = f"{read_files[0]} {read_files[1]}"
        else:  # Single-end reads
            read_files_cmd = f"{read_files[0]}"

        cmd = [
            "STAR",
            "--runThreadN",
            str(threads),
            "--genomeDir",
            genome_idx_dir,
            "--readFilesIn",
            read_files_cmd,
            "--outFileNamePrefix",
            "output_prefix",
            "--outWigType",
            "wiggle",
            "--outSAMtype",
            "BAM SortedByCoordinate",
            "--limitBAMsortRAM",
            "1174874044",
        ]

        try:
            # Execute the command using subprocess
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"Succeeded: {result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to align reads: {e.stderr}")
            raise
