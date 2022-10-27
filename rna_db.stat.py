# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'
from __future__ import division
import os
from biocluster.config import Config
from bson.objectid import ObjectId
import types
import json
import re
from types import StringTypes
import gridfs


def export_stat(collect_name):
    db = Config().mongo_client[Config().MONGODB + "_ref_rna"]
    
    print collect_name
    collection = db[collect_name]
    #size = collection.stats()
    #storageSize = collection.stats()

    my_result = collection.find_one()
    #print "collection:{}\tsize:{}\tstorageSize{}\n".format(collection,size,storageSize)
    print my_result

    return 1
def get_collections():
    db = Config().mongo_client[Config().MONGODB + "_ref_rna"]
    collections = db.collection_names()
    #print collections
    return collections
    

if __name__ == "__main__":
    collections = get_collections()
    #db = Config().mongo_client[Config().MONGODB + "_ref_rna"]
    for collect_name in collections:
        export_stat(collect_name)
