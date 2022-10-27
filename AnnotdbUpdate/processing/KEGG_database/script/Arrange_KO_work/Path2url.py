#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/9/23 9:50
# @Author  : U make me wanna surrender my soul
import pandas as pd

with open('Error1.log', 'r') as f:
    list_pro = []
    list_euk = []
    for line in f:
        if 'Prokaryotes' in line:
            org_id = line.strip('\n').split('/')[-2]
            gene_id = line.strip('\n').split('/')[-1]
            download = org_id + ':' + gene_id
            download = 'http://rest.kegg.jp/get/' + download
            # print(download)
            list_pro.append(download)
        elif 'Eukaryotes' in line:
            org_id = line.strip('\n').split('/')[-2]
            gene_id = line.strip('\n').split('/')[-1]
            download = org_id + ':' + gene_id
            download = 'http://rest.kegg.jp/get/' + download
            # print(download)
            list_euk.append(download)

dict1 = {'ID': list_pro}
df1 = pd.DataFrame(dict1)
df1.to_csv('Pro_Deal_Error.txt', sep='\t', index=None)
dict2 = {'ID': list_euk}
df2 = pd.DataFrame(dict2)
df2.to_csv('Euk_Deal_Error.txt', sep='\t', index=None)