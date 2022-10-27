#!/usr/bin/env python
""" Inject command to own command line """

import sys, fcntl, termios
import pandas as pd
import numpy as np
import sys
enrich_file = sys.argv[1]
node_file = sys.argv[2]
node_out_file = sys.argv[3]
edge_file = sys.argv[4]
edge_out_file = sys.argv[5]

enrich_table = pd.read_table(enrich_file, header=0)
enrich_table = enrich_table[enrich_table["Corrected P-Value"] < 0.05]
enrich_table = enrich_table[enrich_table["typeI"] != "Human Diseases"]
enrich_table = enrich_table[:5]

gene2path = dict()
gene_path_df = enrich_table[["Genes", "Term"]]
for d in gene_path_df.iterrows():
    path = d[1]["Term"]
    for gene in d[1]["Genes"].split("|"):
        if gene in gene2path:
            gene2path[gene].add(path)
        else:
            gene2path[gene] = set([path])


gene_set = set(gene2path.keys())
node_table = pd.read_table(node_file, header=0)
node_table_choose = node_table[node_table["nodeName"].isin(gene_set)]
# node_table_choose["paths"] = node_table_choose["nodeName"].map(lambda x:";".join(list(gene2path[x])))
node_table_choose["paths"] = node_table_choose["nodeName"].map(lambda x:list(gene2path[x])[0])
node_table_choose.to_csv(node_out_file, sep="\t", index=False)

edge_table = pd.read_table(edge_file, sep="\t")
edge_table_choose = edge_table[edge_table["fromNode"].isin(gene_set) & edge_table["toNode"].isin(gene_set)]
edge_table_choose = edge_table_choose[edge_table_choose["weight"]> 0.25]
edge_table_choose.to_csv(edge_out_file, sep="\t", index=False)
