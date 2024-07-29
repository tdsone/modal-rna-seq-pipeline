"""
Stops all modal apps and redeploys them

1. Get all apps: modal app list. Returns: 

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ App ID                    ┃ Description          ┃ State    ┃ Tasks ┃ Created at            ┃ Stopped at            ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ ap-bp9s5LR6PfugG75OMPQY9Z │ rnaseq-staralign     │ deployed │ 0     │ 2024-06-20 13:08 CEST │                       │
│ ap-tBu8uY9X2MAAfNqLqtD2P7 │ rnaseq-trim-galore   │ deployed │ 0     │ 2024-06-20 13:08 CEST │                       │
│ ap-EaNoaRBWBm6H3M6iokQZdR │ plextract-ocr        │ deployed │ 0     │ 2024-06-20 08:12 CEST │                       │
│ ap-lFM0b3xdud8L9M6X9zVV71 │ plextract-lineformer │ deployed │ 0     │ 2024-06-20 08:12 CEST │                       │
│ ap-n4xJ034z6GcsHdgU96oMub │ plextract-chartdete  │ deployed │ 0     │ 2024-06-20 08:08 CEST │                       │
│ ap-LPanQRUIvpBMEr9Evl1eQu │ rnaseq-fastqc        │ deployed │ 0     │ 2024-06-19 17:33 CEST │                       │
│ ap-VxsOwZbdFn7xzp8vK1vrlj │ rnaseq-strandedness  │ deployed │ 0     │ 2024-06-13 15:31 CEST │                       │
│ ap-Ao7WRMzR1gCVYuUHNnWHcd │ rna-seq              │ deployed │ 0     │ 2024-06-13 14:58 CEST │                       │
│ ap-HufVskbCIBDYAuFqsHGdl5 │ modal shell          │ unknown  │ 0     │ 2024-06-08 20:10 CEST │                       │
│ ap-S5SblLj7V3P91XHBDbvX6p │ rnaseq-downloader    │ deployed │ 0     │ 2024-06-07 17:53 CEST │                       │
│ ap-FP4dlFNScEMe3po463EAUF │ rnaseq-trim-galore   │ stopped  │ 0     │ 2024-06-18 16:58 CEST │ 2024-06-20 13:06 CEST │
│ ap-ytkIcdcRCHcVCr6ZPIVzdj │ rnaseq-staralign     │ stopped  │ 0     │ 2024-06-19 17:33 CEST │ 2024-06-20 13:06 CEST │
│ ap-qNglh6rjfJ1129FBAA4CYe │ rna-seq              │ stopped  │ 0     │ 2024-06-20 13:05 CEST │ 2024-06-20 13:05 CEST │
│ ap-MBV2imoe0FcZFPfV5DkoLf │ rnaseq-fastqc        │ stopped  │ 0     │ 2024-06-20 13:03 CEST │ 2024-06-20 13:04 CEST │
│ ap-iqFKDotNrfuHWt8hSfG9mc │ rnaseq-fastqc        │ stopped  │ 0     │ 2024-06-20 13:02 CEST │ 2024-06-20 13:03 CEST │
│ ap-15nGN9RL0jh4kAPYcIIsoF │ rnaseq-fastqc        │ stopped  │ 0     │ 2024-06-20 13:00 CEST │ 2024-06-20 13:00 CEST │
    1.1 Get this output
    1.2 Get all app ids via regex

2. Stop all apps: modal app stop <app id>
3. Redeploy all apps: ./scripts/deploy.sh all
"""

import os
import subprocess
import re


# Step 1: Get all apps
def get_all_apps():
    result = subprocess.run(["modal", "app", "list"], capture_output=True, text=True)
    return result.stdout


# Step 1.2: Extract app IDs via regex
def extract_app_ids(app_list_output):
    app_ids = re.findall(r"ap-[a-zA-Z0-9]+", app_list_output)
    return app_ids


# Step 2: Stop all apps
def stop_all_apps(app_ids):
    for app_id in app_ids:
        print(f"Stopping app {app_id}")
        subprocess.run(["modal", "app", "stop", app_id])


# Step 3: Redeploy all apps
def redeploy_all_apps():
    subprocess.run(["./scripts/deploy.sh", "all"])


# Main function to execute the steps
def main():
    app_list_output = get_all_apps()
    app_ids = extract_app_ids(app_list_output)
    stop_all_apps(app_ids)
    redeploy_all_apps()


if __name__ == "__main__":
    main()
