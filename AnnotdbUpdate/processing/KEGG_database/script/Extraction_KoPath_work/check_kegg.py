#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/10/08 13:20
# @Author  : 
import sys
import os

db_path= "/mnt/ilustre/users/ruiyang.gao/Database/KEGG/"
pathway_dir = "/mnt/ilustre/users/ruiyang.gao/Database/KEGG/OrgPathway"
class_ = "Prokaryotes"


def get_gene_path(spe, gene):
    return os.path.join(db_path, class_, spe, gene)

def get_pathway_path(spe, pathway):
    return os.path.join(pathway_dir, class_, spe, pathway + ".html")


def check_path():
    

# Set up line wrapping rules (see Bio.KEGG._wrap_kegg)

if __name__ == "__main__":
    file_type = sys.argv[1]
    unload_file = sys.argv[2]
    with open(unload_file, "r") as f:
        f.readline()
        for line in f:
            #print(line)
            name = line.strip().split("/")[-1]
            
            if file_type == "gene":
                spe, gene = name.split(":") 
                path = get_gene_path(spe, gene)
            elif file_type == "html":
                spe = name[13:-5]
                pathway = name[13:]
                # print(pathway)
                path = get_pathway_path(spe, pathway)
            # print(path)
            if os.path.exists(path):
                print("\t".join([line.strip(), "true"]))
            else:
                print("\t".join([line.strip(), "false"]))