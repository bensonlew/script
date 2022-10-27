# -*- coding: utf-8 -*-

import os
import json
import logging
import re
import sys

import regex

from biocluster.api.file.remote import RemoteFileManager
from biocluster.api.file.lib.transfer import TransferManager
import glob


def upload_to_s3(from_file, to_path, cover=True):
    if not re.match(r"^\w+://\S+/.+$", to_path):
        raise Exception("上传路径%s格式不正确!" % to_path)
    if os.path.basename(to_path) == ".":
        raise Exception("目标文件不能叫\".\"!")

    target_dir = False
    if to_path.endswith("/"):
       target_dir = True

    s3transfer = TransferManager()
    s3transfer.base_path = os.getcwd()
    s3transfer.overwrite = cover
    source = os.path.join(os.getcwd(), from_file)
    for f in glob.glob(os.path.join(source)):
        if target_dir:
            target = os.path.join(to_path, os.path.basename(f))
            print target
        else:
            target = to_path
        if os.path.isdir(f):
            for root, dirs, files in os.walk(f):
                rel_path = os.path.relpath(root, f)
                for i_file in files:
                    if rel_path == ".":
                        key_path = os.path.join(target, i_file)
                    else:
                        key_path = os.path.join(target, rel_path, i_file)
                    i_file_path = os.path.join(root, i_file)
                    s3transfer.add(i_file_path, key_path)
        else:
            print "{}to{}".format(f, target)
            s3transfer.add(f, target)
    s3transfer.wait()


if __name__ == '__main__':
    from_path = sys.argv[1]
    to_path = sys.argv[2]
    if to_path.startswith("http"):
        ## 仅测试机对象存储使用
        d1 = to_path.split("//")[1]
        d2 = d1.split("/")[1:]
        head = d1.split("/")[0].split(".")
        to_path = head[1] + "://" + head[0] + "/" + "/".join(d2)
        print to_path
    upload_to_s3(from_path, to_path)
    

