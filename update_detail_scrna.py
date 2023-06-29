# -*- coding: utf-8 -*-
# __author__ 'gudeqing,qinjincheng'


import re

import datetime
import unittest
import os
import types


class TestFunction(unittest.TestCase):
    """
    This is test for the tool. Just run this script to do test.
    """



    def test_gene_detail(self):
        from mbio.workflows.medical_transcriptome.medical_transcriptome_test_api import MedicalTranscriptomeTestApiWorkflow
        from biocluster.wsheet import Sheet
        import random

        data = {
            "id": "c99f_d1oo8598pmnr7icf56qve2",
            "project_sn": "j897kab1d3r0lu0fl5in1qm6l8",
            "type": "workflow",
            "name": "scrna.scrna_test_api",
            "options": {
            },
        }
        feature_table = ""
        annot_file = ""
        refrna_seqdb = "/"
        species_urls = ""
        test_api = GeneDetail(bind_object=None)
        test_api.add_gene_detail(feature_table=feature_table, gene_detail_path=annot_file, refrna_seqdb=refrna_seqdb, species_urls=species_urls)

if __name__ == '__main__':
    os.environ["current_mode"]="workflow"
    os.environ["NTM_PORT"]="7322"
    os.environ["WFM_PORT"]="7321"
    unittest.main()
