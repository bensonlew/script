#! /bin/bash
#SBATCH -J Arrange_Pro
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 2  
#SBATCH -p DNA
#SBATCH -o Pro.stdout
#SBATCH --mem=20gb


python3 Arrange_Pro.py