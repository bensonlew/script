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
import sys
import pandas as pd

class RefUpdate(object):
    def __init__(self, project_type, bind_object=None):
        super(RefUpdate, self).__init__()
        self.db = Config().get_mongo_client(mtype=project_type, db_version=1)[Config().get_mongo_dbname(project_type, db_version=1)]
        self._project_type = project_type
    
    def update_record_by_dict(self, collection_name, query_dict, insert_dict):
        conn = self.db[collection_name]
        print query_dict
        conn.update(query_dict, {"$set": insert_dict}, upsert=True)

    def find_record(self, collection_name, query_dict):
        conn = self.db[collection_name]
        result = conn.find_one(query_dict)
        return result 
    def find_records(self, collection_name, query_dict):
        conn = self.db[collection_name]
        results = conn.find(query_dict)
        print conn
        return results

    def update_by_task(self, main_table="sg_geneset", detail_table="sg_geneset_detail", task_id=None):
        if task_id == "all":
            query_dict = {"source": "diff_exp"}
        else:
            query_dict = {"task_id": task_id, "source": "diff_exp"}
        main_records = self.find_records(main_table, query_dict)
        
        for rec in main_records:
            # print rec
            task_id = rec["task_id"]
            main_id = rec["main_id"]
            name = rec["name"]
            detail = self.find_record(detail_table, {"geneset_id": main_id})
            seq_list  = detail["seq_list"]
            regulate_list = detail["regulate_list"]
            if len(seq_list) != len(regulate_list):
                print "{}\t{}\t geneset length mismatch regulate_list length".format(task_id, name)
                cmp_name = name.split("_mRNA")[0]
                diff_pd = pd.read_table(cmp_name + ".degseq.xls", header=0, sep='\t')
                sig_regulate = list(diff_pd['regulate'][(~diff_pd['seq_id'].str.contains("sRNA")) & (diff_pd['significant'] == 'yes')])

                update = {"regulate_list": sig_regulate}
                self.update_record_by_dict(detail_table, {"geneset_id": main_id}, update)
                print "{} updated".format(main_id)
            # self.update_record_by_dict(main_table, query_dict, {"source": "diff_e
            # xp"})


if __name__ == '__main__':
    update_api = RefUpdate("prok_rna")
    update_api.update_by_task(task_id=sys.argv[1])
