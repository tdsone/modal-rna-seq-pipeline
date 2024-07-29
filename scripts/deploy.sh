#!/bin/bash

# Function to deploy modules based on abbreviation
deploy_module() {
    IFS=',' read -ra MODULES <<< "$1"
    for module in "${MODULES[@]}"; do
        case $module in
            is)
                echo "Deploying infer_strandedness..."
                modal deploy rnaseqpipe/modules/infer_strandedness/main.py
                ;;
            tg)
                echo "Deploying trim-galore..."
                modal deploy rnaseqpipe/modules/trim-galore.py
                ;;
            qc)
                echo "Deploying fastqc..."
                modal deploy rnaseqpipe/modules/fastqc.py
                ;;
            sa)
                echo "Deploying staralign..."
                modal deploy rnaseqpipe/modules/staralign.py
                ;;
            bw)
                echo "Deploying wigToBigWig..."
                modal deploy rnaseqpipe/modules/wigToBigWig.py
                ;;
            up)
                echo "Deploying uploader..."
                modal deploy rnaseqpipe/modules/uploader.py
                ;;
            main)
                echo "Deploying main..."
                modal deploy rnaseqpipe/main.py
                ;;
            all)
                echo "Deploying all modules..."
                modal deploy rnaseqpipe/modules/infer_strandedness/main.py
                modal deploy rnaseqpipe/modules/trim-galore.py
                modal deploy rnaseqpipe/modules/fastqc.py
                modal deploy rnaseqpipe/modules/staralign.py
                modal deploy rnaseqpipe/modules/wigToBigWig.py
                modal deploy rnaseqpipe/modules/uploader.py
                modal deploy rnaseqpipe/main.py
                ;;
            *)
                echo "Unknown module: $module"
                ;;
        esac
    done
}

deploy_module "$1"
