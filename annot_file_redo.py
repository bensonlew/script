from mbio.packages.ref_rna_v2.extract_annotation_result import RefAnnotation
import os
import sys


a= RefAnnotation()
a.annot_dir = sys.argv[1]
a.out_dir = sys.argv[2]
a.change_annot_result(os.path.join(a.annot_dir, "refannot_class/all_annot.xls"), os.path.join(a.out_dir, 'AnnotDetail/ref_gene_annot_detail.xls'), os.path.join(a.out_dir, 'AnnotDetail/ref_transcript_annot_detail.xls'))
if os.path.exists(os.path.join(a.annot_dir, "newannot_class/all_annot.xls")):
    a.change_annot_result(os.path.join(a.annot_dir, "newannot_class/all_annot.xls"), os.path.join(a.out_dir, 'AnnotDetail/new_gene_annot_detail.xls'), os.path.join(a.out_dir, 'AnnotDetail/new_transcript_annot_detail.xls'))
    a.change_annot_result(os.path.join(a.annot_dir, "allannot_class/all_annot.xls"), os.path.join(a.out_dir, 'AnnotDetail/all_gene_annot_detail.xls'), os.path.join(a.out_dir, 'AnnotDetail/all_transcript_annot_detail.xls'))
import pandas as pd
pd.

