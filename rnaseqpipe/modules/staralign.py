from modal import App, Secret, Image, build, enter, method
from typing import List

from rnaseqpipe.modules.utils import PLID
from rnaseqpipe.modules.downloader import download_from_azure
from rnaseqpipe.config import vol

app = App("rnaseq-staralign")
aligner_img = (
    Image.debian_slim()
    .pip_install("azure-storage-blob")
    .apt_install("wget")
    .run_commands(
        "wget https://github.com/alexdobin/STAR/archive/2.7.11b.tar.gz",
        "tar -xzf 2.7.11b.tar.gz",
        "cd STAR-2.7.11b",
    )
    .run_commands("ls STAR-2.7.11b/bin")
    .apt_install("tree")
)


@app.cls(
    image=aligner_img,
    volumes={"/data": vol},
    secrets=[Secret.from_name("azure-connect-str")],
    cpu=8.0,
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

    @method()
    def align(self, plid: PLID, read_files: List[str]):
        import subprocess  # Ensure this import is added to the module where this class and method are defined.

        assert len(read_files) in (1, 2), "Only 1 or 2 read files supported."

        print("Aligning reads...")
        threads = 8
        genome_idx_dir = "genome-index/genome-index"

        import os

        print(os.listdir("genome-index"))

        # Construct the basic command for STAR alignment
        if len(read_files) == 2:  # Paired-end reads
            read_files_cmd = f"{read_files[0]},{read_files[1]}"
        else:  # Single-end reads
            read_files_cmd = f"{read_files[0]}"

        cmd = [
            "/STAR-2.7.11b/bin/Linux_x86_64_static/STAR",
            "--runThreadN",
            str(threads),
            "--genomeDir",
            genome_idx_dir,
            "--readFilesIn",
            read_files_cmd,
            "--outWigType",
            "wiggle",
            "--outSAMtype",
            "BAM",
            "SortedByCoordinate",
            "--limitBAMsortRAM",
            "1174874044",
        ]

        try:
            # Execute the command using subprocess
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            vol.commit()

            print(f"Succeeded: {result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to align reads: {e.stderr}")
            raise

        return True


@app.local_entrypoint()
def run():
    from pathlib import Path
    import modal

    plid = PLID("pl-9e233179-57c0-43fb-b514-1f98745ceacb")
    read_dir = Path("reads")

    """
    plid: PLID, container_name: str, blob_name: str, dest: Path
    """

    print("read dir: ", read_dir)

    star = STARAlign()

    star.align.remote(plid, ["/data/pl-DRR023782/trimgalore/DRR023782_trimmed.fq.gz"])

    pass
