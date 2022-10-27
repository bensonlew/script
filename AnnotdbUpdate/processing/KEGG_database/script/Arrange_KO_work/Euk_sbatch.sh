#! /bin/bash
#SBATCH -J Arrange_Euk
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 2  
#SBATCH -p DNA
#SBATCH -o Euk.stdout
#SBATCH --mem=20gb


python3 Arrange_Euk.py