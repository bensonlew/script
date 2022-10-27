#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/7/22 14:44
# @Author  : U make me wanna surrender my soul
from urllib import request
import json

# 要访问的目标页面
targetUrl = "https://www.baidu.com"

# 代理服务器
proxyHost = "dyn.horocn.com"
proxyPort = "50000"

# 代理隧道验证信息
proxyUser = "XVGG1705966243473906"
proxyPass = "1OmSB1rNDiWCVG0E"

proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
    "host": proxyHost,
    "port": proxyPort,
    "user": proxyUser,
    "pass": proxyPass,
}

proxy_handler = request.ProxyHandler({
    "http": proxyMeta,
    "https": proxyMeta,
})

opener = request.build_opener(proxy_handler)
request.install_opener(opener)
ip = request.urlopen('https://whois.pconline.com.cn/ipJson.jsp?json=true').read().decode(encoding='gbk')
print(ip)
