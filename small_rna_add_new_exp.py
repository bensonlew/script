# -*- coding: utf-8 -*-
# __author__ = 'gudeqing, qinjincheng'
import sys
import pandas as pd
from bson.objectid import ObjectId
from biocluster.config import Config

a  = pd.DataFrame()
# ef = "Srna/output/novel_mirna_count.xls"
#
ef = sys.argv[1]
task_id = sys.argv[2]

all_exp_pd = pd.read_table(ef, index_col=0, header=0)
all_exp_pd.rename(columns={"miRNA_ID": "seq_id"}, inplace=True)
from bson.objectid import ObjectId

project_type = 'small_rna'
db = Config().get_mongo_client(mtype=project_type)[Config().get_mongo_dbname(project_type)]
# all_exp_pd['exp_id'] = ObjectId("5f91522d28fb4f5fd291e96b")
exp_dict = db['sg_exp'].find_one({'task_id': task_id, 'exp_type': 'count'})
all_exp_pd['exp_id'] = exp_dict['main_id']
all_exp_pd['is_novel'] = True


all_exp_pd.reset_index(level=0, inplace=True)
all_exp_pd.rename(columns={"miRNA_ID": "seq_id"}, inplace=True)
row_dict_list = all_exp_pd.to_dict('records')

conn = db["sg_exp_detail"]
conn.insert_many(row_dict_list)

