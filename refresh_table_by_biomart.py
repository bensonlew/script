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

biomart = sys.argv[1]
old = sys.argv[2]
new = old + ".new"

a = pd.read_table(biomart, sep = "\t")
b = zip(a['Transcript stable ID'], a['Gene description'])
c = dict(b)

with open(old, 'r') as f_in, open(new, 'w') as f_out:
    f_out.write(f_in.readline())
    for line in f_in:
        cols = line.split("\t")
        cols[5] = str(c.get(cols[1], ''))
        f_out.write("\t".join(cols))

#  python ./update_by_table.py  -p small_rna -c sg_annotation_query_detail   -t table -q_f 'lambda x:{"query_id" : ObjectId("5c1b4504a4e1af70b4bd4543"), "transcript_id":x[0]}' -i_f 'lambda x:{"gene_name": x[1]}'
