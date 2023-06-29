# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'
import os
from posixpath import split
import re
import sys
import datetime
from bson.son import SON
from bson.objectid import ObjectId
import types
import gridfs
import json
import unittest
from biocluster.api.database.base import Base, report_check
from biocluster.config import Config
from mbio.api.database.ref_rna_v2.api_base import ApiBase
from pymongo import MongoClient
import argparse
import pandas as pd


class MongoStorageStat(object):
    def __init__(self, project_type, db_version=1):
        super(MongoStorageStat, self).__init__()
        self.db_version = db_version
        self.db = Config().get_mongo_client(mtype=project_type, db_version=db_version)[Config().get_mongo_dbname(project_type, db_version=db_version)]
        self._project_type = project_type
        self.sanger_ip = "10.11.1.102"
        #self._db_name = Config().MONGODB + '_ref_rna'

    def storage_stat(self):
        '''
        备份collection到文件
        '''
        colls = self.db.list_collection_names()

        table_relation = self.db["sg_table_relation"]
        record = table_relation.find_one()
        target = record["target"]
        # print(target)
        main_coll_list = []
        detail_coll_dict = {}
        for c in target:
            main_coll_list.append(c[0])
            if isinstance(c[1], list):
                for cc in c[1]:
                    detail_coll_dict[cc] = [c[0], c[2]]
            else:
                if c[1]:
                    detail_coll_dict[c[1]] = [c[0], c[2]]
    
        line_dict = {
            "collection" : "",
            "type": "",
            "main_collection" : "",
            "main_id": ""
        }
        lines = list()
        for col in colls:
            line_dict_one = line_dict.copy()
            if col in main_coll_list:
                line_dict_one["collection"] = col
                line_dict_one["type"] = "main"
            else:
                line_dict_one["collection"] = col
                line_dict_one["type"] = "detail"
                if col in detail_coll_dict:
                    line_dict_one["main_collection"] = detail_coll_dict[col][0]
                    line_dict_one["main_id"] = detail_coll_dict[col][1]
            lines.append(line_dict_one)
        # print(lines)
        df = pd.DataFrame.from_records(lines)

        df.to_csv("{}.check_relation.tsv".format(self._project_type), index=False, sep="\t")
            

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='for update by table\n ')
    parser.add_argument('-p', type=str, default="ref_rna_v2", help="project type.")
    parser.add_argument('-f', type=str, default=None, help='field_list.')
    parser.add_argument('-d', type=str, default=None, help='db version.')

    args = parser.parse_args()
    os.environ["current_mode"]="workflow"
    os.environ["NTM_PORT"]="7322"
    os.environ["WFM_PORT"]="7321"

    api = MongoStorageStat(args.p, db_version=args.d)        

    api.storage_stat()

