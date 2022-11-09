# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'

# from biocluster.api.database.base import Base, report_check
import types
from biocluster.config import Config
from bson.objectid import ObjectId
from collections import OrderedDict
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from datetime import datetime
from cmd_mongo_api import CmdMongo

class ApiBase(object):
    def __init__(self, bind_object=None):
        super(ApiBase, self).__init__()
        self.index = 'test_db'
        self.logger = bind_object
        self.es = Elasticsearch(hosts=['localhost:9299'], timeout=200)

    def get_mongo_db(self):
        self.project_type = 'denovo_assembly'
        self.mongo_db = Config().get_mongo_client(mtype=self.project_type)[Config().get_mongo_dbname(self.project_type)]
        return self.mongo_db

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
            data_dict["c_id"] = data_dict["id"]
            data_dict.pop("id")
            # print data_dict
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


    def syn_cmd(self):
        mongo_db = self.get_mongo_db()
        col = mongo_db["sg_dev_cmds"]
        results = col.find({}, {"_id": 0})
        if self.es.indices.exists(index='sg_dev_cmds'):
            pass
        else:
            self.create_db(index_name='sg_dev_cmds')
        self.bulk_db_table('sg_dev_cmds', 'cmds', results)

    def syn_dir(self):
        mongo_db = self.get_mongo_db()
        col = mongo_db["sg_dev_dirs"]
        results = col.find({}, {"_id": 0})
        if self.es.indices.exists(index='sg_dev_dirs'):
            pass
        else:
            self.create_db(index_name='sg_dev_dirs')
        self.bulk_db_table('sg_dev_dirs', 'dirs', results)

    def syn_file(self):
        mongo_db = self.get_mongo_db()
        col = mongo_db["sg_dev_files"]
        results = col.find({}, {"_id": 0})
        if self.es.indices.exists(index='sg_dev_files'):
            pass
        else:
            self.create_db(index_name='sg_dev_files')
        self.bulk_db_table('sg_dev_files', 'files', results)

    def create_db(self, index_name, body=None):
        body = {
            "settings": {
                "analysis": {
                    "tokenizer": {
                        "my_tokenizer": {
                            "type": "pattern",
                            "pattern": "[ _./]"
                        }
                    },
                    "analyzer": {
                        "default": {
                            "tokenizer": "my_tokenizer",
                            "filter": ["lowercase"]
                        }
                    }
                }
            }
        }
        self.es.indices.create(index=index_name, body=body)


    def text_search(self, string, types, sort_field="num"):
        types2index = {
            "cmds": "sg_dev_cmds",
            "dir": "sg_dev_dirs",
            "file": "sg_dev_files"
        }

        index = types2index[types]

        if types == "cmds":
            source_includes = ["cmds"]
        if types == "file":
            source_includes = ["file"]
        if types == "dir":
            source_includes = ["dir"]

        size = 200

        body =  {
            "query": {
                "match": {
                    types: {"query": string,  "fuzziness": "AUTO"}
                }
            }
        }
        # print index,body
        results = self.es.search(index=index,
                                 body=body,
                                 size=size)

        # print results
        data_result = ""
        if "hits" in results and len(results["hits"]["hits"]) > 0:
            # print results["hits"]["hits"]
            data_result = "\n".join([r.get("_source", {}).get(types, "") for r in results["hits"]["hits"]])
        # print data_result
        return data_result

    def cmd_update(self, string, dirs=[], pre_cmds=[], num=1, user="", ssh_client="", ssh_port=""):
        # 更新命令记录
        index = "sg_dev_cmds"
        body =  {
            "query": {
                "term": {
                    "cmds.keyword": string
                }

            }
        }
        results = self.es.search(index=index,
                                 body=body,
                                 size=1)
        self.logger.info("results is {}".format(results))
        if len(results["hits"]["hits"]) > 0:
            result = results["hits"]["hits"][0]
            self.logger.info( "update id {}".format(result["_id"]))
            self.es.update(index=index,
                           doc_type="cmds",
                           id = result["_id"],
                           body = {
                                 "doc": {
                                     "num": result["_source"]["num"] + num,
                                     "dirs": list(set(result["_source"]["dirs"] + dirs))
                                 }
                           }
            )
            cmd_id = result["_source"]["c_id"]
        else:
            largest_body = {
                "aggs" : {
                    "max_id" : {
                        "max" : {
                            "field" : "c_id"
                        }
                    }
                },
                "size":0
            }
            self.logger.info(largest_body)
            results = self.es.search(index=index,
                                     body=largest_body)

            self.logger.info(results)
            cmd_id = int(results["aggregations"]["max_id"]["value"]) + 1
            self.logger.info(cmd_id)
            body = {
                'c_id': cmd_id,
                "cmds": string,
                'num': num,
                'time': datetime.now(),
                'dirs': dirs,
                'user': user,
                'pre_cmds': pre_cmds,
                'ssh_client': ssh_client,
                'ssh_port': ssh_port
            }
            # self.logger.info( body)
            a = self.es.index(index = index, body=body, doc_type="cmds")
        return cmd_id
        # return cmd_id

    def dir_update(self, string, num=1):
        # 更新路径记录

        index = "sg_dev_dirs"
        body =  {
            "query": {
                "term": {
                    "dirs.keyword": string
                }

            }
        }
        results = self.es.search(index=index,
                                 body=body,
                                 size=1)
        self.logger.info( "dir results is {}".format(results))
        if len(results["hits"]["hits"]) > 0:
            result = results["hits"]["hits"][0]
            self.es.update(index=index,
                           doc_type="dir",
                           id = result["_id"],
                           body = {
                               "doc": {
                                   "num": result["_source"]["num"] + num
                               }
                           }
            )
            self.logger.info(result)
            cmd_id = result["_source"]["c_id"]
        else:
            largest_body = {
                "aggs" : {
                    "max_id" : {
                        "max" : {
                            "field" : "c_id"
                        }
                    }
                },
                "size":0
            }
            results = self.es.search(index=index,
                                     body=largest_body)


            cmd_id = int(results["aggregations"]["max_id"]["value"]) + 1
            self.logger.info( "insert dir")
            self.logger.info( cmd_id)
            body = {
                'c_id': cmd_id,
                "dirs": string,
                'num': num,
                'time': datetime.now()
            }
            a = self.es.index(index = index, body=body, doc_type="dir")
        self.logger.info("cmd_id {}".format(cmd_id))
        return cmd_id


    def file_update(self, string, dirs, num=1, ssh_client="", ssh_port=""):
        # 更新文件记录
        index = "sg_dev_files"
        body =  {
            "query": {
                "term": {
                    "file.keyword": string
                }
            }
        }
        results = self.es.search(index=index,
                                 body=body,
                                 size=1)
        # self.logger.info( results)
        if len(results["hits"]["hits"]) > 0:
            result = results["hits"]["hits"][0]
            self.es.update(index=index,
                           doc_type="dirs",
                           id = result["_id"],
                           body = {
                                 "doc": {
                                     "num": result["_source"]["num"] + num
                                 }
                           }
            )
            cmd_id = result["_source"]["c_id"]
        else:
            largest_body = {
                "aggs" : {
                    "max_id" : {
                        "max" : {
                            "field" : "c_id"
                        }
                    }
                },
                "size":0
            }
            results = self.es.search(index=index,
                                     body=largest_body)


            cmd_id = int(results["aggregations"]["max_id"]["value"]) + 1
            body = {
                'c_id': cmd_id,
                "file": string,
                'num': num,
                'time': datetime.now(),
                'dirs': dirs,
                'ssh_client': ssh_client,
                'ssh_port': ssh_port
            }
            a = self.es.index(index = index, body=body, doc_type="file")
        return cmd_id

        '''
        col = self.db["sg_dev_files"]
        query_condition = {"file": string}
        sort=[("_id", DESCENDING)]
        result = col.find_one(query_condition)
        result.update({"num": result["num"] + num,
                       "dirs": list(set(result["dirs"] + dirs))
        })
        if result:
            col.update(query_condition, result)
        else:
            file_id = col.find_one(sort=sort)["id"] + 1
            if types == "cmds":
                col.insert({
                    'id': file_id,
                    'num': num,
                    'file': string,
                    'time': datetime.now(),
                    'dirs': dirs,
                    'ssh_client': ssh_client,
                    'ssh_port': ssh_port
                })
        return file_id
        '''

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
        self.bulk_db_table('sg_dev_dirs', 'dirs', records_list)

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
        self.bulk_db_table('sg_dev_files', 'files', records_list)

    def bulk_db_table_by_list(self, content_dict_list):
        '''
        insert table by dict list
        '''
        self.bulk_db_table(self.index, self.types, content_dict_list)

    def filter_table(self, table_dic):
        for dic in table_dic:
            if "_id" in dic:
                dic.pop("_id")
            yield dic
    def drop_db(self, index_name):
        self.es.indices.delete(index_name)


    def update_from_mongo(self, types):
        '''
        update_from_mongo
        '''
        types2collection = {
            "cmds": "sg_dev_cmds",
            "dir": "sg_dev_dirs",
            "file": "sg_dev_files"
        }
        self.cmd_mongo_api = CmdMongo(None)
        cmd_info = self.cmd_mongo_api.get_cmd_info(types)
        self.types = types
        self.index = types2collection[types]
        if self.es.indices.exists(index=self.index):
            pass
        else:
            self.create_db(index_name=self.index)
        self.bulk_db_table_by_list(self.filter_table(cmd_info))




