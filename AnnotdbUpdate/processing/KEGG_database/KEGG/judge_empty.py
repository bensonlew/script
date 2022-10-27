#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/8/10 9:43
# @Author  : U make me wanna surrender my soul
import os


def search(path):
    if len(os.listdir(path)) <= 5:  # 判断文件夹内数量是否达标
        with open('ERROR_ORG.file', 'a+') as f:
            print(path, file=f)
    else:
        pass


org_list = os.listdir('/mnt/ilustre/users/ruiyang.gao/Database/KEGG/OrgPathway/Eukaryotes')
for org in org_list:
    search(org)
