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

class RefUpdate(Base):
    def __init__(self, project_type, bind_object=None):
        super(RefUpdate, self).__init__(bind_object)
        self._project_type = project_type
    
    def update_record_by_dict(self, collection_name, query_dict, insert_dict):
        conn = self.db[collection_name]
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
    parser = argparse.ArgumentParser(description='for update by table\n ')
    parser.add_argument('-p', type=str, default="ref_rna_v2", help="project type.")
    parser.add_argument('-t', type=str, default=None, help='table file')
    parser.add_argument('-c', type=str, default=None, help='collection name')
    parser.add_argument('-q_f', type=str, default=None, help='lambda function for get query dict')
    parser.add_argument('-i_f', type=str, default=None, help='lambda function for get insert dict')
    parser.add_argument('-q', type=str, default=None, help='query dict')
    parser.add_argument('-i', type=str, default=None, help='query dict')
    parser.add_argument('-m', type=str, default="many2one", help='update method, one2one, one2many, many2one, many2many')
    parser.add_argument('--sample', type=bool, default=None, help='cmd samples')

    args = parser.parse_args()
    if args.sample:
        print cmd_samples
    update_api = RefUpdate(args.p)
    if args.m == "many2one":
        pass
    elif args.m == "one2many":
        update_api.update_by_dict(args.c, args.q, args.i)
    elif args.m == "many2one":
        update_api.update_by_table(args.c, args.t, args.q_f, args.i_f)


#  python ./update_by_table.py  -p small_rna -c sg_annotation_query_detail   -t table -q_f 'lambda x:{"query_id" : ObjectId("5c1b4504a4e1af70b4bd4543"), "transcript_id":x[0]}' -i_f 'lambda x:{"gene_name": x[1]}'
