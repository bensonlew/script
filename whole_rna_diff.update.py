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
import glob

files = glob.glob("*_vs_*_deseq2*.xls")
for file_ in files:
    ctrl, case = file_.split("_deseq2")[0].split("_vs_")
    os.system("sed '1s/{}_mean_tpm\t{}_mean_tpm/{}_mean_tpm\t{}_mean_tpm/'  -i {}".format(case, ctrl, ctrl, case, file_))

files = glob.glob("*_vs_*_degseq.xls")
for file_ in files:
    ctrl, case = file_.split("_degseq")[0].split("_vs_")
    os.system("sed '1s/{}_mean_tpm\t{}_mean_tpm/{}_mean_tpm\t{}_mean_tpm/'  -i {}".format(case, ctrl, ctrl, case, file_))
