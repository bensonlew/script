#! /bin/bash
#SBATCH -J Extraciton_Pro_Seq
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 4  
#SBATCH -p DNA
#SBATCH -o Pro.stdout
#SBATCH --mem=40gb


python3 Extraction_Pro_Sequence.py