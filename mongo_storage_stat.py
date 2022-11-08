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


class MongoStorageStat(object):
    def __init__(self, project_type, db_version=1):
        super(MongoStorageStat, self).__init__()
        self.db_version = db_version
        self.db = Config().get_mongo_client(mtype=project_type, db_version=db_version)[Config().get_mongo_dbname(project_type, db_version=db_version)]
        self._project_type = project_type
        self.sanger_ip = "10.11.1.102"
        #self._db_name = Config().MONGODB + '_ref_rna'

    def storage_stat(self, field_list):
        '''
        备份collection到文件
        '''
        f = open(self._project_type + "_" + str(self.db_version) + "_storage.xls", "w")
        colls = self.db.list_collection_names()
        f.write("collection\tindex\t" + "\t".join(field_list) + "\n")
        collection_list = list()
        for coll in colls:
            # stat_dict = self.db[coll].stats()
            if coll in ["system.profile"]:
                continue
            try:
                stat_dict = self.db.command("collstats", coll)
                coll_c = self.db[coll]
                index_dict = coll_c.index_information()
                index_clean = dict()
                for k,v in index_dict.items():
                    index_clean[k] = dict(v['key'])
            
            except Exception as e:
                print(e)
                continue
            # print stat_dict
            values = list()
            for field in field_list:
                fields = field.split(".")
                if field in stat_dict:
                    values.append(stat_dict[field])
                elif len(fields) == 2:
                    values.append(stat_dict[fields[0]][fields[1]])
                elif len(fields) == 3:
                    if "wiredTiger" not in stat_dict:
                        """
                        分片统计
                        """
                        vs = list()
                        for k, v in stat_dict["shards"].items():
                            vs.append(v[fields[0]][fields[1]][fields[2]])
                        values.append(sum(vs))
                    else:
                        values.append(stat_dict[fields[0]][fields[1]][fields[2]])
                else:
                    if field == "totalSize":
                        values.append(stat_dict["storageSize"] + stat_dict["totalIndexSize"])
                    else:
                        values.append("None")
            collection_list.append([coll,str(index_clean)] + values)

        collection_list_sort = sorted(collection_list, key=lambda x:x[-3])
        for collect in collection_list_sort:
            f.write("\t".join([str(v) for v in collect])  + "\n")
        
        total_storage = sum([x[-3] for x in collection_list])
        reuse_storage = sum([x[-1] for x in collection_list])
        print("{}\t{}\t{}\t{}".format(self._project_type, self.db_version, total_storage, reuse_storage))
        f.close()



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

    if args.f:
        field_list = args.f.split(",")
    else:
        field_list = [
            "size",
            "count",
            "avgObjSize",
            "storageSize",
            "freeStorageSize",
            "totalIndexSize",
            "totalSize",
            "wiredTiger.block-manager.blocks allocated",
            "wiredTiger.block-manager.file bytes available for reuse"
        ]


    api.storage_stat(field_list)

