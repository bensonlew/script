# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'
import os
import re
from bson.son import SON
from bson.objectid import ObjectId
import json
import unittest
import argparse
import sys
import pandas as pd
from datetime import datetime
from collections import OrderedDict


cmd_dir = sys.argv[1]
cmd_id = int(sys.argv[2])
dir_id = int(sys.argv[3])
file_id = int(sys.argv[4])

files = os.listdir(cmd_dir)
cmd_dict = OrderedDict()
file_dict = OrderedDict()
dir_dict = OrderedDict()

last_dir = ""
last_cmd = ""

for cmd_path in files:
    if cmd_path.startswith(".") or cmd_path.endswith("stat.xls"):
        continue
    else:
        with open(cmd_path, 'r') as cmd_file:
            for line in cmd_file:
                l = line.strip().rstrip("}").strip()
                cols = l.split(":")
                try:
                    time = datetime.strptime(":".join(cols[0:3]), '%Y-%m-%d %H:%M:%S')
                except:
                    print l
                    continue
                user_name = cols[3]
                dir_path = cols[4]
                cmds = ":".join(cols[5:])

                if cmds == last_cmd and dir_path == last_dir:
                    # 重复记录过滤
                    continue

                ## 所有到过的路径都会被记录下

                if dir_path in dir_dict:
                    if dir_dict[dir_path]['time'] < time:
                        dir_dict[dir_path]['time'] = time
                    dir_dict[dir_path]['num'] += 1
                else:
                    dir_id += 1
                    dir_dict[dir_path] = {
                        'id': dir_id,
                        'time': time,
                        'user': user_name,
                        'num': 1
                    }

                # dir_id = dir_dict[dir_path]['id']


                ## 判断查看编辑过的文件

                if len(cmds.split()) >= 32 or len(cmds.split()) < 1:
                    # print cmds
                    continue

                if cmds.split()[0] in ['less', 'cat', 'zcat', 'nano', 'vi', 'vim', 'emacs', 'grep', 'head', 'tail']:
                    for f in cmds.split()[1:]:
                        # 不考虑当前目录下的文件， 和非文件
                        if f[0] == "~" or "/" in f:
                            if f in file_dict:
                                if file_dict[f]['time'] < time:
                                    file_dict[f]['time'] = time
                                    file_dict[f]['num'] += 1
                                    file_dict[f]['dirs'].add(dir_id)
                            else:
                                file_id += 1
                                file_dict[f] = {
                                    'id': file_id,
                                    'time': time,
                                    'num': 1,
                                    'user': user_name,
                                    'dirs': set([dir_id])
                                }

                if cmds.split()[0] not in ['cd', 'which', 'less', 'cat', 'zcat', 'nano', 'vi', 'vim', 'emacs', 'grep', 'pwd', "ls", 'll', 'mkdir', 'rm', 'head', 'tail', '#'] or "|" in cmds:
                    if cmds.startswith("#"):
                        pass
                    else:
                        if cmds in cmd_dict:
                            cmd_dict[cmds]['time'] = time
                            cmd_dict[cmds]['num'] += 1
                            cmd_dict[cmds]['dirs'].add(dir_id)

                            if dir_path == last_dir and cmd_id != 0:
                                cmd_dict[cmds]['pre_cmds'].add(cmd_id)
                        else:
                            last_cmd = cmd_id
                            cmd_id += 1
                            cmd_dict[cmds] = {
                                'id': cmd_id,
                                'time': time,
                                'num': 1,
                                'user': user_name,
                                'dirs': set([dir_id]),
                                'pre_cmds': set()
                            }
                            if dir_path == last_dir:
                                cmd_dict[cmds]['pre_cmds'].add(last_cmd)
                last_dir = dir_path
                last_cmd = cmd_path



with open('dir_stat.xls', 'w') as fo:
    for d,dir_rec in dir_dict.items():
        fo.write(d + "\t" + "\t".join([str(dir_rec[x]) for x in ['id', 'time', 'num', 'user']])  + "\n" )

with open('file_stat.xls', 'w') as fo:
    for f,file_rec in file_dict.items():
        file_rec['dirs'] = list(file_rec['dirs'])
        fo.write(f + "\t" + "\t".join([str(file_rec[x]) for x in ['id', 'time', 'num', 'dirs', 'user']])  + "\n")

with open('cmd_stat.xls', 'w') as fo:
    for c,cmd_rec in cmd_dict.items():
        cmd_rec['dirs'] = list(cmd_rec['dirs'])
        cmd_rec['pre_cmds'] = list(cmd_rec['pre_cmds'])
        fo.write(c + "\t" + "\t".join([str(cmd_rec[x]) for x in ['id', 'time', 'num', 'dirs', 'user', 'pre_cmds']])  + "\n")
