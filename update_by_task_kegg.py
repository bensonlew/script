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

    def update_by_main_table(self, main_table, detail_table, query_dict, create_from=None, create_to=None):
        print query_dict
        if create_from:
            query_dict.update({"created_ts": {"$gt": create_from}})
        if create_to:
            query_dict.update({"created_ts": {"$lt": create_to}})
        main_records = self.find_records(main_table, query_dict)
        for rec in main_records:
            main_id = rec["main_id"]
            name = rec["name"]
            print name
            details = self.find_records(detail_table, {"kegg_enrich_id": main_id})
            for detail in details:
                if "seq_list" in detail:
                    # ref_rna_v2
                    if self._project_type == "denovo_rna_v2":
                        seq_list  = detail["seq_list"]
                        if isinstance(seq_list, list):
                            insert = {"seq_lists": seq_list, "gene_lists": "|".join(seq_list)}
                            print("{} to {}".format(detail['_id'], insert))
                            self.update_record_by_dict(detail_table, detail, insert)
                    else:
                        seq_list  = detail["seq_list"]
                        if isinstance(seq_list, list):
                            insert = {"seq_list": "|".join(seq_list)}
                            print("{} to {}".format(detail['_id'], insert))
                            self.update_record_by_dict(detail_table, detail, insert)
                else:
                    pass
                    # self._project_type = "denovo_rna_v2":
                    # gene_lists = detail["gene_lists"]
                    # if isinstance(gene_lists, str):
                    #     insert = {"seq_list": gene_lists.split("|")}
                    #     print("{} to {}".format(detail['_id'], insert))
                    #     self.update_record_by_dict(detail_table, detail, insert)

    def update_by_main_table_goenrich(self, main_table, detail_table, query_dict, create_from=None, create_to=None):
        print query_dict
        if create_from:
            query_dict.update({"created_ts": {"$gt": create_from}})
        if create_to:
            query_dict.update({"created_ts": {"$lt": create_to}})
        main_records = self.find_records(main_table, query_dict)
        for rec in main_records:
            main_id = rec["main_id"]
            name = rec["name"]
            print name
            details = self.find_records(detail_table, {"go_enrich_id": main_id})
            for detail in details:
                print detail
                if "seq_list" in detail and "gene_list" not in detail:
                    seq_list = detail["seq_list"]
                    seq_str = detail["seq_str"]
                    insert = {"gene_list": seq_list, "gene_str": seq_str}
                    print("{} to {}".format(detail['_id'], insert))
                    self.update_record_by_dict(detail_table, detail, insert)

    def update_by_main_table_goenrich2(self, main_table, detail_table, query_dict, create_from=None, create_to=None):
        print query_dict
        if create_from:
            query_dict.update({"created_ts": {"$gt": create_from}})
        if create_to:
            query_dict.update({"created_ts": {"$lt": create_to}})
        main_records = self.find_records(main_table, query_dict)
        for rec in main_records:
            main_id = rec["main_id"]
            name = rec["name"]
            if "level" in rec and "geneset_type" not in rec and rec["params"] != "":
                params = json.load(rec["params"])
                insert = {
                    "geneset_type": rec["level"],
                    "has_enrich_file": "yes",
                    "geneset_id": params["geneset_id"]
                }
                print insert
                self.update_record_by_dict(main_table, rec, insert)

    def update_by_main_table_goenrich3(self, main_table, detail_table, query_dict, create_from=None, create_to=None):
        print query_dict
        if create_from:
            query_dict.update({"created_ts": {"$gt": create_from}})
        if create_to:
            query_dict.update({"created_ts": {"$lt": create_to}})
        main_records = self.find_records(main_table, query_dict)
        for rec in main_records:
            main_id = rec["main_id"]
            if "result_dir" in rec:
                result_dir = rec["result_dir"]
                if result_dir.endswith("go_enrich_stat.xls/go_enrich_geneset_list_gene.xls"):
                    insert = {
                        "result_dir": os.path.dirname(result_dir)
                    }
                    print insert
                    self.update_record_by_dict(main_table, rec, insert)

    def update_by_main_table_goclass(self, main_table, detail_table, query_dict, create_from=None, create_to=None):
        print query_dict
        if create_from:
            query_dict.update({"created_ts": {"$gt": create_from}})
        if create_to:
            query_dict.update({"created_ts": {"$lt": create_to}})
        main_records = self.find_records(main_table, query_dict)
        for rec in main_records:
            main_id = rec["main_id"]
            name = rec["name"]
            print name
            details = self.find_records(detail_table, {"go_regulate_id": main_id})
            for detail in details:
                update_dict = {}
                for k,v in detail.items():
                    if k.endswith("_list"):
                        update_dict.update({k.replace("_list", "_genes"): v})
                if len(update_dict) > 0:
                    print("{} to {}".format(detail['_id'], update_dict))
                    self.update_record_by_dict(detail_table, detail, update_dict)
                else:
                    pass
    def update_by_main_table_keggclass(self, main_table, detail_table, query_dict, create_from=None, create_to=None):
        print query_dict
        if create_from:
            query_dict.update({"created_ts": {"$gt": create_from}})
        if create_to:
            query_dict.update({"created_ts": {"$lt": create_to}})
        main_records = self.find_records(main_table, query_dict)
        for rec in main_records:
            main_id = rec["main_id"]
            name = rec["name"]
            print name
            details = self.find_records(detail_table, {"kegg_id": main_id})
            for detail in details:
                update_dict = {}
                for k,v in detail.items():
                    if k.endswith("_list"):
                        update_dict.update({k.replace("_list", "_genes"): v})
                if len(update_dict) > 0:
                    print("{} to {}".format(detail['_id'], update_dict))
                    self.update_record_by_dict(detail_table, detail, update_dict)
                else:
                    pass
 
                

    def update_by_table(self, collection_name, table, query_dict_f, insert_dict_f):
        '''
        query_dict_f: lambda function how to get query_dict
        insert_dict_f: lambda function how to get insert_dict
        table: tab sep table file 
        '''
        q_f = eval(query_dict_f)
        i_f = eval(insert_dict_f)
        print q_f
        print i_f
        with open(table, 'r') as f:
            for line in f:
                cols = line.strip().split("\t")
                query_dict = dict(q_f(cols))
                insert_dict = dict(i_f(cols))
                
                try:
                    self.update_record_by_dict(collection_name, query_dict, insert_dict)
                except:
                    record = self.find_record(collection_name, query_dict)
                    if record:
                        self.update_record_by_dict(collection_name, dict(record), insert_dict)
                    else:
                        print "{} not find".format(query_dict)

    def update_by_dict(self, collection_name, query_dict, insert_dict):
        '''
        query_dict:  query_dict
        insert_dict: insert_dict
        '''
        query_dict = eval(query_dict)
        insert_dict = eval(insert_dict)
        print query_dict
        records = self.find_records(collection_name, query_dict)
        for record in records:
            try:
                # print dict(record)
                self.update_record_by_dict(collection_name, dict(record), insert_dict)
            except:
                print "cat not update {}".format(record)


