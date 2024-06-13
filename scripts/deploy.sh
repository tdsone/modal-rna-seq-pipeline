#!/bin/bash

# Function to deploy modules based on abbreviation
deploy_module() {
    case $1 in
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
        *)
            echo "Unknown module: $1"
            ;;
    esac
}

deploy_module $1