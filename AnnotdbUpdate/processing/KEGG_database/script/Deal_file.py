#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/8/6 13:33
# @Author  : U make me wanna surrender my soul
import pandas as pd
import re
import os


# 处理错误代码
def error_deal(file):
    rule = r'[a-zA-z]+://[^\s]*'
    pathway_list = []
    with open(file, 'r', encoding='UTF-8') as f:
        data = f.readlines()
        for i in data:
            try:
                pathway_list.append(re.findall(rule, i)[0].strip('>'))
            except IndexError:
                pass
    pathway_list = list(set(pathway_list))
    return pathway_list


# 检查物种内缺失文件
def check_file(file):
    with open('less_file.txt', 'a+') as f:
        file_list = os.listdir(file)
        if len(file_list) <= 5:
            print(file, file=f)


# df = pd.read_csv('trt.txt', sep='\t', header=None)
# one = df.loc[0].tolist()
#
# two = df.loc[1].tolist()
#
# fin = []
# for i, j in zip(one, two):
#     fin.append(i + '-' + j)
# df.columns = fin
# print(df.head())
# df.to_csv('other.txt', sep='\t', index=False)
# org_list = os.listdir('/mnt/ilustre/users/ruiyang.gao/Database/KEGG/OrgPathway/Eukaryotes')
#
# try:
#     for i in org_list:
#         print(i)
#         check_file('/mnt/ilustre/users/ruiyang.gao/Database/KEGG/OrgPathway/Eukaryotes/' + i)
# except NotADirectoryError:
#     pass

a = error_deal('Prokaryotes_gene3.log')
print(len(a))
print(a)
df = pd.DataFrame()
df['ID'] = a
df.to_csv('Deal_Error.txt', sep='\t', index=None)
