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

class SangerApi(Base):
    def __init__(self, project_type, bind_object=None):
        super(SangerApi, self).__init__(bind_object)
        self._project_type = project_type
                        
    def get_all_indexes(self):
        '''
        query_dict:  query_dict
        insert_dict: insert_dict
        '''
        ensure_file = open("ensure.sh", 'w')
        collections = self.db.collection_names()
        for collection in collections:
            indexs = self.db[collection].index_information()
            for index_name, index  in indexs.items():
                if index_name in ["_id_", "_id"]:
                    continue
                else:
                    
                    key_strs = list()
                    for key in index["key"]:
                        key_strs.append('"{}": {}'.format(key[0], key[1]))
                    ensure_file.write('db.getSiblingDB("sanger_{}").{}.ensureIndex({}{}{})\n'.format(self._project_type, collection, "{",", ".join(key_strs), "}"))
                    print collection, str(index["key"])

                        
if __name__ == '__main__':

    cmd_samples = '''
'''
    parser = argparse.ArgumentParser(description='get a project all collection index\n ')
    parser.add_argument('-p', type=str, default="ref_rna_v2", help="project type.")

    args = parser.parse_args()

    sanger_api = SangerApi(args.p)
    sanger_api.get_all_indexes()


#  python ./update_by_table.py  -p small_rna -c sg_annotation_query_detail   -t table -q_f 'lambda x:{"query_id" : ObjectId("5c1b4504a4e1af70b4bd4543"), "transcript_id":x[0]}' -i_f 'lambda x:{"gene_name": x[1]}'
