#!/usr/bin/python
# -*- coding: utf-8 -*-
# __author__: shicaiping

from bson.objectid import ObjectId
from pymongo import MongoClient
import argparse
import pandas as pd
import re
import os
from biocluster.config import Config

def insert_db(file, database):
    """
    将数据库中的转录因子信息导入参考库
    """
    db = Config().get_mongo_client(mtype="ref_rna", ref=True)[Config().get_mongo_dbname("ref_rna", ref=True)]
    collection = db['known_tf']
    with open(file, "r") as f:
	data_list = []
        head = f.readline()
        for line in f:
            items = line.strip().split("\t")
            data = {
                'gene_id' : items[0],
                'transcript_id' : items[1],
                'tf_id' : items[2],
                'family' : items[3],
                'specie' : items[4],
                'db' : database,
            }
	    data_list.append(data)
        collection.insert_many(data_list)

def _main():
    parser = argparse.ArgumentParser(description='insert')
    parser.add_argument('-i', '--file')
    parser.add_argument('-db', '--database')
    args = parser.parse_args()
    insert_db(args.file, args.database)

if __name__ == "__main__":
    _main()


