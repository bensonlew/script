# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'

import logging
import sys
import time
import json
from biocluster.config import Config
from concurrent.futures import ThreadPoolExecutor
import sqlite3
from collections import defaultdict
import re

def biomart(biomart_path, biomart_type='type1'):
        """
        为了获得已知基因的description, gene_type信息
        :param biomart_path: this file must be tab separated.
        :param biomart_type: the type of biomart file
        :return: dict1. gene_id:  {"trans_id": [trans_id], "gene_name": [gene_name],
        "chromosome": [chromosome], "gene_type": [gene_type], "description": [desc],
         "strand": [strand], "pep_id": [pep_id], "start": [start], "end": [end]}
        dict2. pep->transcript
        """
        if biomart_type == "type1":
            gene_id_ind = 0
            trans_id_ind = 1
            gene_name_ind = 2
            chromosome_ind = 8
            gene_type_ind = 16
            desc_ind = 7
            strand_ind = 11
            start_ind = 9
            end_ind = 10
            pep_id_ind = 6
        elif biomart_type == 'type2':
            gene_id_ind = 0
            trans_id_ind = 1
            gene_name_ind = 2
            chromosome_ind = 6
            gene_type_ind = 14
            desc_ind = 5
            strand_ind = 9
            start_ind = 7
            end_ind = 8
            pep_id_ind = 4
        elif biomart_type == 'type3':
            gene_id_ind = 0
            trans_id_ind = 1
            gene_name_ind = 0
            chromosome_ind = 4
            gene_type_ind = 12
            desc_ind = 3
            strand_ind = 7
            start_ind = 5
            end_ind = 6
            pep_id_ind = 2
        else:
            raise ValueError('biomart_type should be one of type1, type2, type3')

        biomart_info = dict()
        pep2transcript = dict()
        with open(biomart_path) as f:
            for line in f:
                if not line.strip():
                    continue
                line = line.replace('\t\t', '\t-\t')
                tmp_list = line.strip('\n').split("\t")
                gene_id = tmp_list[gene_id_ind]
                trans_id = tmp_list[trans_id_ind]
                gene_name = tmp_list[gene_name_ind]
                if biomart_type == 'type3':
                    gene_name = '-'
                chromosome = tmp_list[chromosome_ind]
                gene_type = tmp_list[gene_type_ind]
                desc = tmp_list[desc_ind]
                strand_tmp = tmp_list[strand_ind]
                if strand_tmp == "1":
                    strand = "+"
                elif strand_tmp == "-1":
                    strand = "-"
                elif strand_tmp == "0":
                    strand = "."
                else:
                    strand = strand_tmp
                start = tmp_list[start_ind]
                end = tmp_list[end_ind]
                pep_id = tmp_list[pep_id_ind]

                biomart_info.setdefault(gene_id, defaultdict(list))
                biomart_info[gene_id]['trans_id'].append(trans_id)
                biomart_info[gene_id]['gene_name'].append(gene_name)
                biomart_info[gene_id]['chromosome'].append(chromosome)
                biomart_info[gene_id]['gene_type'].append(gene_type)
                biomart_info[gene_id]['description'].append(desc)
                biomart_info[gene_id]['pep_id'].append(pep_id)
                biomart_info[gene_id]['strand'].append(strand)
                biomart_info[gene_id]['start'].append(start)
                biomart_info[gene_id]['end'].append(end)
                pep2transcript[pep_id] = trans_id

        if not biomart_info:
            raise Exception("biomart information is None")
        else:
            # raw check
            if (not start.isdigit()) or (not end.isdigit()):
                raise NameError('we find "start" or "end" is not digit. Maybe biomart_type is wrong')
        print('Information of {} genes was parsed from biomart file'.format(len(biomart_info)))
        return biomart_info, pep2transcript

def get_pep_seq(pep_path, p2t):
        """
        get transcript's pep info, including protein sequence
        :param pep_path:
        :param p2t: dict of pep_id:transcript_id
        :return: dict, trans_id={"name": pep_id, "sequence": pep_sequence,
                                 "sequence_length": len(pep_sequence)}
        """
        pep_dict = dict()
        j, trans_id, trans_id_else, pep_sequence, pep_id = 0, '', '', '', ''
        pep_pattern = re.compile(r'>([^\s]+)')
        trans_pattern = re.compile(r'transcript:([^\s]+)')

        with open(pep_path) as f:
            for line in f:
                if not line.strip():
                    continue
                if line.startswith('>'):
                    j += 1
                    if j > 1:
                        seq_len = len(pep_sequence)
                        if trans_id:
                            pep_dict[trans_id] = dict(name=pep_id, sequence=pep_sequence, sequence_length=seq_len)
                            pep_dict[trans_id_else] = dict(name=pep_id, sequence=pep_sequence, sequence_length=seq_len)
                    pep_id = pep_pattern.match(line).group(1)
                    try:
                        trans_id = trans_pattern.search(line).group(1)
                    except Exception:
                        if pep_id not in p2t:
                            if '.' in pep_id:
                                pep_id_else = pep_id[:pep_id.rfind('.')]
                                if pep_id_else not in p2t:
                                    print('transcript id -> protein {} failed in biomart'.format(pep_id_else))
                                    trans_id = None
                                    continue
                                else:
                                    trans_id = p2t[pep_id_else]
                            else:
                                print('transcript id -> protein {} failed in biomart'.format(pep_id))
                                trans_id = None
                                continue
                        else:
                            trans_id = p2t[pep_id]
                    if '.' in trans_id:
                        trans_id_else = trans_id[:trans_id.rfind('.')]
                    else:
                        trans_id_else = trans_id
                    pep_sequence = ''
                else:
                    pep_sequence += line.strip()
            else:
                seq_len = len(pep_sequence)
                pep_dict[trans_id] = dict(name=pep_id, sequence=pep_sequence, sequence_length=seq_len)
                pep_dict[trans_id_else] = dict(name=pep_id, sequence=pep_sequence, sequence_length=seq_len)
        if not pep_dict:
            print('提取蛋白序列信息为空')
        print("共统计出{}条转录本的蛋白序列信息".format(len(pep_dict)))
        return pep_dict
    
def add_gene_detail(db_path, biomart_file, biomart_type, known_pep):
    biomart_gene_detail, pep2trans = biomart(biomart_file, biomart_type)
    known_pep = get_pep_seq(known_pep, pep2trans)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for k, pep_dict in known_pep.items():
        update = "UPDATE trans_annot SET pep_id = '{}', pep_seq = '{}' WHERE transcript_id = '{}';".format(pep_dict['name'], pep_dict['sequence'], k)
        print update
        cursor.execute(update)
    conn.commit()
    conn.close()


if __name__ == '__main__':
    logging.info('Usage: python add_batch.py <project_type>')
    # task_id = sys.argv[1]
    project_type = sys.argv[1]
    table_name = sys.argv[2]
    add_key = sys.argv[3]
    add_gene_detail(db_path=sys.argv[1], biomart_file=sys.argv[2], known_pep=sys.argv[3], biomart_type="type2")

    
