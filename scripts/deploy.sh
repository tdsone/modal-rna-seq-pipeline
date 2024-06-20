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
            all)
                echo "Deploying all modules..."
                modal deploy rnaseqpipe/modules/infer_strandedness/main.py
                modal deploy rnaseqpipe/modules/trim-galore.py
                modal deploy rnaseqpipe/modules/fastqc.py
                modal deploy rnaseqpipe/modules/staralign.py
                ;;
            *)
                echo "Unknown module: $module"
                ;;
        esac
    done
}

deploy_module "$1"
