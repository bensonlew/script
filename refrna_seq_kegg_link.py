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
from bson.objectid import ObjectId

class RefUpdate(object):
    def __init__(self, project_type, bind_object=None):
        super(RefUpdate, self).__init__()
        self.db = Config().get_mongo_client(mtype=project_type, db_version=1)[Config().get_mongo_dbname(project_type, db_version=1)]
        self._project_type = project_type
        self.map_dict = dict()

    def find_records(self, collection_name, query_dict):
        conn = self.db[collection_name]
        results = conn.find(query_dict)
        print conn
        return results
    

    def update_record_by_dict(self, collection_name, query_dict, insert_dict):
        conn = self.db[collection_name]
        print collection_name
        print query_dict
        print insert_dict
        conn.update(query_dict, {"$set": insert_dict}, upsert=True)

    def find_record(self, collection_name, query_dict):
        conn = self.db[collection_name]
        result = conn.find_one(query_dict)
        return result

    def find_records(self, collection_name, query_dict):
        conn = self.db[collection_name]
        results = conn.find(query_dict)
        print conn
        return results

    def update(self, task_id):
        self.get_background_info(task_id)
        self.replace_links(task_id)

    def get_task(self, query_dict):
        records = self.find_records("sg_geneset_kegg_enrich", query_dict)
        task_id = [record['task_id'] for record in records]
        return list(set(task_id))

    def get_path_ko(self, main_id):
        self.gene2ko = dict()
        kegg_kos = self.find_records("sg_annotation_kegg_table", {"kegg_id": main_id})
        for kegg_ko in kegg_kos:
            self.gene2ko[kegg_ko["transcript_id"]] = kegg_ko["ko_id"]

    def get_background_info(self, task_id):
        kegg= self.find_record("sg_annotation_kegg", {"task_id": task_id})
        if not kegg:
            print "task wrong {}".format(task_id)
        records = self.find_records("sg_annotation_kegg_level", {"kegg_id": kegg["main_id"]})

        self.get_path_ko(kegg["main_id"])
        for record in records:
            pathway = record["pathway_id"]
            links = record["hyperlink"].split("?")[1].split("/")
            links.pop(0)  # 去除掉map
            dict = {}
            for link in links:
                ko = link.split("%09")[0]  # K06101
                color = link.split("%09")[1]  # tomato
                dict[ko] = color
            self.map_dict[pathway] = dict  # self.map_dict["map05340"] = {"K10887": "yellow"}

    def get_geneset_detail(self, main_id):
        geneset_detail = self.find_record("sg_geneset_detail", {"geneset_id": main_id})
        geneset_ko = defaultdict(set)
        regulate_gene = defaultdict(set)
        geneset_ko["up"] = list()
        geneset_ko["down"] = list()
        dic = zip(geneset_detail["seq_list"], geneset_detail["regulate_list"])
        regulate_gene["up"] = [k for k, v in dic if v == "up"]
        regulate_gene["down"] = [k for k, v in dic if v == "down"]
        for gene in regulate_gene["up"]:
            if gene in self.gene2ko:
                geneset_ko["up"].extend(self.gene2ko[gene].split(";"))

        for gene in regulate_gene["down"]:
            if gene in self.gene2ko:
                geneset_ko["down"].extend(self.gene2ko[gene].split(";"))
        self.category = geneset_ko

    def replace_links(self, task_id):
        enrich_records = self.find_records("sg_geneset_kegg_enrich", {"task_id": task_id})
        for enrich_record in enrich_records:
            if enrich_record["params"] == "":
                continue
            params = json.loads(enrich_record["params"])
            gene_set = self.find_record("sg_geneset", {"main_id": ObjectId(params["geneset_id"])})
            
            if gene_set.get("source", "") == "diff_exp" and enrich_record["status"] == "end":
                self.get_geneset_detail(gene_set["main_id"])
                print task_id, enrich_record["main_id"]
                self.replace_link(enrich_record["main_id"])


    def replace_link(self, main_id):
        enrich_details = self.find_records("sg_geneset_kegg_enrich_detail", {"kegg_enrich_id": main_id})
        for record in enrich_details:
            links = record["hyperlink"]
            if "multi_query" in links:
                print main_id, "结果正确"
                break
            pathway = record["id"]
            links_ko = links.split("?")[1].split("/")
            links_ko.pop(0)  # 去除掉map
            lnk = links.split("?")[0] + "?map=" + pathway + "&multi_query="
            ko_tmp = [x.split("%09")[0] for x in links_ko]
            ko_link_all = []
            ko_link_bg = []
            if pathway in self.map_dict:  # 含有背景色
                for ko in self.map_dict[pathway].keys():
                    if ko == "":
                        continue
                    if ko in ko_tmp:  # 基因ko显著富集
                        if self.get_color(ko):
                            ko_link_all.append(ko + "+{},{}%0d%0a".format(self.map_dict[pathway][ko], self.get_color(ko)))

                        else:
                            ko_link_bg.append(ko + "+{}%0d".format(self.map_dict[pathway][ko]))
                    else:
                        ko_link_bg.append(ko + "+{}%0d".format(self.map_dict[pathway][ko]))

            else:
                for ko in ko_tmp:
                    if ko == "":
                        continue
                    if self.get_color(ko):
                        ko_link_bg.append(ko + "+{},{}%0d%0a".format("white", self.get_color(ko)))

                    else:
                        pass
            link_new = lnk + "".join(ko_link_all) + "".join(ko_link_bg)
            # print links, link_new
            self.update_record_by_dict("sg_geneset_kegg_enrich_detail", {"_id": record["_id"], "kegg_enrich_id": record["kegg_enrich_id"]}, {"hyperlink": link_new, "err_link": links})

    def get_color(self, ko):
        """
        根据基因的ko号，获取颜色
        :param ko: 基因的ko号
        :return:
        """
        if len(self.category) == 1:
            if ko in self.category[self.category.keys()[0]]:
                return "red"
                # return "blue"
            else:
                return False
        elif len(self.category) == 2:
            # if self.option('source') == 'diff_exp':
            # lst = list(self.category.keys())  # 基因集列表
            lst = ["up", "down"]
            # lst.sort()
            if ko in self.category[lst[0]] and ko in self.category[lst[1]]:
                return "pink"
            elif ko in self.category[lst[0]]:
                return "red"
            elif ko in self.category[lst[1]]:
                return "blue"
            else:
                return False

if __name__ == '__main__':
    logging.info('Usage: python add_batch.py <project_type>')
    
    project_type = sys.argv[1]
    if len(sys.argv) == 2:
        ref = RefUpdate(project_type=project_type)
        print "\n".join(ref.get_task({"created_ts": {"$gte": "2021-02-26"}}))
    else:
        task_id = sys.argv[2]
        ref = RefUpdate(project_type=project_type)
        ref.update(task_id=task_id)
    
