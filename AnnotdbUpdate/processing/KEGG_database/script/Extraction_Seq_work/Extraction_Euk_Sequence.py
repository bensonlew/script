#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/9/27 16:43
# @Author  : U make me wanna surrender my soul
from kegg_parse import parse
from Arrange import get_seq
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq
from Bio import SeqIO
import pandas as pd
import time

# 此处修改原核和真核的物种列表
path = '/mnt/ilustre/users/ruiyang.gao/Database/KEGG/Eukaryotes/'
df = pd.read_csv(
    path + 'Eukaryotes.txt', sep='\t', header=None,
)


df = df.fillna('nan')
org_list = df[1].tolist()
# org_list = ['oct']

for org in org_list:
    gene_df = pd.read_csv(path + org + '/' + org + '.txt', sep='\t', header=None)
    gene_list = gene_df[0].tolist()
    fnn = []
    faa = []
    for gene in gene_list:
        gene = gene.split(':')[-1]
        gene_path = path + org + '/' + gene
        dict1 = dict(
            gene_entry='',
            KO_id='',
            gene_name='',
            org='',
        )
        try:
            with open(gene_path) as f:
                data = parse(f)
                a = list(data)[0]
                entry = a.entry
                orhtology = a.orthology
                if len(orhtology) != 0:
                    orhtology = orhtology[0][0]
                else:
                    orhtology = '-'
                if len(a.name) == 0:
                    name = '-'
                else:
                    name = a.name
                    name = ':'.join(name)
                dict1['gene_entry'] = entry
                dict1['KO_id'] = orhtology
                dict1['gene_name'] = name
                dict1['org'] = a.organism[0]
            # print(dict1)
            aaseq, ntseq = get_seq(open(gene_path))
            # print(aaseq)
            # print(ntseq)
            seq_id = dict1['gene_entry'] + ':' + dict1['KO_id'] + ':' + dict1['gene_name'] + ':' + dict1['org']
            if aaseq == '':
                pass
            else:
                aaseq = Seq(aaseq) # 使用Seq()构建seq对象
                aa = SeqRecord(aaseq, id=seq_id, description='') # 构建Seqrecord对象
                faa.append(aa)
            if ntseq == '':
                pass
            else:
                ntseq = Seq(ntseq)
                nn = SeqRecord(ntseq, id=seq_id, description='')
                fnn.append(nn)
        except Exception as e:
            with open('Seq_Error.log', 'a+') as f:
                a = str(gene_path)
                # 可以增加下载功能
                print(time.strftime("%Y:%m:%d:%H:%M:%S", time.localtime()), ':', e, ':', a, file=f)
    SeqIO.write(faa, path + org + '/' + org + '.faa', 'fasta') # 将包含Seqrecord对象的列表写入文件
    print(org + ':faa extra over')
    SeqIO.write(fnn, path + org + '/' + org + '.fnn', 'fasta')
    print(org + ':fnn extra over')
