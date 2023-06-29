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

from mbio.api.database.ref_rna_v2.api_base import ApiBase
from pymongo import MongoClient
import argparse



def mongo2uri(project_type, db_version=1, export_type="studio3t", ref=False):
    from biocluster.config import Config
    cfg = Config()
    cfg.get_mongo_client(mtype=project_type, db_version=db_version)[cfg.get_mongo_dbname(project_type, db_version=db_version)]
    if ref:
        uri = str(cfg._mongodb_info.values()[0]["refuri"])
        db_name = str(cfg._mongodb_info.values()[0]["refdbname"])
    else:
        uri = str(cfg._mongodb_info.values()[0]["uri"])
        db_name = str(cfg._mongodb_info.values()[0]["dbname"])

    uris = uri.split('/')
    uris[-2] += ":27017"
    uri = "/".join(uris)
    
    if export_type == "studio3t":
        uri = uri.split("?")[0] + "?" + \
        "serverSelectionTimeoutMS=5000&connectTimeoutMS=10000&authSource={}&authMechanism=SCRAM-SHA-1&3t.uriVersion=3&3t.connection.name={}&3t.databases={}&3t.alwaysShowAuthDB=true&3t.alwaysShowDBFromUserRole=true".format(
            db_name,
            "c_" + db_name + "_" + str(db_version),
            db_name
        )


    print("// {}".format(db_name))
    print(uri)
    del cfg

    



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='for update by table\n ')
    parser.add_argument('-p', type=str, default="all", help="project type.")
    parser.add_argument('-e', type=str, default='studio3t', help='studio3t')
    parser.add_argument('-d', type=int, default=1, help='db version.')
    parser.add_argument('-r', type=bool, default=False, help='db version.')

    args = parser.parse_args()
    os.environ["current_mode"]="workflow"
    os.environ["NTM_PORT"]="7322"
    os.environ["WFM_PORT"]="7321"

    projects = []

    if args.p == "all":
        for p in projects:
            mongo2uri(project_type=p, db_version=args.d, export_type=args.e, ref=args.r)
    else:
        mongo2uri(project_type=args.p, db_version=args.d, export_type=args.e, ref=args.r)

