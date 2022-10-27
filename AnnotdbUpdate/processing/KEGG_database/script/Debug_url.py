#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/9/1 9:44
# @Author  : U make me wanna surrender my soul
import requests
import pandas as pd
from requests.adapters import HTTPAdapter
import http.client

# 解决requests.exceptions.ChunkedEncodingError
http.client.HTTPConnection._http_vsn = 10
http.client.HTTPConnection._http_vsn_str = 'HTTP/1.0'

tunnel = "tps134.kdlapi.com:15818"
# 用户名密码方式
username = "t12874651469012"
password = "eybijvuz"
proxies = {
    "http": "http://%(user)s:%(pwd)s@%(proxy)s/" % {"user": username, "pwd": password, "proxy": tunnel},
    "https": "http://%(user)s:%(pwd)s@%(proxy)s/" % {"user": username, "pwd": password, "proxy": tunnel}
}


def get_data(url):
    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=3))
    s.mount('https://', HTTPAdapter(max_retries=3))
    database = 'E:\\KEGG_Database\\Eukaryotes'
    try:
        res = s.get(url, proxies=proxies, timeout=60)
        if res.status_code == 200:
            res_url = res.url
            orgname = res_url.split('/')[-1].split(':')[0]
            orgid = res_url.split('/')[-1].split(':')[-1]
            print(orgname, ':', orgid)
            with open(database + '\\' + orgname + '\\' + orgid, 'w') as f:
                f.write(res.text)
        else:
            with open('response_error.txt', 'a+') as f:
                print(url, file=f)
    except TimeoutError:
        with open('TimeoutError.txt', 'a+') as f:
            print(url, file=f)


df = pd.read_csv('Deal_Error.txt', sep='\t')
gene_id = df['ID'].tolist()
for i in gene_id:
    get_data(i)
