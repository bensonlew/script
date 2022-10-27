# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'

import logging
import sys
import time
import json
from biocluster.config import Config
from concurrent.futures import ThreadPoolExecutor
import sqlite3
from collections import defaultdict
import re
import os
from bson.objectid import ObjectId
from mbio.api.database.whole_transcriptome.api_base import ApiBase

class RefUpdate(ApiBase):
    def __init__(self, project_type, bind_object=None):
        super(RefUpdate, self).__init__(bind_object)
        self._config.DBVersion = 1
        # self.db = Config().get_mongo_client(mtype=project_type, db_version=1)[Config().get_mongo_dbname(project_type, db_version=1)]
        self._project_type = project_type
        self.map_dict = dict()


    def create_db_table(self, table_name, content_dict_list, tag_dict=None):
        '''
        Create main/detail table in database system.
        :param table_name: table name
        :param content_dict_list: list with dict as elements
        :param tag_dict: a dict to be added into each record in content_dict_list.
        :return: None or main table id
        '''
        table_id = None
        conn = self.db[table_name]
        if tag_dict:
            for row_dict in content_dict_list:
                row_dict.update(tag_dict)
        record_num = len(content_dict_list)
        try:
            if record_num > 5000:
                for i in range(0, record_num, 3000):
                    tmp_list = content_dict_list[i: i + 3000]
                    conn.insert_many(tmp_list)
            else:
                if record_num >= 2:
                    conn.insert_many(content_dict_list)
                else:
                    table_id = conn.insert_one(content_dict_list[0]).inserted_id
        except Exception as e:
            print e
        else:
            return table_id
    def add_snp_detail(self, snp_anno, snp_id, new_output=None):
        """
        导入SNP详情表的函数
        :param snp_anno: snp模块的结果文件夹，即~/output_dir/
        :param snp_id: SNP主表的ID
        :return:
        """
        data_anno = os.path.join(snp_anno, "data_anno_pre.xls")
        with open(data_anno, "r") as f:
            headers = f.readline().strip().split("\t")
            data_list = list()
            for row, line in enumerate(f):
                data = dict()
                line = line.strip().split('\t')
                if len(headers) == len(line):
                    for n in range(len(headers)):
                        if headers[n] in ["reads_num", "qual"]:
                            try:
                                data.update({headers[n]: float(line[n])})
                            except:
                                data.update({headers[n]: line[n]})
                        else:
                            data.update({headers[n]: line[n]})
                    data.update({"snp_id": snp_id})
                    data_list.append(data)
                    if row != 0 and row % 100000 == 0:
                        try:
                            self.create_db_table('snp_detail', data_list)
                        except Exception as e:
                            print("导入SNP详情表出错: {}".format(e))
                        else:
                            print("导入SNP详情表成功，已经导入了%s条记录" % str(row))
                            data_list = list()
            if data_list:
                try:
                    self.create_db_table('snp_detail', data_list)
                except Exception as e:
                    print("导入SNP详情表出错:%s" %e)
                else:
                    print("导入SNP详情表成功，已经导入了%s条记录" % str(row))
                    data_list = list()


if __name__ == '__main__':
    logging.info('Usage: python add_batch.py <project_type>')

    project_type = sys.argv[1]

    ref = RefUpdate(project_type=project_type)
    ref.add_snp_detail(snp_anno=sys.argv[2], snp_id=ObjectId(sys.argv[3]))
