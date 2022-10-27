#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'

import pickle
from biocluster.core.function import load_class_by_path
import sys
import os

def load_by_class(class_pk, pk):
    a=open(class_pk, 'rb')
    old_env = os.environ.copy()
    tool_pk = pickle.load(a)
    tool_path = tool_pk['tool']
    tool_path = tool_path.split("mbio.tools.")[1]
    tool = load_class_by_path(tool_path, tp='Tool')
    with open(pk, "rb") as pk_file:
	pk_config = pickle.load(pk_file)
	pk_config.DEBUG = True
	tool_obj = tool(pk_config)
    	env = os.environ
        for key,value in env.items():
            if old_env.has_key(key):
                # print key + "\t" + value + "\t" + old_env[key]
                if old_env[key] == value:
                    pass
                else:
                    print key + "=" + value.split(old_env[key])[0] + "$" + key
            else:
                print key + "=" + env[key]

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "python ~/sg-users/liubinxu/script/tool_env.py tool_class.pk tool.pk"
    else:
        load_by_class(sys.argv[1], sys.argv[2])
