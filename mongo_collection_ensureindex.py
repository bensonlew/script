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
from pymongo import ASCENDING, DESCENDING, HASHED



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

    def get_index(self):
        '''
        获取所有collection 对应的index， 最好在线上运行
        '''
        self.index_dict = dict()
        cols = self.db.list_collection_names()
        for col in cols:
            if col in ["system.profile"]:
                continue
            index = self.db[col].index_information()
            index.pop("_id_")
            self.index_dict[col] = index
        with open("all_index.json", "w") as f:
            f.write(json.dumps(self.index_dict, indent=4, ensure_ascii=False).encode('utf8').decode())


    def ensure_all_indexes(self, json_file=None):
        # self.bind_object.logger.info('ensuring all indexes')
        # script_path = os.path.split(os.path.realpath(__file__))[0]


        with open(json_file, "r") as f:
            index_dict = json.load(f)

        for col, indexes in index_dict.items():
            for name, index in indexes.items():
                self.create_index(col, name, index)

    def create_index(self, collection, name, index):
        if index:
            col = self.db[collection]
            index_create = []
            for k in index["key"]:
                if k[1] == 1:
                    index_create.append((k[0], ASCENDING))
                elif k[1] == -1:
                    index_create.append((k[0], DESCENDING))
                elif k[1] == "hashed":
                    index_create.append((k[0], HASHED))
                else:
                    print("unknown index {} {}".format(collection, name))
            try:
                col.create_index(index_create, name=name)
            except Exception as e:
                print(e)
            print("{}的{}索引{}构建完成！".format(collection, name, index))
            #self.bind_object.logger.info("{}的{}索引{}构建完成！".format(collection, name, index))
        else:
            print("传入的index值为空，不进行建索引！")
            # self.bind_object.logger.info("传入的index值为空，不进行建索引！")

            

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

    api.ensure_all_indexes(args.f)

