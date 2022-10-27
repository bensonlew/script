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


class MongoGenomeStat(object):
    def __init__(self):
        super(MongoGenomeStat, self).__init__()
        self.genome_list = []
        self.path_list = []
        self.sanger_ip = "10.11.1.102"
        #self._db_name = Config().MONGODB + '_ref_rna'

    def get_genome_list(self):
        db_version = 1
        self.db = Config().get_mongo_client(mtype="ref_rna_v2", db_version=db_version)[Config().get_mongo_dbname("ref_rna_v2", db_version=db_version)]
        coll = self.db["sg_genome_db"]
        for genome_dict in coll.find():
            genome_dict["_id"] = str(genome_dict["_id"])
            self.genome_list.append(genome_dict)
            self.path_list.append(genome_dict["dna_fa"].split("/dna")[0])

    def get_old_genome_list(self, dir):
        self.old_list = list()
        old_json =  os.path.join(dir,"annot_species.json")
        with open(old_json, "r") as f:
            old_genome_json = json.load(f)
            for k,v in old_genome_json.items():
                path = v["dna_fa"].split("/dna")[0]
                self.old_list.append(path)

    def walk(self, dir):
        print self.old_list
        print self.path_list
        for dira in ['vertebrates', 'plants', 'fungi', 'protists', 'metazoa']:
            for dirb in os.listdir(os.path.join(dir, dira)):
                dirb_path = os.path.join(dir, dira, dirb)
                if os.path.isdir(dirb_path):
                    for dirc in os.listdir(dirb_path):
                        dirc_path = os.path.join(dir, dira, dirb, dirc)
                        relpath = os.path.join(dira, dirb, dirc)
                        time = os.path.getmtime(dirc_path)
                        t = str(datetime.datetime.fromtimestamp(time))
                        if relpath in self.old_list:
                            in_old = "true"
                        else:
                            in_old = "false"

                        if relpath in self.path_list:
                            in_mongo = "true"
                        else:
                            in_mongo = "false"
                        print "\t".join([relpath, t, in_old, in_mongo])

                        




    def get_task_info(self, project_type, db_version=1):
        self.db_version = db_version
        self.db = Config().get_mongo_client(mtype=project_type, db_version=db_version)[Config().get_mongo_dbname(project_type, db_version=db_version)]
        task_list = []
        coll = self.db["sg_task"]
        if project_type == "whole_transcriptome":
            coll = self.db["task"]
        for task in coll.find():
            task["_id"] = str(task["_id"])
            if project_type == "whole_transcriptome":
                if "long_task" in task:
                    task["long_task"]["_id"] = str(task["long_task"]["_id"])
                if "small_task" in task:
                    task["small_task"]["_id"] = str(task["small_task"]["_id"])
                if "circle_task" in task:
                    task["circle_task"]["_id"] = str(task["long_task"]["_id"])
                if "whole_task" in task:
                    task["whole_task"]["_id"] = str(task["small_task"]["_id"])
            task_list.append(task)
            

        return task_list


    def stat(self):
        self.get_genome_list()
        time_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        refrna_task_0 = self.get_task_info("ref_rna_v2", db_version=0)
        refrna_task_1 = self.get_task_info("ref_rna_v2", db_version=1)
        smallrna_task_0 = self.get_task_info("small_rna", db_version=0)
        smallrna_task_1 = self.get_task_info("small_rna", db_version=1)
        lncrna_task_0 = self.get_task_info("lnc_rna", db_version=0)
        lncrna_task_1 = self.get_task_info("lnc_rna", db_version=1)
        medical_task_0 = self.get_task_info("medical_transcriptome", db_version=0)
        medical_task_1 = self.get_task_info("medical_transcriptome", db_version=1)
        whole_task_0 = self.get_task_info("whole_transcriptome", db_version=0)
        whole_task_1 = self.get_task_info("whole_transcriptome", db_version=1)

        for genome_dict in self.genome_list:
            genome_id = genome_dict["genome_id"]
            refrna_list = [task for task in refrna_task_0 if task.get("genome_id", "unknown") == genome_id and task.get("is_demo", 0) == 0]  + \
                          [task for task in refrna_task_1 if task.get("genome_id", "unknown") == genome_id and task.get("is_demo", 0) == 0]

            lncrna_list = [task for task in lncrna_task_0 if task.get("genome_id", "unknown") == genome_id and task.get("is_demo", 0) == 0]  + \
                          [task for task in lncrna_task_1 if task.get("genome_id", "unknown") == genome_id and task.get("is_demo", 0) == 0]

            smallrna_list = [task for task in smallrna_task_0 if task.get("genome_id", "unknown") == genome_id and task.get("is_demo", 0) == 0]  + \
                          [task for task in smallrna_task_1 if task.get("genome_id", "unknown") == genome_id and task.get("is_demo", 0) == 0]

            whole_list = [task for task in whole_task_0 if task.get("genome_id", "unknown") == genome_id and task.get("is_demo", 0) == 0]  + \
                          [task for task in whole_task_1 if task.get("genome_id", "unknown") == genome_id and task.get("is_demo", 0) == 0]

            medical_list = [task for task in medical_task_0 if task.get("genome_id", "unknown") == genome_id and task.get("is_demo", 0) == 0]  + \
                          [task for task in medical_task_1 if task.get("genome_id", "unknown") == genome_id and task.get("is_demo", 0) == 0]

            genome_dict.update({
                "ref_rna_task": refrna_list,
                "lncrna_task": lncrna_list,
                "smallrna_task": smallrna_list,
                "wholetrans_task":  whole_list,
                "medical_task": medical_list
            })

        with open("genome_task_{}.json".format(time_str), "w") as dump_f:
            dump_f.write(str(self.genome_list))
            #json.dump(self.genome_list, dump_f, indent=4)

        stat_f = open("genome_task_{}.stat.xls".format(time_str), "w")
        stat_f.write("\t".join([
            "genome_id",
            "common_name",
            "name",
            "release",
            "created_ts",
            "status",
            "ensemble_class",
            "recommend",
            "secret",
            "ref_rna_num",
            "ref_rna_task",
            "lncrna_num",
            "lncrna_task",
            "smallrna_num",
            "smallrna_task",
            "wholetrans_num",
            "wholetrans_task",
            "medical_num",
            "medical_task",
            "all_num"

        ]) + "\n")
        for genome_dict in self.genome_list:
            stat_f.write("\t".join([
               genome_dict["genome_id"],
               genome_dict.get("common_name", ""),
               genome_dict["name"],
               genome_dict.get("ensemble_release", ""),
               genome_dict.get("created_ts", ""),
               genome_dict.get("status", "true"),
               genome_dict.get("ensemble_class", ""),
               genome_dict.get("recommend", ""),
               genome_dict.get("secret", ""),
               str(len(genome_dict["ref_rna_task"])),
               ";".join([task["task_id"] for task in genome_dict["ref_rna_task"]]),
               str(len(genome_dict["lncrna_task"])),
               ";".join([task["task_id"] for task in genome_dict["lncrna_task"]]),
               str(len(genome_dict["smallrna_task"])),
               ";".join([task["task_id"] for task in genome_dict["smallrna_task"]]),
               str(len(genome_dict["wholetrans_task"])),
               ";".join([task["task_id"] for task in genome_dict["wholetrans_task"]]),
               str(len(genome_dict["medical_task"])),
               ";".join([task["task_id"] for task in genome_dict["medical_task"]]),
               str(len(genome_dict["ref_rna_task"]) + len(genome_dict["lncrna_task"]) + len(genome_dict["smallrna_task"]) + len(genome_dict["wholetrans_task"]) + len(genome_dict["medical_task"]))

            ]
            )+ "\n")





if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='for update by table\n ')
    parser.add_argument('-d', type=str, default=None, help="project type.")


    args = parser.parse_args()
    os.environ["current_mode"]="workflow"
    os.environ["NTM_PORT"]="7322"
    os.environ["WFM_PORT"]="7321"

    api = MongoGenomeStat()
    



    if args.d:
        api.get_genome_list()
        api.get_old_genome_list(args.d)
        api.walk(args.d)
    else:
        api.stat()