if __name__ == '__main__':
    import sys

    if sys.argv[1] in ["-h", "-help", "--h", "--help"]:
        print( "\n".join(["syn_cmd", "syn_dir", "syn_file"]))
        if len(sys.argv) == 3:
            help(getattr(ApiBase, sys.argv[2]))
    elif len(sys.argv) >= 2:
        es_api = ApiBase()
        if sys.argv[1] == "syn_cmd":
            es_api.syn_cmd()
        elif sys.argv[1] == "syn_dir":
            es_api.syn_dir()
        elif sys.argv[1] == "syn_file":
            es_api.syn_file()
        elif sys.argv[1] == "text_search":
            es_api.text_search(types=sys.argv[2], string=" ".join(sys.argv[3:]))
        elif sys.argv[1] == "cmd_update":
            string=" ".join(sys.argv[3:])
            es_api.cmd_update(string, dirs=[], pre_cmds=[], num=1, user="", ssh_client="", ssh_port="")
        elif sys.argv[1] == "update_from_mongo":
            es_api.update_from_mongo(types=sys.argv[2])
        elif sys.argv[1] == "drop_db":
            es_api.drop_db(index_name=sys.argv[2])



    '''
    es_api.bulk_dir(sys.argv[2])
    es_api.bulk_file(sys.argv[3])


    table = pd.read_table(sys.argv[1], header=None, na_values="")
    table = table.fillna("")
    table.columns = ["ensembl_gene_id","ensembl_transcript_id","external_gene_name","external_gene_source","external_transcript_name","external_transcript_source_name","ensembl_peptide_id","description","chromosome_name","start_position","end_position","strand","transcript_start","transcript_end","transcription_start_site","transcript_length","gene_biotype","transcript_biotype"]
    data_list = table.to_dict('records')
    es_api = ApiBase()
    es_api.bulk_db_table("test_db", "document", data_list)
    '''
