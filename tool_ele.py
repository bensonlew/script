#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'

import pickle
import sys
import os

def load_by_ele(pk):
    a=open(pk, 'rb')
    tool_pk = pickle.load(a)
    a.close
    for key,value in tool_pk.__dict__.items():
        if key == '_options':
            for op_key,op_value in value.items():
                if op_value.__dict__['_type'] == 'infile':
                    path = ''
                    if op_value.__dict__['_value'].__dict__['_properties'].has_key('path'):
                        path = op_value.__dict__['_value'].__dict__['_properties']['path']
                    print "    {}: is_set: {} path {} format:{}".format(op_key, 
                                                                        op_value.__dict__['_value'].__dict__['_is_set'],
                                                                        path,
                                                                        op_value.__dict__['_options'] )
                                                                         
                elif op_value.__dict__['_type'] == 'outfile':
                    print "    {}: is_set: {} path format:{}".format(op_key, 
                                                                     op_value.__dict__['_value'].__dict__['_is_set'],
                                                                     op_value.__dict__['_options'] )
                else:
                    print "    {}: {}  format:{}".format(op_key, op_value.__dict__['_value'], op_value.__dict__['_options'] )
        else:
            print "{}: {}".format(key, value)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "python ~/sg-users/liubinxu/script/tool_ele.py tool.pk"
    else:
        load_by_ele(sys.argv[1])
