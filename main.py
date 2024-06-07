from modal import App, Mount

app = App("rna-seq")


@app.function()
def run_pipeline():

    pass


@app.function(mounts=[Mount.from_local_dir("tasks", remote_path="/tasks")])
def distribute_tasks():
    import os

    files = os.listdir("/tasks")

    # Group files by prefix
    task_groups = {}
    for file in files:
        split = file.split("_")

        if len(split) == 1:
            task_groups[file.split(".")[0]] = [file]
            continue

        prefix = split[0]
        if prefix not in task_groups:
            task_groups[prefix] = []
        task_groups[prefix].append(file)

    print(task_groups)

    pass


@app.local_entrypoint()
def main():
    distribute_tasks.remote()
    pass
