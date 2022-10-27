#!/usr/bin/python
#-*- coding:utf-8 -*-

import sys
import socket
# import threading
from time import sleep
from datetime import datetime
import os


if __name__ == "__main__":
    while 1:
        print os.environ.get("TESTAA", "")
        sleep(5)	
