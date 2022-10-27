import random
from mbio.workflows.single import SingleWorkflow
from biocluster.wsheet import Sheet
from biocluster.wpm.client import *
import sys
import json
worker = worker_client()


json_file = open(sys.argv[1], 'r')
data = json.load(json_file)
data["rerun"] = True
data["to_file"] = []
info = worker.add_task(data)
print info
'''
wsheet = Sheet(data=data)
wf = SingleWorkflow(wsheet)
wf.run()
'''
