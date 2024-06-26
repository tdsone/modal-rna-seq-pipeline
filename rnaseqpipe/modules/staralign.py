from modal import App, Secret, Image, build, enter, method
from typing import List

from rnaseqpipe.modules.utils import PLID
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
    timeout=60 * 10,
    cpu=8.0,
    container_idle_timeout=5,
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
            zip_ref.extractall("/data/genome-index")

        vol.commit()

        pass

    @enter()
    def enter(self):
        pass

    @method()
    def align(
        self,
        plid: PLID,
        read_files: List[str],
        force_recompute: bool = False,
    ):
        import subprocess  # Ensure this import is added to the module where this class and method are defined.
        import os

        assert len(read_files) in (1, 2), "Only 1 or 2 read files supported."

        print("Aligning reads...")
        threads = 8
        genome_idx_dir = "/data/genome-index/genome-index"
        result_path = f"/data/{plid}/staralign/"

        os.makedirs(result_path, exist_ok=True)

        if (
            os.path.exists(f"{result_path}/Signal.Unique.str1.out.wig")
            and os.path.exists(f"{result_path}/Signal.Unique.str2.out.wig")
            and not force_recompute
        ):
            print(f"Alignment result already exists for {plid}. Skipping alignment.")
            return True

        # Construct the basic command for STAR alignment
        if len(read_files) == 2:  # Paired-end reads
            read_files_cmd = f"{read_files[0]} {read_files[1]}"
        else:  # Single-end reads
            read_files_cmd = f"{read_files[0]}"

        cmd = f"""/STAR-2.7.11b/bin/Linux_x86_64_static/STAR --runThreadN {str(threads)} \
            --genomeDir {genome_idx_dir} \
            --readFilesIn {read_files_cmd} \
            --outWigType wiggle \
            --outSAMtype BAM SortedByCoordinate \
            --limitBAMsortRAM 1174874044 \
            --outFileNamePrefix {result_path}
            """

        print(cmd)

        try:
            # Execute the command using subprocess
            result = subprocess.run(cmd, check=True, capture_output=True, shell=True)

            vol.commit()

            print(f"Succeeded: {result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to align reads: {e.stderr}")
            raise

        return True


@app.local_entrypoint()
def run():
    from pathlib import Path
    from modal import Cls

    plid = PLID("pl-ERR11502246")

    AlingerRef = Cls.lookup("rnaseq-staralign", "STARAlign")

    Aligner = AlingerRef()

    Aligner.align.remote(
        plid,
        [
            f"/data/{plid}/trimgalore/ERR11502246_1_val_1.fq",
            f"/data/{plid}/trimgalore/ERR11502246_2_val_2.fq",
        ],
        False,
    )

    pass
