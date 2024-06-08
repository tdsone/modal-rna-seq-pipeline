# modal-rna-seq-pipeline
An RNA-seq pipeline build on top of modal.com

## Setup
1. Install the pipeline as an editable package: `pip install -e rnaseqpipe`

# Misc

## Generating the Salmon Decoy Transcriptome
https://github.com/COMBINE-lab/SalmonTools/tree/master: 
generateDecoyTranscriptome.sh — Located in the scripts/ directory, this is a preprocessing script for creating augmented hybrid fasta file for salmon index. It consumes genome fasta (one file given through -g), transcriptome fasta (-t) and the annotation (GTF file given through -a) to create a new hybrid fasta file which contains the decoy sequences from the genome, concatenated with the transcriptome (gentrome.fa). It runs mashmap (path to binary given through -m) to align transcriptome to an exon masked genome, with 80% homology and extracts the mapped genomic interval. It uses awk and bedtools (path to binary given through -b) to merge the contiguosly mapped interval and extracts decoy sequences from the genome. It also dumps decoys.txt file which contains the name/id of the decoy sequences. Both gentrome.fa and decoys.txt can be used with salmon index with salmon >=0.14.0.
NOTE: Salmon version v1.0 can directly index the genome and transcriptome and doesn't mandates to run the generateDecoyTranscriptome script, however it's still backward compatible. Please checkout this tutorial on how to run salmon with full genome + transcriptome without the annotation.