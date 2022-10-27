#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/9/22 9:24
# @Author  : U make me wanna surrender my soul
from kegg_parse import parse, parse_ko
import re
import pandas as pd
import sys
import time
import json
import os

sys.path.append('./')

def get_kopath2ko(ko_path):
    kopath2ko = dict()
    files = os.listdir(ko_path)
    for file in files:
        if file.split(".")[-1] in ['png', 'kgml']:
            continue
        # print(file)
        with open(os.path.join(ko_path, file), 'r') as k_f:
            # print(ko_path)
            for ko_rec in parse_ko(k_f):
                 kopath2ko[ko_rec.entry] = ko_rec.orthology
    return kopath2ko

if __name__ == '__main__':
    ko_path = '/mnt/ilustre/users/ruiyang.gao/Database/KEGG/kopathway'
    spe_path = "/mnt/ilustre/users/ruiyang.gao/Database/KEGG/OrgPathway/Prokaryotes/"
    spe_file = "/mnt/ilustre/users/ruiyang.gao/Database/KEGG/Prokaryotes/all.txt"

    kopath2ko_dict = get_kopath2ko(ko_path)
    with open("ko2path.json", "w") as f:
        f.write(json.dumps(kopath2ko_dict, indent=4))

    df = pd.read_csv(
        spe_file, sep='\t', header=None,
    )
    df = df.fillna('nan')
    org_list = df[1].tolist()

    for org in org_list:
        spe_path_list = spe_path + org + '/pathway_' + org + '.txt'
        if os.path.exists(spe_path_list):
            pass
        else:
            print("no exists path %s" % spe_path_list)
            continue
        path_df = pd.read_csv(spe_path_list, sep='\t', header=None)
        path_list = path_df[0].tolist()
        # print(path_list)
        # path_clean = [l.split(":")[1] for l in path_list]
        header = "ko_id\tKO_list\tclass\tko_name\tdb_link\torganism\tDescription\n"
        fo = open(spe_path + org+ "/{}_info.xls".format(org), "w")
        fo.write(header)
        for path in path_list:
            path = path.split(':')[-1]
            path_path = spe_path + org + '/' + path
            if os.path.exists(path_path):
                pass
            else:
                print("error {} not find".format(path_path))
                continue
            with open(path_path, 'r') as f:
                # print(path_path)
                for spe_path_rec in parse(f):
                    # print(spe_path_rec.entry)
                    kopath = "ko" + spe_path_rec.entry[-5:]
                    if kopath in kopath2ko_dict:
                        kostr = ";".join(kopath2ko_dict[kopath])
                    else:
                        print("error for {}".format(kopath))

                    fo.write("\t".join([
                        kopath,
                        kostr,
                        spe_path_rec._class, 
                        spe_path_rec.name,
                        spe_path_rec.dblinks, 
                        spe_path_rec.organism,
                        spe_path_rec.description
                        
                    ]) + "\n")

        fo.close()


