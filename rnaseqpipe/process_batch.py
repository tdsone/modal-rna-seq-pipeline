from modal import App, Image, Function


app = App("rnaseq-process_batch")


@app.local_entrypoint()
def main():

    # def run_pipeline(sample_id: Tuple[str, List[str]], no_cache: bool = False):

    sample_ids = [
        (("SRR11808917", ["SRR11808917_1.fastq.gz", "SRR11808917_2.fastq.gz"]), False),
        # (("SRR13120263", ["SRR13120263_1.fastq.gz", "SRR13120263_2.fastq.gz"]), False),
        (("SRR14480065", ["SRR14480065_1.fastq.gz", "SRR14480065_2.fastq.gz"]), False),
        (("SRR20666409", ["SRR20666409_1.fastq.gz", "SRR20666409_2.fastq.gz"]), False),
        (("SRR11808918", ["SRR11808918_1.fastq.gz", "SRR11808918_2.fastq.gz"]), False),
        (("SRR14480064", ["SRR14480064_1.fastq.gz", "SRR14480064_2.fastq.gz"]), False),
        (("SRR22383428", ["SRR22383428_1.fastq.gz", "SRR22383428_2.fastq.gz"]), False),
    ]

    run_pipeline = Function.lookup("rna-seq", "run_pipeline")

    for sample_id, no_cache in sample_ids:
        run_pipeline.spawn(sample_id)
