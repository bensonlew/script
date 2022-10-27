#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'

import json
import sys

js_file = sys.argv[1]
lines = open(js_file, "rb").readlines()
try:
    if "var content " in lines[2]:
        content = lines[2].split("var content = ")[1].strip().rstrip(";")
    if "var content " in lines[3]:
        content = lines[3].split("var content = ")[1].strip().rstrip(";")
    if "var content " in lines[4]:
        content = lines[4].split("var content = ")[1].strip().rstrip(";")
    else:
        content = lines[5].split("var content = ")[1].strip().rstrip(";")
except:
    print js_file
a = json.loads(content)
jsonout = open(sys.argv[2],'w')
jsonout.write(json.dumps(a, indent=4))
jsonout.close()
