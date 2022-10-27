#! /bin/bash
#SBATCH -J Extraciton_Euk_Seq
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 4  
#SBATCH -p DNA
#SBATCH -o Euk.stdout
#SBATCH --mem=40gb



python3 Extraction_Euk_Sequence.py
