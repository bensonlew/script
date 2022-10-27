#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/7/31 13:36
# @Author  : U make me wanna surrender my soul
import pandas as pd
import requests
import re
import os

# org = pd.read_csv('organism.txt', sep='\t', header=None)
# # print(org.head())
# Euk = org.loc[org[3].str.contains('Eukaryotes')]
# Pro = org.loc[org[3].str.contains('Prokaryotes')]
# Euk.to_csv('Eukaryotes.txt', header=None, index=None, sep='\t')
# Pro.to_csv('Prokaryotes.txt',header=None, index=None, sep='\t')

# image = requests.get(url='http://rest.kegg.jp/get/path:ko00010/image')
# with open('image.png', 'wb') as f:
#     f.write(image.content)
df = pd.read_csv(r'E:\KEGG_Database\compound\compound.txt', sep='\t', header=None)
list1 = df[0].tolist()
list3 = []
for i in list1:
    try:
        list3.append(i.strip('cpd:'))
    except:
        pass
print(len(list3), '***')
list_file = os.listdir(r'E:\KEGG_Database\compound')
list_file.remove('compound.txt')
img_list = []
ann_list = []
for j in list_file:
    if j.endswith('.png'):
        img_list.append(j.strip('.png'))
    else:
        ann_list.append(j)
# 去重
list_ann = list(set(ann_list))
list_img = list(set(img_list))
print(len(list_ann), '***')

list2 = list((set(list3) ^ set(list_ann)))
list4 = list((set(list3) ^ set(list_img)))
print(list2)
print(len(list2))

print('____')
print(list4)
print(len(list4))