# """
# This script is used to generate a decoy transcriptome for use in the Salmon quantification step.
# """

# from modal import App, Image
# from rnaseqpipe.config import vol

# app = App("generate-decoy-transcriptome")

# image = (
#     Image.debian_slim()
#     .apt_install("git", "wget")
#     .run_commands("git clone https://github.com/tdsone/SalmonTools")
#     .run_commands("chmod +x SalmonTools/scripts/generateDecoyTranscriptome.sh")
#     .run_commands("wget https://zenodo.org/api/records/11527624/files-archive")
#     .run_commands("mv files-archive files-archive.zip")
#     .apt_install("unzip")
#     .run_commands("unzip files-archive.zip")
#     .apt_install("bedtools")
#     .run_commands(
#         "wget https://github.com/marbl/MashMap/releases/download/v2.0/mashmap-Linux64-v2.0.tar.gz",
#         "tar -xzf mashmap-Linux64-v2.0.tar.gz",
#         "cp mashmap-Linux64-v2.0/mashmap /usr/local/bin/",
#     )
# )


# @app.function(image=image, volumes={"/data": vol})
# def generate_decoy_transcriptome(assembly_name: str = "R64-1-1"):
#     import os
#     import subprocess

#     salmon_index_dir = f"/data/salmon_index/{assembly_name}"
#     os.makedirs(salmon_index_dir, exist_ok=True)

#     # Run the script to generate the decoy transcriptome
#     subprocess.run(
#         [
#             "/SalmonTools/scripts/generateDecoyTranscriptome.sh",
#             "-a",
#             "/Saccharomyces_cerevisiae.R64-1-1.111.gtf",
#             "-g",
#             "/R64-1-1.fa",
#             "-t",
#             "/Saccharomyces_cerevisiae.R64-1-1.cdna.all.fa.gz",
#             "-o",
#             f"{salmon_index_dir}/decoy",
#         ],
#         check=True,
#     )

"""
This script is used to generate a decoy transcriptome for use in the Salmon quantification step.
"""

from modal import App, Image
from rnaseqpipe.config import vol

app = App("generate-decoy-transcriptome")

image = (
    Image.debian_slim()
    .apt_install("git", "wget", "grep")
    .run_commands("wget https://zenodo.org/api/records/11550687/files-archive")
    .run_commands("mv files-archive files-archive.zip")
    .apt_install("unzip")
    .run_commands("unzip files-archive.zip")
)


@app.function(image=image, volumes={"/data": vol})
def generate_decoy_transcriptome(assembly_name: str = "R64-1-1"):
    import os
    import subprocess

    salmon_index_dir = f"/data/salmon_index/{assembly_name}/decoy"
    os.makedirs(salmon_index_dir, exist_ok=True)

    # Delete all files in salmon_index_dir
    for file in os.listdir(salmon_index_dir):
        os.remove(f"{salmon_index_dir}/{file}")

    print(os.listdir("/"))

    # Run the script to generate the decoy transcriptome

    subprocess.run(
        f'grep "^>" <(gunzip -c /R64-1-1.fa.gz) | cut -d " " -f 1 > {salmon_index_dir}/decoys.txt',
        shell=True,
        executable="/bin/bash",
    )

    subprocess.run(
        f"sed -i.bak -e 's/>//g' /data/salmon_index/R64-1-1/decoy/decoys.txt",
        shell=True,
    )
    subprocess.run(
        f"cat /Saccharomyces_cerevisiae.R64-1-1.cdna.all.fa.gz /R64-1-1.fa.gz > {salmon_index_dir}/gentrome.fa.gz",
        shell=True,
    )

    vol.commit()
