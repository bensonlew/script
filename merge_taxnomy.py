import os
import json
import logging
import re
import sys

import regex

def merge_name(old, new):
    known_dict =dict()
    with open(old, 'r') as f:
        for line in f:
            cols = line.split("\t")
            if cols[0] in known_dict:
                known_dict[cols[0]].append(line)
            else:
                known_dict[cols[0]] = [line]
    
    with open(new, 'r') as f, open(new + ".merge", 'w') as fo:
        a = set()
        for line in f:
            fo.write(line)
            cols = line.split("\t")
            if cols[6] == "scientific name":
                a.add(cols[0])
        for tax in known_dict:
            if tax in a:
                pass
            else:
                fo.write("".join(known_dict[tax]))

def merge_node(old, new):
    known_dict =dict()
    with open(old, 'r') as f:
        for line in f:
            cols = line.split("\t")
            known_dict[cols[0]] = [cols[4], line]
    
    with open(new, 'r') as f, open(new + ".merge", 'w') as fo:
        a = set()
        for line in f:
            cols = line.split("\t")
            fo.write(line)
            a.add(cols[0])
        for tax in known_dict:
            if tax in a:
                pass
            else:
                fo.write("".join(known_dict[tax][1]))
                

if __name__ == '__main__':
    merge_type =  sys.argv[1]
    old = sys.argv[2]
    new = sys.argv[3]
    if merge_type == "node":
        merge_node(old, new)
    else:
        merge_name(old, new)
