# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'

import pickle
from biocluster.core.function import load_class_by_path
import sys
import os
import sys

if len(sys.argv) < 3:
	print "python ~/sg-users/liubinxu/script/script/delete_list.py Sfur.gtf ../dna/n.list 'lambda x:x.split(\"\\t\")[8].split(\"\\\"\")[1]'"
	raise Exception

'''
print sys.argv[1]
print sys.argv[2]
print sys.argv[3]
'''
f=lambda x:x.split("\t")[0]
if len(sys.argv) > 3:
    f=eval(sys.argv[3])

with open(sys.argv[2], 'r') as list_f:
    delete_list = [line.strip("\n") for line in list_f.readlines()]

with open(sys.argv[1], 'r') as table_f:
    for line in table_f.readlines():
        line = line.strip("\n")
        if f(line) in delete_list:
            pass
        else:
            print line


