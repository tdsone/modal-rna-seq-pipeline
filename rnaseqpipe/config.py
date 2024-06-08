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
