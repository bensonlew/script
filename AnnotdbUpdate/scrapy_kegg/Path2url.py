#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/9/23 9:50
# @Author  : U make me wanna surrender my soul
import pandas as pd

with open('Error1.log', 'r') as f:
    list1 = []
    for line in f:
        org_id = line.strip('\n').split('/')[-2]
        gene_id = line.strip('\n').split('/')[-1]
        download = org_id + ':' + gene_id
        download = 'http://rest.kegg.jp/get/' + download
        # print(download)
        list1.append(download)

dict1 = {'ID': list1}
df = pd.DataFrame(dict1)
df.to_csv('No_down.txt', sep='\t', index=None)
