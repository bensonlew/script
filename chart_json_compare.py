#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@time    : 2023/1/10
@file    : chart json 前后结果比较
"""


import re
import json
import os
import sys
from collections import OrderedDict

def compare(file1, file2):
    with open(file1, 'r') as json1:
        data1 = json.load(json1)

    with open(file2, 'r') as json2:
        data2 = json.load(json2)

    for key, value in data1.items():
        pres = key
        if key == "dataset":
            pass
        else:
            if key in data2:
                compare_one(pres, data1[key], data2[key])
            else:
                print("{} lacks key".format(key))

def compare_one(pres, data1, data2):
    if type(data1) != type(data2):
        print("pres type error {}".format(pres))
    elif type(data1) == dict:
        for key, value in data1.items():
            pres += "." + key
            if key not in data2:
                print("{} lack in old".format(pres))
            else:
                compare_one(pres, data1[key], data2[key])
    elif type(data1) == list:
        for k, value in enumerate(data1):
            pres += "." + str(k)
            if k in data2:
                compare_one(pres, data1[k], data2[k])
            else:
                print("{} lacks key".format(pres))
    else:
        if data1 != data2:
            print("{}  not equal {} {}".format(pres, data1, data2))

if __name__ == '__main__':
    file1 = sys.argv[1]
    file2 = sys.argv[2]
    compare(file1, file2)

