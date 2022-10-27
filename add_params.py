# -*- coding: utf-8 -*-
# __author__ = 'zoujiaxun'

import logging
import sys
import time
import json
from biocluster.config import Config
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(format='%(asctime)s\t%(name)s\t%(levelname)s : %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)


class AddbatchMongo(object):
    def __init__(self, project_type, table_name, add_key, add_value):
        self.db = Config().get_mongo_client(mtype=project_type)[Config().get_mongo_dbname(project_type)]
        self._project_type = project_type
        self.table_name = table_name
        self.add_key = add_key
        self.add_value = add_value
    def run(self):
        self.add_params()

    def add_params(self):
        sg_diff = self.db[self.table_name]
        document = sg_diff.find({})
        for record in document:
            try:
                params = record['params']
                params = json.loads(params)
                params_old = params
		if self.add_key not in params_old:
                    params[self.add_key] = str(self.add_value)
                    params_new = json.dumps(params, sort_keys=True, separators=(',', ':'))
                    params_old = json.dumps(params_old, sort_keys=True, separators=(',', ':'))
                    sg_diff.update({'_id': record["_id"]}, {'$set': {'params': params_new}})
		else:
  		    continue
            except:
                continue

if __name__ == '__main__':
    logging.info('Usage: python add_batch.py <project_type>')
    # task_id = sys.argv[1]
    project_type = sys.argv[1]
    table_name = sys.argv[2]
    add_key = sys.argv[3]
    add_value = sys.argv[4]
    start_time = time.time()
    inst = AddbatchMongo(project_type, table_name, add_key, add_value)
    inst.run()
    end_time = time.time()
    logging.info('Elapsed time: {}'.format(end_time - start_time))
