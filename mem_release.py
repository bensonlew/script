# -*- coding: utf-8 -*-

from ctypes import *
import time
import sys


#在这里申请1G的内存，单位k
num = int(sys.argv[1])
mem = create_string_buffer(num*1024*1024*1024)


#释放内存
mem= None
