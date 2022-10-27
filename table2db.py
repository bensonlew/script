#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@time    : 2019/5/21 16:27
@file    : gsea.py
"""


from biocluster.config import Config
import re
import collections
import json
from itertools import islice
import subprocess
import gridfs
import os
import sys


def db2table(project, collection, fields, tab=None, ref=False):
    '''
    修改图片转换为并行
    '''
    client = Config().get_mongo_client(mtype="prok_rna", ref=ref)
    mongodb = client[Config().get_mongo_dbname("prok_rna", ref=ref)]

    fields_list = fields.split(",")
    print "\t".join(fields_list)

    col = mongodb[collection]

    rec_list = list()
    with open(tab, 'r') as f:
        for line in f:
            cols = line.strip().split("\t")
            
            rec_list.append(dict(zip(fields_list, cols)))

    col.insert_many(rec_list)


if __name__ == '__main__':
    p = sys.argv[1]
    c = sys.argv[2]
    f = sys.argv[3]
    t = sys.argv[4]
    db2table(p, c, f, t)
