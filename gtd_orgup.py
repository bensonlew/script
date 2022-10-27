#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'
# coding=utf-8

import os
import datetime
import sys

sdin_str = sys.stdin.read()
awork = dict()
work_list = list()

print sdin_str
for line in sdin_str.split("\n"):
    if line.startswith("+*"):
        print line
        eles = line.split(" ")
        print eles[1]
        if eles[0].startswith("+") and eles[1] in ['TODO']:
            awork = {
                "status": eles[1],
                "task_name": " ".join(eles[2:])
            }
            work_list.append(awork)
        if eles[0].startswith("+") and  eles[1] in ['DONE']:
            awork = {
                "status": eles[1],
                "task_name": " ".join(eles[2:])
            }
            work_list.append(awork)
        if line.startswith("+   SCHEDULED"):
            date = line.split("<")[1].split(" ")[0]
            awork.update({
                "date": date
            })
        if line.startswith("+   CLOSED"):
            date = line.split("[")[1].split(" ")[0]
            awork.update({
                "date": date
            })

time_now = datetime.datetime.now()
today_str = time_now.strftime("%Y-%m-%d")
print work_list
for work in work_list:
    if work.get("status", "") == "TODO":
        print work.get("task_name", "") + " 未完成, 待处理"
    if work.get("status", "") == "DONE":
        print "完成" + work.get("task_name", "")
