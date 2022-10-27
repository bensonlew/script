# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'

import pickle
from biocluster.core.function import load_class_by_path
import sys
import os
import sys
import json
from libs.upload_task import UploadTask
from get_file_list import get_list
from biocluster.api.file.remote import RemoteFileManager

if len(sys.argv) < 2:
	print "python ~/sg-users/liubinxu/script/script/delete_list.py Sfur.gtf ../dna/n.list 'lambda x:x.split(\"\\t\")[8].split(\"\\\"\")[1]'"
	raise Exception

json_file = "data.json"
a= open("data.json")
b = json.load(a)

target = b["output"]
from_file = sys.argv[1]
identity_code = sys.argv[2]


from_dir = os.path.realpath(from_file)
to_file = "/".join(from_file.split("/")[1:])
target_dir = os.path.join(target, to_file)


'''
工作流上传方式， 可以成功，但无法刷新页面信息
remote_file = RemoteFileManager(target_dir)

if remote_file.type != "local":
    print "from {} to {}".format(from_dir, target_dir)
    print "remote_file type {}".format(remote_file.type)
    print "remote_file type {}".format(remote_file.type)
    remote_file.upload(from_dir)
'''
if target.startswith("s3nb"):
    mode = nsanger
else:
    mode = tsg
stream_on = False
project_type = b["name"]

task = UploadTask(from_dir, os.path.abspath("file_list"), identity_code, mode, stream_on, project_type)

post_file = "post_result_data.json"
post_dict = get_post_file(post_file)
rel_path_list = get_rel_path(from_file)
rel2rel_dir = from_file

task._file_info = get_file_info(post_dict, rel_path_list)
task.post_filesdata()


def get_rel_path(from_file):
    from_list = list()
    for d1,d2,fs in os.walk("upload_results/Express"):
        for f in fs:
            from_list.append(d1 + "/" + f)
    return from_list

def get_file_info(post_dict, rel_path_list, rel2rel_dir):
    file_list = list()
    uploaded_list  = post_dict["data"]['sync_task_log']["files"]
    uploaded_dict = dict()
    for uploaded in uploaded_list:
        uploaded_dict[uploaded['path']]  =  uploaded
    for rel_path in rel_path_list:
        if rel_path in uploaded_dict:
            file_dict = {
		    "path" : "",
		    "size" : os.path.getsize(os.path.join("upload_results", rel_path)),
		    "rel_path" : rel_path.split(rel2rel_dir)[1],
		    "description": uploaded_dict[rel_path]["description"],
		    "format": uploaded_dict[rel_path]["format"], 
		    "code": uploaded_dict[rel_path]["code"],
		    "lock": "0",
 		    }
        else:
            file_dict = {
		    "path" : "",
		    "size" : os.path.getsize(os.path.join("upload_results", rel_path)),
		    "rel_path" : rel_path.split(rel2rel_dir)[1],
		    "description": "",
		    "format": "", 
		    "code": "",
		    "lock": "0",
 		    }
        file_list.append(file_dict)
    return file_list
    


def get_post_file(file_path):
    post_file = open(file_path, "r")
    post_dict = json.load(post_file)
    post_file.close()
    return post_dict
