#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'

import pickle
import sys
import os
import json
from biocluster.option import Option

def load_by_ele(pk):
    a=open(pk, 'rb')
    tool_pk = pickle.load(a)
    
    a.close
    show_dict = dict()
    for key,value in tool_pk.__dict__.items():
        if key == '_options':
            for op_key, op_value in value.items():
                if op_value.__dict__['_type'] == 'infile':
                    path = ''
                    if op_value.__dict__['_value'].__dict__['_properties'].has_key('path'):
                        path = op_value.__dict__['_value'].__dict__['_properties']['path']

                        show_dict.update({op_key: {"_value": op_value.__dict__['_value'].__dict__}})
                    # print "    {}: is_set: {} path {} format:{}".format(op_key, 
                    #                                                     op_value.__dict__['_value'].__dict__['_is_set'],
                    #                                                     path,
                    #                                                     op_value.__dict__['_options'] )

                elif op_value.__dict__['_type'] == 'outfile':
                    show_dict.update({op_key: {"_value": op_value.__dict__['_value'].__dict__}})
                    # print "    {}: is_set: {} path format:{}".format(op_key, 
                    #                                                  op_value.__dict__['_value'].__dict__['_is_set'],
                    #                                                  op_value.__dict__['_options'] )
                else:
                    show_dict.update({op_key: {'_value': op_value.__dict__['_value'], '_options': op_value.__dict__['_options']}})
                    # print "    {}: {}  format:{}".format(op_key, op_value.__dict__['_value'], op_value.__dict__['_options'])
            print json.dumps(show_dict, indent=4)
        else:
            pass
            # print "{}: {}".format(key, value)

def edit_pk(pk, edit_file):
    a=open(pk, 'rb')
    tool_pk = pickle.load(a)
    options = tool_pk.__dict__['_options']
    with open(edit_file, 'r') as f:
        edict_dict = json.load(f)
        for k, v in edict_dict.items():
            if k in options:
                pickle_opt = options[k]
                if pickle_opt.__dict__['_type'] == 'infile':
                    if pickle_opt.__dict__['_value'].__dict__['_properties'].has_key('path'):
                        if pickle_opt.__dict__['_value'].__dict__['_properties']['path'] != v['_value']['_properties']['path']:
                            pickle_opt.__dict__['_value'].__dict__['_properties']['path'] = v['_value']['_properties']['path']
                else:
                    if pickle_opt.__dict__['_value'] != v['_value']:
                        pickle_opt.__dict__['_value'] = v['_value']
            else:
                print k
                options[k] = Option(v["_options"])
                options[k].__dict__['_value'] = v['_value']
    with open(pk, 'w') as f:
        f.write(pickle.dumps(tool_pk))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "python ~/sg-users/liubinxu/script/tool_ele.py tool.pk"
    elif len(sys.argv) ==3 :
        edit_pk(sys.argv[1], sys.argv[2])
    else:
        load_by_ele(sys.argv[1])
