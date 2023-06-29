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
from bson import json_util

class RefUpdate(object):
    def __init__(self, project_type, bind_object=None):
        super(RefUpdate, self).__init__()
        self.db = Config().get_mongo_client(mtype=project_type, db_version=0)[Config().get_mongo_dbname(project_type, db_version=0)]
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

    def get_exp_details(self, task_id):

        conn = self.db["exp"]
        exp_record = conn.find_one({
            "task_id": task_id,
            "level": "T"
        })
        query_dict = {
            "exp_id": exp_record["main_id"],            
        }
        conn = self.db["exp_detail"]
        results = conn.find(query_dict)
        g2t = dict()
        for result in results:
            if "gene_id" in result:
                if result["gene_id"] in g2t:
                    g2t[result["gene_id"]].append(result["transcript_id"])
                else:
                    g2t[result["gene_id"]] = [result["transcript_id"]]
        return g2t

    def get_trans_detail(self, task_id):
        conn = self.db["genes"]
        gene_record = conn.find_one({
            "task_id": task_id
        })
        query_dict = {
            "genes_id": gene_record["main_id"],
            "level": "T", 
            "category": "lncRNA"           
        }
        print(query_dict)
        conn = self.db["genes_detail"]
        results = conn.find(query_dict)
        t = dict()
        for result in results:
            t[result["transcript_id"]] = result
        return t

    def update(self, task_id):
        g2t = self.get_exp_details(task_id)
        t = self.get_trans_detail(task_id)

        conn = self.db["genes"]
        gene_record = conn.find_one({
            "task_id": task_id
        })
        query_dict = {
            "genes_id": gene_record["main_id"],
            "level": "G"         
        }
        # print(g2t)
        # print(t)
        conn = self.db["genes_detail"]
        results = conn.find(query_dict)
        update_list = []
        old_list = []
        for result in results:
            gene_id = result["gene_id"]
            if len(result["transcripts"]) < len(g2t[gene_id]):
                tran_list2 = result["transcripts"][:]
                tran_list = result["transcripts"]
                tran_ids = set([x["transcript_id"] for x in tran_list])
                add_trans = set(g2t[gene_id])  - tran_ids
                for tran_id in add_trans:
                    if tran_id in t:
                        t_dic = t[tran_id]
                        tran_list.append({
                            "start" : t_dic["start"],
                            "length" : t_dic["length"],
                            "transcript_id" : tran_id,
                            "end" : t_dic["end"],
                            "strand" : t_dic["strand"]
                        })
                if len(tran_list) != len(tran_list2):
                    update = [result["_id"], tran_list]
                    old_list.append([result["_id"], tran_list2])

                    print(update)
                    update_list.append(update)
        with open("old.back.json", "w") as f:
            f.write(json_util.dumps(old_list))
        for update in update_list:
            query_dict = {"_id": update[0], "genes_id": gene_record["main_id"]}
            insert_dict = {"transcripts": update[1]}
            conn.update(query_dict, {"$set": insert_dict}, upsert=True)
            




                        
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

    update_api.update(args.t)

#  python ./update_by_table.py  -p small_rna -c sg_annotation_query_detail   -t table -q_f 'lambda x:{"query_id" : ObjectId("5c1b4504a4e1af70b4bd4543"), "transcript_id":x[0]}' -i_f 'lambda x:{"gene_name": x[1]}'
