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

def convert(file1, file2):
    with open(file1, 'r') as json1:
        data1 = json.load(json1)


    # 修改字体
    try:
        data1["chart"]["textStyle"]["fontFamily"] = "Arial"
    except KeyError:
        print('data1["chart"]["textStyle"]["fontFamily"]')

    if "legend" in data1:
        for sub in data1["legend"]:
            try:
                sub["textStyle"]["fontFamily"] = "Arial"
            except:
                print("ignore key err")
    

    with open(file2, 'w') as json2:
        json2.write(json.dumps(data1, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    file1 = sys.argv[1]
    file2 = sys.argv[2]
    convert(file1, file2)

