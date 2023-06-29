# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'
import os
import re
import datetime
from bson.son import SON
from bson.objectid import ObjectId
import types
import gridfs
import json
import unittest
from biocluster.api.database.base import Base, report_check
from biocluster.config import Config
import argparse
import pandas as pd

class RefUpdate(object):
    def __init__(self, project_type, bind_object=None):
        super(RefUpdate, self).__init__()
        self.db = Config().get_mongo_client(mtype=project_type, db_version=1, ref=True)[Config().get_mongo_dbname(project_type, db_version=1, ref=True)]
        self._project_type = project_type
    

    def find_records(self, collection_name, query_dict):
        conn = self.db[collection_name]
        # print collection_name
        # print query_dict
        # print conn
        results = conn.find(query_dict)
        # print(list(results)[:10])
        # print conn
        df = pd.DataFrame(list(results))
        df.to_csv("monogo.tmp.tsv", sep='\t', index=False)



                        
if __name__ == '__main__':

    cmd_samples = '''

'''
    os.environ["current_mode"]="workflow"
    os.environ["NTM_PORT"]="7322"
    os.environ["WFM_PORT"]="7321"
    parser = argparse.ArgumentParser(description='for update by table\n ')
    parser.add_argument('-p', type=str, default="ref_rna_v2", help="project type.")
    parser.add_argument('-t', type=str, default=None, help='task')
    parser.add_argument('-d', type=str, default=None, help='detail table')
    parser.add_argument('-m', type=str, default=None, help='main_table')


    args = parser.parse_args()

    update_api = RefUpdate(args.p)
    collection_name = args.m
    update_api.find_records(collection_name, {})

#  python ./update_by_table.py  -p small_rna -c sg_annotation_query_detail   -t table -q_f 'lambda x:{"query_id" : ObjectId("5c1b4504a4e1af70b4bd4543"), "transcript_id":x[0]}' -i_f 'lambda x:{"gene_name": x[1]}'
