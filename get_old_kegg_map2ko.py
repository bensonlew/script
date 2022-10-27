# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
from biocluster.config import Config
import re
from Bio.KEGG.KGML import KGML_parser
from Bio.Graphics.KGML_vis_t import KGMLCanvas
from mbio.packages.rna.kegg_html import KeggHtml
from reportlab.lib import colors
import collections
from itertools import islice
import subprocess
import gridfs
import os
import sys
import tarfile
import shutil


def get_old():
    # 输入blast比对的xml文件
    """
    输入基因/转录本id对应的K编号文件(kegg.list)，输出kegg_table.xls
    """

    client = Config().get_mongo_client(mtype="ref_rna", ref=True)
    mongodb = client[Config().get_mongo_dbname("ref_rna", ref=True)]  # 20171101 by zengjing 数据库连接方式修改
    ko_coll = mongodb.kegg_ko_v1

    gloabl = ["map01100", "map01110", "map01120", "map01130", "map01200", "map01210", "map01212", "map01230", "map01220"]

    ko_records = ko_coll.find()
    for record in ko_records:
        ko = record["ko_id"]
        pathways = record["pathway_id"]
        for pathway in pathways:
            pathway = pathway.replace("ko", "map")
            if pathway in gloabl:
                pass
            else:
                print "path:{}\tko:{}".format(pathway, ko)

if __name__ == '__main__':
    get_old()
