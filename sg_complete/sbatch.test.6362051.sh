#!/bin/bash
#SBATCH -c 1
#SBATCH -D /mnt/ilustre/users/sanger-dev/sg-users/liubinxu
#SBATCH -n 1
#SBATCH -w compute-2-1
#SBATCH -N 1
#SBATCH -J test
#SBATCH -p SANGERDEV
#SBATCH --mem=2G
#SBATCH -o /mnt/ilustre/users/sanger-dev/sg-users/liubinxu/sbatch.test.6362051.out
#SBATCH -e /mnt/ilustre/users/sanger-dev/sg-users/liubinxu/sbatch.test.6362051.err
cd /mnt/ilustre/users/sanger-dev/sg-users/liubinxu
sleep 30

