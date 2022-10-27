#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/9/22 9:24
# @Author  : U make me wanna surrender my soul
from kegg_parse import parse
import re
import pandas as pd
import sys
import time

sys.path.append('./')


def get_seq(handle):
    """
    :param handle: 基因文件
    :return: 返回核酸序列和蛋白序列
    """
    s = handle.read()
    AASEQ = re.findall("AASEQ\s+\d+\s(.*)NTSEQ", s, re.DOTALL)[0].replace('\n', '')  # 去换行符
    AASEQ = AASEQ.strip().replace(' ', '')  # 去首尾空格并去除中间空格
    NTSEQ = re.findall("NTSEQ\s+\d+\s(.*)///", s, re.DOTALL)[0].replace('\n', '')
    NTSEQ = NTSEQ.strip().replace(' ', '')
    return AASEQ, NTSEQ


def get_img(org, handle):
    """
    :param handle: 基因文件
    :return: 提取基因文件中的信息，返回一个字典
    """
    global ko_list
    dict1 = dict(
        gene_entry='',
        KO_id='',
        gene_name='',
        ko_list='',
    )

    f = parse(handle)
    l1 = list(f)[0]
    entry = l1.entry
    orhtology = l1.orthology
    if len(orhtology) != 0:
        orhtology = orhtology[0][0]
    else:
        orhtology = '-'
    if len(l1.name) == 0:
        name = '-'
    else:
        name = l1.name[0]
    if len(l1.pathway) != 0:
        ko_list = ['ko' + i[0][-5:] for i in l1.pathway]
        ko_list = ';'.join(ko_list)
    else:
        ko_list = '-'
    dict1['gene_entry'] = org + ':' + entry
    dict1['KO_id'] = orhtology
    dict1['gene_name'] = name
    dict1['ko_list'] = ko_list
    return dict1


if __name__ == '__main__':
    path = '/mnt/ilustre/users/ruiyang.gao/Database/KEGG/Prokaryotes/'
    df = pd.read_csv(
        path + 'Prokaryotes.txt', sep='\t', header=None,
    )
    df = df.fillna('nan')
    org_list = df[1].tolist()
    # org_list = ['brk']

    for org in org_list:
        gene_df = pd.read_csv(path + org + '/' + org + '.txt', sep='\t', header=None)
        gene_list = gene_df[0].tolist()
        img_df = pd.DataFrame(columns=['gene_entry', 'KO_id', 'gene_name', 'ko_list'])
        for gene in gene_list:
            gene = gene.split(':')[-1]
            gene_path = path + org + '/' + gene
            try:
                dict_img = get_img(org, open(gene_path))
                img_df = img_df.append(dict_img, ignore_index=True)
            except Exception as e:
                # print(gene_path)
                with open('Error1.log', 'a+') as f:
                    b = str(gene_path)
                    print(time.strftime("%Y:%m:%d:%H:%M:%S", time.localtime()), ':', e, ':', b, file=f)
        # print(img_df.head())
        img_df.to_csv(path + org + '/' + org + '_allGene_ko.xls', sep='\t', index=False)
        # print(img_df)
        with open('Pro_Process.log', 'a+') as p:
            print(time.strftime("%Y-%m-%d-%H_%M_%S", time.localtime()), ':', org + ':arrange over', file=p)
        # id = dict_img['gene_entry']
        # aaseq, ntseq = get_seq(gene_path)
