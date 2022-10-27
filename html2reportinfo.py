# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'

import os
import sys

html_file = sys.argv[1]
import lxml.html

html = lxml.html.parse(html_file)
root = html.getroot()
deposits = root.find_class('deposit')
id_ = 1000
for desposit in deposits:
    img_url = desposit.attrib["src"].split("?")[0]
    par = desposit.getparent()
    btn = par.find_class("btn btn-yellow table-show-report")[0]
    btn_url = btn.attrib["analysis-url"]
    btn_path = btn_url.split("?")[0]
    # btn_task_id = btn_url.split("?")[1]
    previous = desposit.getprevious()
    par = desposit.getparent()
    par_par = par.getparent()

    category = par_par.find("h4")
    if category is not None:
        pass
    else:
        category = par_par.find("h5")
    try:
        print("\t".join([
            str(id_),
            category.text,
            previous.text,
            btn_path,
            img_url
        ]))
    except:
        print img_url
    id_ += 1
