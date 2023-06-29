# -*- coding: utf-8 -*-
# __author__ 'liubinxu'
import re
import datetime
import unittest
import os
import types
from biocluster.config import Config
import pandas as pd
import argparse

class scrnaUpdate(object):
    def __init__(self, project_type, bind_object=None):
        super(scrnaUpdate, self).__init__()
        self.db = Config().get_mongo_client(mtype=project_type, db_version=1)[Config().get_mongo_dbname(project_type, db_version=1)]
        self._project_type = project_type

    def update_record_by_dict(self, collection_name, query_dict, insert_dict):
        conn = self.db[collection_name]
        print(query_dict)
        print("***", query_dict)
        if "_id" in query_dict:
            query_dic = {"_id": query_dict["_id"]}
        else:
            query_dic = query_dict
        print query_dic
        print insert_dict
        conn.update(query_dic, {"$set": insert_dict}, upsert=True)

    def find_record(self, collection_name, query_dict):
        conn = self.db[collection_name]
        result = conn.find_one(query_dict)
        return result 
    def find_records(self, collection_name, query_dict):
        conn = self.db[collection_name]
        results = conn.find(query_dict)
        print conn
        return results
    
    def update_mouse(self, descript_file):
        a = pd.read_table(descript_file, sep="\t", header=0)
        gene2des_dict = dict(zip(a['gene_id'], a['description']))
        for gene,des in gene2des_dict.items():
            gene_results = self.find_records("sg_genes_detail", {"gene_id": gene})
            for gene_result in gene_results:
                if(type(gene_result["description"]) == int):
                    collection_name = "sg_genes_detail"
                    query_dict = {"_id": gene_result["_id"]}
                    insert_dict = {"description": des}
                    self.update_record_by_dict(collection_name, query_dict, insert_dict)


if __name__ == '__main__':
    os.environ["current_mode"]="workflow"
    os.environ["NTM_PORT"]="7322"
    os.environ["WFM_PORT"]="7321"

    parser = argparse.ArgumentParser(description='for update by table\n ')
    parser.add_argument('-p', type=str, default="scrna", help="project type.")
    parser.add_argument('-t', type=str, default=None, help='task')
    parser.add_argument('-d', type=str, default=None, help='detail table')
    parser.add_argument('-m', type=str, default=None, help='main_table')

    args = parser.parse_args()

    update_api = scrnaUpdate(args.p)
    des_table = args.d
    update_api.update_mouse(des_table)