if __name__ == '__main__':

    cmd_samples = '''
python ./update_by_table.py  -p small_rna -c sg_annotation_query_detail   -t table -q_f 'lambda x:{"query_id" : ObjectId("5c1b4504a4e1af70b4bd4543"), "transcript_id":x[0]}' -i_f 'lambda x:{"gene_name": x[1]}'
python update_by_table.py -m one2many -c sg_annotation_query_detail -p prok_rna -q '{"query_id":ObjectId("5bd993cc28fb4f0b8e150f4f"), "ko_id":None}' -i '{"ko_id":""}'
'''
    os.environ["current_mode"]="workflow"
    os.environ["NTM_PORT"]="7322"
    os.environ["WFM_PORT"]="7321"
    parser = argparse.ArgumentParser(description='for update by table\n ')
    parser.add_argument('-p', type=str, default="ref_rna_v2", help="project type.")
    parser.add_argument('-d', type=str, default=None, help='detail table')
    parser.add_argument('-m', type=str, default=None, help='main_table')
    parser.add_argument('-f', type=str, default=None, help='from when')
    parser.add_argument('-t', type=str, default=None, help='to_when')
    args = parser.parse_args()

    update_api = RefUpdate(args.p)
    query_dict = {}
    update_api.update_by_main_table_goenrich3(args.m, args.d, query_dict, create_from=args.f, create_to=args.t)

    #  python ./update_by_table.py  -p small_rna -c sg_annotation_query_detail   -t table -q_f 'lambda x:{"query_id" : ObjectId("5c1b4504a4e1af70b4bd4543"), "transcript_id":x[0]}' -i_f 'lambda x:{"gene_name": x[1]}'
