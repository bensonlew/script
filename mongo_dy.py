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
from mbio.api.database.mongo.mongo_backup import MongoBackup 



            

if __name__ == '__main__':
    import sys
    os.environ["current_mode"]="tool"
    os.environ["NTM_PORT"]="7322"
    os.environ["WFM_PORT"]="7321"


    ContractID = sys.argv[1]

    
    os.environ["ContractID"] = ContractID
    # test_api = MongoBackup(bind_object=None)

    project_type = sys.argv[2]
    db = Config().get_mongo_client(mtype=project_type)[Config().get_mongo_dbname(project_type)]
