# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'

import re
import os
import sys
import math
import collections
from Bio import SeqIO

def get_fa(seq):
    seq_dict = dict()
    for seq in SeqIO.parse(seq, "fasta"):
        seq_id = seq.id
        seqs = seq.seq
        seq_dict[seq_id] = str(seqs).replace("U", "T")
        return seq_dict




if __name__ == "__main__":
    known_seq = sys.argv[1]
    novel_seq = sys.argv[2]
    all_seq = sys.argv[3]
    sample_f = sys.argv[4]
    sample_f_dict = dict()
    with open(sample_f) as f:
        for line in f:
            s_id,s_name = line.strip().split("=")
            sample_f_dict[s_id] = open(s_name + "_non_mirna.txt", 'w')

    known_seq_dict = get_fa(known_seq)
    novel_seq_dict = get_fa(novel_seq)
    known_seq_values = known_seq_dict.values()
    novel_seq_values = novel_seq_dict.values()
    mirna_set = set(known_seq_values + novel_seq_values)



    for seq in SeqIO.parse(all_seq, 'fasta'):
        seq_id = seq.id
        seqs = str(seq.seq)
        sample = seq_id.split('_')[0]
        if seqs in mirna_set:
            pass
        else:
            if sample in sample_f_dict:
                sample_f_dict[sample].write("\t".join([seq_id, str(len(seqs)), seqs]) + "\n")

    for f in sample_f_dict.values():
        f.close()