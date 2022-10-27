#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'

import sys
import os


def convert(dendrogram_f):
    leaf_list = list()
    leaf_len = 0.01
    '''
    with open(order_f, 'r') as f:
        for line in f:
            leaf_list.append(line.strip())
    '''
    node_dict = dict()
    tree = ""
    node_num = 0
    with open(dendrogram_f, 'r') as f:
        for line in f:
            node_num += 1
            n1, n2, height = line.strip().split("\t")
            if int(n1) < 0:
                height_n1 = float(height) - leaf_len
                n1_str = "{}:{}".format(abs(int(n1)), height_n1)
            else:
                n1_str = node_dict[abs(int(n1))]
            if int(n2) < 0:
                height_n2 = float(height) - leaf_len
                n2_str = "{}:{}".format(abs(int(n2)), height_n2)
            else:
                n2_str = node_dict[abs(int(n2))]
            n_str = "({},{}):{}".format(n1_str, n2_str, height)
            node_dict[node_num] = n_str

    with open(dendrogram_f + ".tree", 'w') as f:
        f.write(n_str)
    return n_str


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "python ~/sg-users/liubinxu/script/dendrogram2newick dendrogram"
    else:
        convert(sys.argv[1])
