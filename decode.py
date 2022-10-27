#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'
import os
import re
import sys

for line in sys.stdin:
    words = line.strip("\n").split(" ")
    if "ERROR" in words or "ExitError:" in words:
        for n,word in enumerate(words):
            words[n] = word.decode('unicode_escape')
        print " ".join(words)
    else:
        print " ".join(words)
            
