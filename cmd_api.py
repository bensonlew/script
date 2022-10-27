# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'

from biocluster.api.database.base import Base, report_check
import types
from bson.objectid import ObjectId
from collections import OrderedDict
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from datetime import datetime

class ApiBase(object):
    def __init__(self, bind_object=None):
        super(ApiBase, self).__init__()
        self.index = 'test_db'
        self.es = Elasticsearch()


    def gendata(self, index, types, content_dict_list):
        '''
        Create datatable fromlist
        '''
        for content in content_dict_list:
            data_dict = content
            data_dict.update({
                "_op_type": 'create',
                "_index": index,
                "_type": types,
            })

            print data_dict
            yield data_dict

    def bulk_db_table(self, index, types, content_dict_list, tag_dict=None):
        '''
        Create main/detail table in database system.
        :param table_name: table name
        :param content_dict_list: list with dict as elements
        :param tag_dict: a dict to be added into each record in content_dict_list.
        :return: None or main table id
        '''

        data = self.gendata(index, types, content_dict_list)
        helpers.bulk(self.es, data)

    def bulk_cmd(self, cmd_path):
        header = ['cmds', '_id', 'time', 'num', 'dirs', 'user', 'pre_cmds']
        records_list = list()
        with open(cmd_path, 'r') as c_f:
            for line in c_f:
                cols = line.strip().split("\t")
                records = dict(zip(header, cols))
                records['_id'] = int(records['_id'])
                records['num'] = int(records['num'])
                records['time'] = datetime.strptime(records['time'], '%Y-%m-%d %H:%M:%S')
                records['dirs'] = list(eval(records['dirs']))
                records['pre_cmds'] = list(eval(records['pre_cmds']))
                records_list.append(records)
        self.bulk_db_table('sg_dev_cmds', 'cmds', records_list)

    def bulk_dir(self, dir_path):
        header = ['dir', '_id', 'time', 'num']
        records_list = list()
        with open(dir_path, 'r') as c_f:
            for line in c_f:
                cols = line.strip().split("\t")
                records = dict(zip(header, cols))
                records['_id'] = int(records['_id'])
                records['time'] = datetime.strptime(records['time'], '%Y-%m-%d %H:%M:%S')
                records_list.append(records)
        self.bulk_db_table('sg_dev_cmds', 'dirs', records_list)

    def bulk_file(self, file_path):
        header = ['file', '_id', 'time', 'num', 'dirs']
        records_list = list()
        with open(file_path, 'r') as c_f:
            for line in c_f:
                cols = line.strip().split("\t")
                records = dict(zip(header, cols))
                records['_id'] = int(records['_id'])
                records['num'] = int(records['num'])
                records['time'] = datetime.strptime(records['time'], '%Y-%m-%d %H:%M:%S')
                records['dirs'] = list(eval(records['dirs']))
                records_list.append(records)
        self.bulk_db_table('sg_dev_cmds', 'files', records_list)

if __name__ == '__main__':
    import sys

    es_api = ApiBase()
    # es_api.bulk_cmd(sys.argv[1])
    es_api.bulk_dir(sys.argv[2])
    es_api.bulk_file(sys.argv[3])

    '''

    table = pd.read_table(sys.argv[1], header=None, na_values="")
    table = table.fillna("")
    table.columns = ["ensembl_gene_id","ensembl_transcript_id","external_gene_name","external_gene_source","external_transcript_name","external_transcript_source_name","ensembl_peptide_id","description","chromosome_name","start_position","end_position","strand","transcript_start","transcript_end","transcription_start_site","transcript_length","gene_biotype","transcript_biotype"]
    data_list = table.to_dict('records')
    es_api = ApiBase()
    es_api.bulk_db_table("test_db", "document", data_list)
    '''
