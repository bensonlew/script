#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@time    : 2022/12/26
@file    : 前端的html数据库修改为json
"""
pipeline_id = 239

import mysql.connector
import json
import sys

pipeline_id = sys.argv[1]
def get_one_table(pipeline_id,  table_name, cursor):
    '''
    获取一个表格数据
    '''
    schema = "DESCRIBE {}".format(table_name)
    cursor.execute(schema)
    schs = list()
    for q in cursor:
        schs.append(q)

    headers = [sch[0] for sch in schs]
    query = ("SELECT * FROM {} WHERE pipeline_id={}".format(table_name, pipeline_id))
    rows = list()
    cursor.execute(query)
    for q in cursor:
        q_clean = []
        for x in q:
            if type(x) in [int, str]:
                q_clean.append(x)
            else:
                q_clean.append(str(x))
        row_dict = dict(zip(headers, q_clean))
        rows.append(row_dict)

    data = {
        "table": table_name,
        "rows": rows
    }
    # print(data)
    with open(table_name + "_{}".format(pipeline_id) + ".json", 'w') as f:
        f.write(json.dumps(data, indent=4, ensure_ascii=False))


cnx = mysql.connector.connect(user='lab_ro', password='GY4bgC8wP+yVeult',
                              host='10.9.0.10',
                              database='lab_sanger',
                              port= '3306',
                              ssl_disabled= True
                              )

cursor = cnx.cursor()
get_one_table(pipeline_id, "sg_report_category", cursor)
get_one_table(pipeline_id, "sg_report_image", cursor)
get_one_table(pipeline_id, "sg_report_result_table", cursor)
cnx.close()
