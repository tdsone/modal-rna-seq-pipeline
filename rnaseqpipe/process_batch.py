from modal import App, Image, Function


app = App("rnaseq-process_batch")


@app.local_entrypoint()
def main():

    # def run_pipeline(sample_id: Tuple[str, List[str]], no_cache: bool = False):
    sample_ids = [
        (("ERR11502248", ["ERR11502248_1.fastq.gz", "ERR11502248_2.fastq.gz"]), False)
    ]

    run_pipeline = Function.lookup("rna-seq", "run_pipeline")

    result = list(run_pipeline.starmap(sample_ids))

    print(result)
