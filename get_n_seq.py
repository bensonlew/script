import sys
from Bio import SeqIO
seq = sys.argv[1]
for seq in SeqIO.parse(seq, "fasta"):
    seq_seq = str(seq.seq)
    if len(seq_seq.replace("N","")) == 0:
        print seq.name

