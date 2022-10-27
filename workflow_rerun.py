#!/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'guoquan'

import argparse
from biocluster.wpm.db import WorkflowModel
from biocluster.wsheet import Sheet
from biocluster.wpm.client import worker_client
import json
import re
import traceback
import os
import datetime
import time


parser = argparse.ArgumentParser(description="select a already run workflow and rerun it!")
parser.add_argument("-a", "--skip_all_success", action="store_true", help="to skik all the succeed tools, "
                                                                          "only for the tool start run after 2018.3.21")
parser.add_argument("-s", "--skip_steps", type=str, help="the step name used in the workflow you want to skip,"
                                                         " split by \",\"")
parser.add_argument("-t", "--tool_ids", type=str, help="the run id of tools in the workflow you want to skip, "
                                                       "split by \",\", or a file path of the tool id list, "
                                                       "one id per line.")
parser.add_argument("-u", "--UPDATE_STATUS_API", type=str, help="the UPDATE_STATUS_API api module path. "
                                                                "if use false or no, "
                                                                "don't update the states, "
                                                                "default use the original config")
parser.add_argument("-n", "--IMPORT_REPORT_DATA", type=str, choices=["yes", "no"],
                    help="whether run the import date functions with the '@report_check' decorate, default use the "
                         "original config")
parser.add_argument("-ne", "--IMPORT_REPORT_AFTER_END", type=str, choices=["yes", "no"],
                    help="whether run the import date functions with the '@report_check' decorate at the end of "
                         "workflow, default use the original config")

parser.add_argument("-wd", help="work dir")
parser.add_argument("-j", help="json file")
args = parser.parse_args()


def wait_end(model):
    data = model.find()
    if data["is_end"] == 0:
        time.sleep(5)
        wait_end(model)
    else:
        print "Workflow %s 结束已经运行，准备开始重运行..." % model.workflow_id


def main():
    if args.j:
        json_f = args.j
    elif os.path.exists("data.json"):
        json_f = "data.json"
    elif os.path.exists(os.path.join(args.wd, "data.json")):
        json_f = os.path.join(args.wd, "data.json")
    else:
	raise Exception("无法找到json文件")
    # wsheet = Sheet(data={"id": wid})
    # model = WorkflowModel(wsheet)
    # data = model.find()
    if 1:
        '''
        if data["has_run"] == 0:
            raise Exception("Workflow ID %s 尚未开始运行，不能重新运行!" % wid)
        if data["is_end"] == 0:
            print "Workflow %s 正在运行，开始发送结束运行指令..." % wid
            model.stop()
            print "请耐心等待Workflow %s 结束运行..." % wid
            wait_end(model)
        '''
        with open(json_f, "r") as jf:
            json_data = json.load(jf)

        json_data["rerun"] = True
        json_data["run_time"] = datetime.datetime.now()
	json_data["member_type"] = 1
        json_data["to_file"] = []
        if args.wd:
            json_data["work_dir"] = os.path.abspath(args.wd)
        else:
            json_data["work_dir"] = os.path.abspath("./")
        if args.skip_all_success:
            json_data["skip_all_success"] = True
        if args.UPDATE_STATUS_API:
            if args.UPDATE_STATUS_API in ["false", "False","FALSE","no","No","NO"]:
                json_data["UPDATE_STATUS_API"] = False
            else:
                json_data["UPDATE_STATUS_API"] = args.UPDATE_STATUS_API
        if args.IMPORT_REPORT_DATA:
            if args.IMPORT_REPORT_DATA == "yes":
                json_data["IMPORT_REPORT_DATA"] = True
            else:
                json_data["IMPORT_REPORT_DATA"] = False
        if args.IMPORT_REPORT_AFTER_END:
            if args.IMPORT_REPORT_AFTER_END == "yes":
                json_data["IMPORT_REPORT_AFTER_END"] = True
            else:
                json_data["IMPORT_REPORT_AFTER_END"] = False

        if args.skip_steps:
            steps = re.split(r"\s*,\s*", args.skip_steps)
            json_data["skip_steps"] = steps
            print "Skiping steps %s ..." % steps
        if args.tool_ids:
            if os.path.isfile(args.tool_ids):
                with open(args.tool_ids) as f:
                    lines = f.readlines()
                tool_ids = [l.strip() for l in lines]
            else:
                tool_ids = re.split(r"\s*,\s*", args.tool_ids)
            json_data["skip_tools"] = tool_ids
            print "Skiping tools %s ..." % tool_ids
        # print "Connectiong to the WPM Server, try to rerun workflow %s ...." % wid
        try:
            worker = worker_client()
            info = worker.add_task(json_data)
            if "success" in info.keys() and info["success"]:
                print "投递成功，请关注WPM进度日志!"
            else:
                print "任务投递失败: %s" % info["info"]
        except Exception, e:
            exstr = traceback.format_exc()
            print "ERROR:", exstr
            raise Exception("WPM连接失败：%s, %s" % (str(e), str(exstr)))
    else:
        pass
        # raise Exception("Workflow ID %s 不存在，请确认后再次运行!" % wid)

if __name__ == '__main__':
    main()
