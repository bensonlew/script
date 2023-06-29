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

    def task2_table(self):
        '''
        备份collection到文件
        '''

        coll = self.db["sg_task"]
        result_cursor = coll.find()
        df = pd.DataFrame(list(result_cursor))
        df.to_csv("{}_{}.csv".format(self._project_type, "sg_task"), sep="\t", index=False)


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
    api.task2_table()

