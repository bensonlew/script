#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/9/9 13:51
# @Author  : U make me wanna surrender my soul
import os
import pandas as pd

org = pd.read_csv('/mnt/ilustre/users/ruiyang.gao/Database/KEGG/OrgPathway/Prokaryotes/Debug_Prokaryotes.txt', sep='\t',
                  header=None)
org = org.fillna('nan')
org_list = org[1].tolist()
list1 = os.listdir('/mnt/ilustre/users/ruiyang.gao/Database/KEGG/OrgPathway/Prokaryotes/')
list2 = []
for i in list1:
    if i.endswith('.txt'):
        pass
    else:
        list2.append(i)

result4 = list(set(org_list).difference(set(list2)))
print(len(result4))
print(result4)
