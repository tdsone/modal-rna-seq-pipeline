from modal import Volume, Image

vol = Volume.from_name("rnaseq-vol", create_if_missing=True)
salmon_image = (
    Image.debian_slim()
    .apt_install("wget")
    .run_commands(
        "wget https://github.com/COMBINE-lab/salmon/releases/download/v1.10.0/salmon-1.10.0_linux_x86_64.tar.gz"
    )
    .run_commands("tar -xzf salmon-1.10.0_linux_x86_64.tar.gz")
)


def fastqc_img(img: Image) -> Image:
    return (
        img.apt_install("default-jre")
        .run_commands("java -version")
        .apt_install("wget", "unzip")
        .run_commands(
            "wget https://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v0.12.1.zip",
            "unzip fastqc_v0.12.1.zip",
        )
    )

def cita
