# -*- coding:utf-8 -*-
# __author__ = 'shicaiping,qinjincheng'

import glob
import json
import os
import re
import shutil
from collections import OrderedDict

import pandas as pd
from biocluster.config import Config
from biocluster.core.exceptions import OptionError
from biocluster.workflow import Workflow

from mbio.packages.ref_rna_v2.copy_file import CopyFile
from mbio.packages.ref_rna_v2.extract_annotation_result import RefAnnotation
from mbio.packages.ref_rna_v3.functions import workfuncdeco
from mbio.packages.ref_rna_v3.upload import set_assembly, set_rmats
from mbio.packages.ref_rna_v2.functions import tryforgood


class RefrnaWorkflow(Workflow):
    def __init__(self, wsheet_object):
        self._sheet = wsheet_object
        super(RefrnaWorkflow, self).__init__(wsheet_object)
        options = [
            ## 样本选择
            # 样本个数 ['multiple', 'single']
            {'name': 'sample_num', 'type': 'string', 'default': 'multiple'},
            # 分析方案 ['total', 'mapping', 'annotation', 'quantification']
            {'name': 'analysis_strategy', 'type': 'string', 'default': 'total'},

            ## 基础参数设置
            # 数据类型 ['rawdata', 'cleandata']
            {'name': 'datatype', 'type': 'string', 'default': 'rawdata'},
            # 测序类型 ['PE', 'SE']
            {'name': 'fq_type', 'type': 'string', 'default': 'PE'},
            # 质控软件 ['fastp', 'seqprep']
            {'name': 'qc_soft', 'type': 'string', 'default': 'fastp'},
            # "接头序列"    # --adapter_sequence,the adapter for read1  #add by fwy 20200401
            {'name': 'adapter_a', 'type': 'string', 'default': 'AGATCGGAAGAGCACACGTC'},
            # "接头序列"    # --adapter_sequence,the adapter for read2 -only in PE  #add by fwy 20200401
            {'name': 'adapter_b', 'type': 'string', 'default': 'AGATCGGAAGAGCGTCGTGT'},
            # 测序质量 ['phred 33', 'phred 64']
            {'name': 'quality_score_system', 'type': 'string', 'default': 'phred 33'},
            # 长度需求
            {'name': 'length_required', 'type': 'string', 'default': '30'},
            # 链特异性 [False, True]
            {'name': 'strand_specific', 'type': 'bool', 'default': False},
            # 链特异性方向 ['PE': {'RF', 'FR'}, 'SE': {'R', 'F'}]
            {'name': 'strand_dir', 'type': 'string', 'default': 'forward'},
            # 生物学重复 [True, False]
            {'name': 'is_duplicate', 'type': 'bool', 'default': True},
            # 原始序列文件
            {'name': 'fastq_dir', 'type': 'infile', 'format': 'sequence.fastq_dir'},
            # 质控序列文件
            # {'name': 'qc_dir', 'type': 'string', 'default': None},
            {'name': 'qc_dir', 'type': 'infile', 'format': 'sequence.fastq_dir'},
            # 分组方案
            {'name': 'group_table', 'type': 'infile', 'format': 'sample.group_table'},
            # 配对信息表
            {'name': 'pair_table', 'type': 'infile', 'format': 'sample.group_table'},
            # 对照组文件
            {'name': 'control_file', 'type': 'infile', 'format': 'sample.control_table'},
            # 物种类别 ['Animal', 'Plant', 'Protist', 'Fungi']
            {'name': 'taxonmy', 'type': 'string', 'default': 'Animal'},
            # 具体物种 sg_genome_db.name
            {'name': 'ref_genome', 'type': 'string', 'default': None},
            # 基因组版本 sg_genome_db.assembly
            {'name': 'genome_version', 'type': 'string', 'default': None},
            # 基因组注释版本 sg_genome_db.annot_version
            {'name': 'genome_annot_version', 'type': 'string', 'default': None},
            # 基因组编号 sg_genome_db.genome_id
            {'name': 'genome_id', 'type': 'string', 'default': None},
            # 终止后续分析
            {'name': 'mapping_stop', 'type': 'bool', 'default': True},
            # 大于 %的样本
            {'name': 'mapping_sample_percent', 'type': 'float', 'default': 50.0},
            # Mapping Ratio 小于
            {'name': 'mapping_ratio', 'type': 'float', 'default': 60.0},
            # 终止后续分析
            {'name': 'rrna_stop', 'type': 'bool', 'default': True},
            # 大于 %的样本
            {'name': 'rrna_sample_percent', 'type': 'float', 'default': 50.0},
            # rRNA Ratio 小于 %
            {'name': 'rrna_ratio', 'type': 'float', 'default': 15.0},

            ## 高级参数设置
            # 分析水平 ['Transcript', 'Gene']
            {'name': 'level', 'type': 'string', 'default': 'Transcript'},
            # 比对软件 ['Hisat', 'Tophat', 'STAR']
            {'name': 'align_method', 'type': 'string', 'default': 'Hisat'},
            # 转录组质量评估
            {'name': 'map_assess_method', 'type': 'string', 'default': 'saturation,coverage,distribution,chr_stat'},
            # 是否进行拼接 [True, False]
            {'name': 'is_assemble', 'type': 'bool', 'default': True},
            # 拼接软件 ['stringtie', 'cufflinks']
            {'name': 'assemble_method', 'type': 'string', 'default': 'stringtie'},
            # NR库分类 ['Animal, Plant', 'Protist', 'Fungi', 'All']
            {'name': 'nr_database', 'type': 'string', 'default': None},
            # KEGG库分类 ['Animal, Plant', 'Protist', 'Fungi', 'All']
            {'name': 'kegg_database', 'type': 'string', 'default': None},
            # NR(GO)-Evalue
            {'name': 'nr_evalue', 'type': 'float', 'default': 1e-5},
            # Swissprot-Evalue
            {'name': 'swissprot_evalue', 'type': 'float', 'default': 1e-5},
            # KEGG-Evalue
            {'name': 'kegg_evalue', 'type': 'float', 'default': 1e-5},
            # COG-Evalue
            {'name': 'cog_evalue', 'type': 'float', 'default': 1e-5},
            # Pfam-Evalue
            {'name': 'pfam_evalue', 'type': 'float', 'default': 1e-5},
            # 其它注释过滤参数
            {'name': 'nr_identity', 'type': 'float', 'default': 0},
            {'name': 'nr_similarity', 'type': 'float', 'default': 0},
            {'name': 'swissprot_identity', 'type': 'float', 'default': 0},
            {'name': 'swnissprot_similarity', 'type': 'float', 'default': 0},
            {'name': 'kegg_identity', 'type': 'float', 'default': 0},
            {'name': 'kegg_similarity', 'type': 'float', 'default': 0},
            {"name": "kegg_subtax1", "type": "string", "default": None},
            {"name": "kegg_subtax2", "type": "string", "default": None},
            {"name": "kegg_specific", "type": "string", "default": None},
            {"name": "kegg_version", "type": "string", "default": "202003"},
            {'name': 'cog_identity', 'type': 'float', 'default': 0},
            {'name': 'cog_similarity', 'type': 'float', 'default': 0},
            {'name': 'database', 'type': 'string', 'default': 'go,nr,cog,kegg,swissprot,pfam'},

            # 表达定量软件 ['RSEM', 'Kallisto', 'Salmon']
            {'name': 'express_method', 'type': 'string', 'default': 'RSEM'},
            # 表达定量指标 ['tpm', 'fpkm']
            {'name': 'exp_way', 'type': 'string', 'default': 'tpm'},
            # Filter TPM
            {'name': 'filter_tpm', 'type': 'float', 'default': 0},
            # 差异分析软件 ['DESeq2', 'edgeR', 'DEGseq', 'limma', 'NOIseq']
            {'name': 'diff_method', 'type': 'string', 'default': 'DESeq2'},
            # FC
            {'name': 'fc', 'type': 'float', 'default': 2},
            # 显著性指标
            {'name': 'pvalue_padjust', 'type': 'string', 'default': 'padjust'},
            # 显著性水平
            {'name': 'diff_fdr_ci', 'type': 'float', 'default': 0.05},
            # 多重验证校正方法 ['BH', 'Bonferroni', 'Holm', 'BY']
            {'name': 'padjust_way', 'type': 'string', 'default': 'BH'},
            # SNP分析 ['True', 'False', 'Skip']
            {'name': 'is_snp', 'type': 'string', 'default': 'True'},
            # SNP分析方法 ['Samtools', 'GATK', 'Sentieon']
            {'name': 'snp_method', 'type': 'string', 'default': 'samtools'},
            # 可变剪切分析 ['True', 'False', 'Skip']
            {'name': 'is_as', 'type': 'string', 'default': 'True'},
            # 可变剪切分析方法 ['rMATS', 'ASprofile']
            # {'name': 'as_method', 'type': 'string', 'default': 'rMATS'},
            # 是否将质控结果和比对结果文件传输至线下服务器
            {'name': 'upload_offline', 'type': 'bool', 'default': False}
        ]
        self.add_option(options)
        self.set_options(self._sheet.options())
        self.task_id = self._sheet.id
        self.project_sn = self._sheet.project_sn

        database = Config().get_mongo_client(mtype='ref_rna_v2')[Config().get_mongo_dbname('ref_rna_v2')]
        collection = database['sg_genome_db']
        genome_info = collection.find_one({'genome_id': self.option('genome_id')})
        if not genome_info:
            self.set_error('数据库中不存在该物种的注释信息，程序退出', code='13700320')
        genome_path = os.path.join(self.config.SOFTWARE_DIR, 'database/Genome_DB_finish')
        self.ref_annot_dir = os.path.join(genome_path, genome_info['anno_path_v2'])
        if not os.path.isdir(self.ref_annot_dir):
            self.set_error('数据库中不存在该物种的参考注释文件，程序退出', code='13700321')
        self.ref_genome = os.path.join(genome_path, genome_info['dna_fa'])
        if not os.path.isfile(self.ref_genome):
            self.set_error('数据库中不存在该物种的参考基因组序列FASTA文件，程序退出', code='13700323')
        self.ref_gtf = os.path.join(genome_path, genome_info['gtf'])
        if not os.path.isfile(self.ref_gtf):
            self.set_error('数据库中不存在该物种的参考基因组注释GTF文件，程序退出', code='13700324')
        self.genome_id = genome_info['genome_id']
        if not self.genome_id:
            self.set_error('数据库中不存在该物种的参考基因组ID编号，程序退出', code='13700325')
        self.des = os.path.join(genome_path, genome_info['bio_mart_annot'])
        if not os.path.isfile(self.des):
            self.set_error('数据库中不存在该物种的功能描述信息（BIOMART）', code='13700326')
        self.des_type = genome_info['biomart_gene_annotype']
        if not self.des_type:
            self.set_error('数据库中不存在该物种的功能描述信息（ANNOTYPE）', code='13700327')
        self.known_cds = os.path.join(genome_path, genome_info['cds'])
        if not os.path.isfile(self.known_cds):
            self.set_error('数据库中不存在该物种的CDS序列FASTA文件', code='13700328')
        self.known_pep = os.path.join(genome_path, genome_info['pep'])
        if not os.path.isfile(self.known_pep):
            self.set_error('数据库中不存在该物种的PEP序列FASTA文件', code='13700329')
        self.entrez = os.path.join(genome_path, genome_info['ensemble2entrez'])
        if not os.path.isfile(self.entrez):
            self.set_error('数据库中不存在该物种的ENTREZ对应文件', code='13700330')
        self.genome_stat = os.path.join(genome_path, genome_info['gene_stat'])
        if not os.path.isfile(self.genome_stat):
            self.set_error('数据库中不存在该物种的参考基因组统计文件', code='13700331')
        self.g2t2p = os.path.join(genome_path, genome_info['g2t2p'])
        if not os.path.isfile(self.g2t2p):
            self.set_error('数据库中不存在该物种的G2T2P对应文件', code='13700332')
        self.species = genome_info['taxon_id']
        if self.species == None or not self.species:
            self.species = ""
            # self.set_error('数据库中不存在该物种的TAXON编号', code='13700333')
        self.hyperlink = genome_info['ensemble_web']
        if not self.hyperlink:
            self.set_error('数据库中不存在该物种的参考基因组来源超链接', code='13700334')
        self.known_ko = os.path.join(genome_path, genome_info['kegg'])
        if not os.path.isfile(self.known_ko):
            self.set_error('数据库中不存在该种的PATHWAY对应文件', code='13700335')
        self.genome_version = genome_info['assembly']
        self.annot_version = genome_info['annot_version']
        self.organism_name = genome_info['organism_name']
        ## 定义分析方案
        if self.option("analysis_strategy") == "mapping":
            self.analysis_content = ["mapping"]
        elif self.option("analysis_strategy") == "annotation":
            self.analysis_content = ["mapping", "annotation"]
        elif self.option("analysis_strategy") == "quantification":
            self.analysis_content = ["mapping", "annotation", "quantification"]
        elif self.option("analysis_strategy") == "total":
            self.analysis_content = ["mapping", "annotation", "quantification", "other"]
        else:
            self.analysis_content = ["mapping", "annotation", "quantification", "other"]

        # 用于在重运行时，删除已经导入到mongo库的表，避免数据重复
        data = os.path.join(self.work_dir, 'data.json')
        if os.path.exists(data):
            with open(data, 'r') as load_f:
                load_dict = json.load(load_f)
                if 'rerun' in load_dict and load_dict['rerun']:
                    self.logger.info("该项目重运行中，先删除mongo库中已有数据")
                    self.delete_mongo_data()

    @tryforgood
    def delete_mongo_data(self):
        self.script = os.path.join(self.config.PACKAGE_DIR, 'project_demo/delete_demo.py')
        self.program = os.path.join(self.config.SOFTWARE_DIR, 'program/Python/bin/python')
        cmd = '{} {}'.format(self.program, self.script)
        cmd += ' {} {}'.format(self.task_id, 'ref_rna_v2')
        code = os.system(cmd)
        if code == 0:
            self.logger.info("命令{}执行成功！".format(cmd))
        else:
            raise Exception("命令{}执行失败！".format(cmd))

    @workfuncdeco
    def check_options(self):
        if self.option("kegg_version") not in ['2020', '2017', '2020版', '2017版']:
            raise OptionError('KEGG数据库版本不支持{}'.format(self.option("kegg_version")))
        if self.option("kegg_version") in ['2020', '2020版']:
            self.option("kegg_version", "202003")
        for k, v in self.sheet.options().items():
            self.logger.debug('{} = {}'.format(k, v))
        else:
            self.logger.info('succeed in displaying incoming options')
        dup = False
        # 判断样本个数选择、分组方案以及is_duplicate是否正确
        if self.option('group_table').is_set:
            group_dict = self.option("group_table").prop['group_dict']
            for g in group_dict.keys():
                if len(group_dict[g]) > 1:
                    dup = True
            if self.option('is_duplicate') != dup:
                self.logger.info(self.option('is_duplicate'))
                self.logger.info(dup)
                raise OptionError('生物学重复参数选择和分组方案不匹配，请检查输入是否有误')
            if self.option('group_table').prop['sample_number'] >= 2:
                if self.option('sample_num') == 'single':
                    raise OptionError('分组方案表中有{}个样本，与样本个数为{}相互矛盾，请重新确认参数.'.format(
                        self.option('group_table').prop['sample_number'], self.option('sample_num')))
        if self.option('sample_num') == 'single':
            self.option('is_duplicate', False)
            self.option('is_as', 'False')
        else:
            if self.option("analysis_strategy") in ["quantification", "total"] and not self.option('group_table').is_set:
                raise OptionError('必须上传样本分组表')
            elif not self.option('group_table').is_set:
                samples = list()
                if self.option('datatype') == 'rawdata':
                    fastq_dir = self.option('fastq_dir').path
                else:
                    fastq_dir = self.option('qc_dir').path
                for line in open(os.path.join(fastq_dir, 'list.txt')):
                    sample = line.strip().split('\t')[1]
                    if sample not in samples:
                        samples.append(sample)
                group_table = os.path.join(self.work_dir, 'group.txt')
                with open(group_table, 'w') as w:
                    w.write('#sample\tgroup\n')
                    for sample in samples:
                        w.write('{}\t{}\n'.format(sample, sample))
                self.option("group_table", group_table)
        if not self.option('fq_type') in ['PE', 'SE']:
            raise OptionError('测序类型应为PE或SE', code='13700309')
        if not 0 < self.option('nr_evalue') < 1:
            raise OptionError('NR比对的E值超出范围', code='13700311')
        if not 0 < self.option('cog_evalue') < 1:
            raise OptionError('COG比对的E值超出范围', code='13700312')
        if not 0 < self.option('kegg_evalue') < 1:
            raise OptionError('KEGG比对的E值超出范围', code='13700313')
        if not 0 < self.option('swissprot_evalue') < 1:
            raise OptionError('SWISSPROT比对的E值超出范围', code='13700314')
        if not 0 < self.option('pfam_evalue') < 1:
            raise OptionError('PFAM比对的E值超出范围', code='13700315')
        if not self.option('align_method').lower() in ['tophat', 'hisat', 'star']:
            raise OptionError('比对软件应为Tophat或Hisat或STAR', code='13700316')
        for i in self.option('map_assess_method').split(','):
            if i.lower() not in ['saturation', 'distribution', 'coverage', 'chr_stat']:
                raise OptionError('比对质量评估分析没有%s，请检查', variables=(i), code='13700317')
        if self.option('is_assemble'):
            if self.option('assemble_method').lower() not in ['cufflinks', 'stringtie']:
                raise OptionError('拼接软件应在cufflinks和stringtie中选择', code='13700318')
        if self.option('nr_database') == 'All':
            self.option('nr_database', 'nr')
        elif self.option('nr_database') == 'Animal':
            self.option('nr_database', 'metazoa')
        elif self.option('nr_database') == 'Plant':
            self.option('nr_database', 'viridiplantae')
        elif self.option('nr_database') == 'Protist':
            self.option('nr_database', 'protist')
        elif self.option('nr_database') == 'Fungi':
            self.option('nr_database', 'fungi')
        if self.option('kegg_database') == 'All':
            self.option('kegg_database', 'All')
        elif self.option('kegg_database') == 'Animal':
            self.option('kegg_database', 'Animals')
        elif self.option('kegg_database') == 'Plant':
            self.option('kegg_database', 'Plants')
        elif self.option('kegg_database') == 'Fungi':
            self.option('kegg_database', 'Fungi')
        elif self.option('kegg_database') == 'Protist':
            self.option('kegg_database', 'Protists')
        if self.option('rrna_stop'):
            if not isinstance(self.option('rrna_sample_percent'), float):
                raise OptionError('核糖体判断中止条件的样本比例值应为浮点数', code='13700319')
            if not isinstance(self.option('rrna_ratio'), float):
                raise OptionError('核糖体判断中止条件的阈值比例值应为浮点数', code='13700320')
        if self.option('mapping_stop'):
            if not isinstance(self.option('mapping_sample_percent'), float):
                raise OptionError('比对结果判断中止条件的样本比例值应为浮点数', code='13700321')
            if not isinstance(self.option('mapping_ratio'), float):
                raise OptionError('比对结果判断中止条件的阈值比例值应为浮点数', code='13700322')
        if self.option('pair_table').is_set:
            if self.option('diff_method').lower() not in ['deseq2', 'edger', 'limma']:
                raise OptionError('做配对分析时，需要从DESeq2, edgeR, limma三款软件中选择')
        for k, v in self.sheet.options().items():
            self.logger.debug('{} = {}'.format(k, v))
        else:
            return True

    def set_step(self, event):
        if 'start' in event['data'].keys():
            event['data']['start'].start()
        if 'end' in event['data'].keys():
            event['data']['end'].finish()
        self.step.update()

    @workfuncdeco
    def run(self):
        self.add_steps()
        super(RefrnaWorkflow, self).run()

    @workfuncdeco
    def add_steps(self):
        if self.option('datatype') == 'rawdata':
            if self.option('qc_soft') == 'fastp':
                self.step.add_steps('fastp_rna')
            elif self.option('qc_soft') == 'seqprep':
                self.step.add_steps('hiseq_qc')
        if "mapping" in self.analysis_content:
            self.step.add_steps('file_check', 'hiseq_reads_stat_raw', 'hiseq_reads_stat_use', 'rnaseq_mapping',
                                'map_assessment')
        if "annotation" in self.analysis_content:
            self.step.add_steps('annot_filter_ref', 'annot_class_beta_ref', 'gene_fa', 'detail')
            if self.option('is_assemble'):
                self.step.add_steps('refrna_assemble', 'annot_mapdb', 'annot_orfpfam', 'annot_filter_new',
                                    'annot_class_beta_new', 'annot_merge')
            else:
                self.step.add_steps('transcript_abstract')
        if "quantification" in self.analysis_content:
            self.step.add_steps('quant')
            if self.option('sample_num') == 'multiple':
                group_spname = self.option("group_table").get_group_spname()
                group_snum = [len(group_spname[g]) for g in group_spname]
                min_group_num = min(group_snum)
                if self.option('group_table').prop['sample_number'] > 2:
                    self.step.add_steps('exp_pca')
                    self.step.add_steps('exp_corr')
                if len(self.option("group_table").prop['group_dict']) > 1:
                    self.step.add_steps('exp_venn')
                if min_group_num >= 3:
                    self.step.add_steps('ellipse')
        if "other" in self.analysis_content:
            if self.option('sample_num') == 'multiple':
                self.step.add_steps('diffexp')
            if self.option('is_snp') == 'True':
                if self.option('snp_method').lower() == 'samtools':
                    self.step.add_steps('sam_rna')
                elif self.option('snp_method').lower() == 'gatk':
                    self.step.add_steps('snp_rna')
                elif self.option('snp_method').lower() == 'sentieon':
                    self.step.add_steps('call_snp_indel')
            if self.option('is_as') == 'True':
                self.step.add_steps('rmats')
        self.run_stage_1()

    @workfuncdeco
    def run_stage_1(self):
        self.file_check = self.add_tool('ref_rna_v2.file_check')
        self.hiseq_reads_stat_use = self.add_module('ref_rna_v2.hiseq_reads_stat')
        if self.option('datatype') == 'rawdata':
            self.hiseq_reads_stat_raw = self.add_module('ref_rna_v2.hiseq_reads_stat')
            self.on_rely([self.hiseq_reads_stat_raw, self.hiseq_reads_stat_use], self.check_rrna)
        self.run_file_check()

    def run_file_check(self):
        if self.option('datatype') == 'rawdata':
            fastq_dir = self.option('fastq_dir')
        elif self.option('datatype') == 'cleandata':
            fastq_dir = self.option('qc_dir')
        opts = {
            'fq_type': self.option('fq_type'),
            'fastq_dir': fastq_dir,
            'in_gtf': self.ref_gtf,
            'sample_num': self.option('sample_num')
        }
        if self.option('control_file').is_set:
            opts.update({'control_file': self.option('control_file')})
        if self.option('group_table').is_set:
            opts.update({'group_table': self.option('group_table')})
        self.file_check.set_options(opts)
        self.file_check.on('start', self.set_step, {'start': self.step.file_check})
        self.file_check.on('end', self.set_step, {'end': self.step.file_check})
        if self.option('datatype') == 'rawdata':
            self.file_check.on('end', self.run_hiseq_reads_stat_raw)
            if self.option('qc_soft') == 'fastp':
                self.file_check.on('end', self.run_fastp_rna)
            elif self.option('qc_soft') == 'seqprep':
                self.file_check.on('end', self.run_hiseq_qc)
        elif self.option('datatype') == 'cleandata':
            self.file_check.on('end', self.run_hiseq_reads_stat_use)
        self.file_check.run()

    def run_hiseq_reads_stat_raw(self):
        if self.option('quality_score_system').endswith('33'):
            quality = 33
        elif self.option('quality_score_system').endswith('64'):
            quality = 64
        self.hiseq_reads_stat_raw.set_options({
            'fastq_dir': self.option('fastq_dir'),
            'fq_type': self.option('fq_type'),
            'quality': quality
        })
        self.hiseq_reads_stat_raw.on('start', self.set_step, {'start': self.step.hiseq_reads_stat_raw})
        self.hiseq_reads_stat_raw.on('end', self.set_step, {'end': self.step.hiseq_reads_stat_raw})
        self.hiseq_reads_stat_raw.on('end', self.set_output, 'hiseq_reads_stat_raw')
        self.hiseq_reads_stat_raw.run()

    def run_fastp_rna(self):
        self.fastp_rna = self.add_module('datasplit.fastp_rna')
        fq_dir = self.option('fastq_dir').path
        sample_path = os.path.join(fq_dir, 'abs.list.txt')
        open(sample_path, 'w').writelines(
            '{}/{}'.format(fq_dir, line) for line in open(os.path.join(fq_dir, 'list.txt'))
        )
        if self.option('fq_type') == "PE":
            self.fastp_rna.set_options({
                'sample_path': sample_path,
                'fq_type': self.option('fq_type'),
                'length_required': self.option('length_required'),
                'quality_score_system': self.option('quality_score_system'),
                'adapter_sequence': self.option('adapter_a'),
                'adapter_sequence_r2': self.option('adapter_b')
            })
        else:
            self.fastp_rna.set_options({
                'sample_path': sample_path,
                'fq_type': self.option('fq_type'),
                'length_required': self.option('length_required'),
                'quality_score_system': self.option('quality_score_system'),
                'adapter_sequence_s': self.option('adapter_a'),
            })
        self.fastp_rna.on('start', self.set_step, {'start': self.step.fastp_rna})
        self.fastp_rna.on('end', self.set_step, {'end': self.step.fastp_rna})
        self.fastp_rna.on('end', self.set_output, 'fastp_rna')
        self.fastp_rna.on('end', self.run_hiseq_reads_stat_use)
        self.fastp_rna.run()

    def run_hiseq_qc(self):
        self.hiseq_qc = self.add_module('ref_rna_v2.hiseq_qc')
        if self.option('fq_type') == "PE":
            self.hiseq_qc.set_options({
                'fastq_dir': self.option('fastq_dir'),
                'fq_type': self.option('fq_type'),
                'quality_score_system': self.option('quality_score_system'),
                'adapter_a': self.option('adapter_a'),
                'adapter_b': self.option('adapter_b')
            })
        else:
            self.hiseq_qc.set_options({
                'fastq_dir': self.option('fastq_dir'),
                'fq_type': self.option('fq_type'),
                'quality_score_system': self.option('quality_score_system'),
                'adapter_a': self.option('adapter_a'),
            })
        self.hiseq_qc.on('start', self.set_step, {'start': self.step.hiseq_qc})
        self.hiseq_qc.on('end', self.set_step, {'end': self.step.hiseq_qc})
        self.hiseq_qc.on('end', self.set_output, 'hiseq_qc')
        self.hiseq_qc.on('end', self.run_hiseq_reads_stat_use)
        self.hiseq_qc.run()

    def run_hiseq_reads_stat_use(self):
        if self.option('quality_score_system').endswith('33'):
            quality = 33
        elif self.option('quality_score_system').endswith('64'):
            quality = 64
        if self.option('datatype') == 'rawdata':
            if self.option('qc_soft') == 'fastp':
                fastq_dir = self.fastp_rna.option('sickle_dir')
            elif self.option('qc_soft') == 'seqprep':
                fastq_dir = self.hiseq_qc.option('sickle_dir')
        elif self.option('datatype') == 'cleandata':
            fastq_dir = self.option('qc_dir')
        self.hiseq_reads_stat_use.set_options({
            'fastq_dir': fastq_dir,
            'fq_type': self.option('fq_type'),
            'quality': quality,
            'dup': True,
            'rfam': True
        })
        self.hiseq_reads_stat_use.on('start', self.set_step, {'start': self.step.hiseq_reads_stat_use})
        self.hiseq_reads_stat_use.on('end', self.set_step, {'end': self.step.hiseq_reads_stat_use})
        self.hiseq_reads_stat_use.on('end', self.set_output, 'hiseq_reads_stat_use')
        if self.option('datatype') == 'cleandata':
            self.hiseq_reads_stat_use.on('end', self.check_rrna)
        self.hiseq_reads_stat_use.run()

    def check_rrna(self):
        if self.option('rrna_stop'):
            df = pd.read_table(os.path.join(self.hiseq_reads_stat_use.output_dir, 'stat_results'))
            rrna_sample_percent = len(
                [i for i in df.iloc[:, -1] if i > self.option('rrna_ratio')]
            ) / float(df.shape[0]) * 100
            if rrna_sample_percent > self.option('rrna_sample_percent'):
                self.stop('rrna')
            else:
                self.run_stage_2()
        else:
            self.run_stage_2()

    def run_stage_2(self):
        self.rnaseq_mapping = self.add_module('ref_rna_v2.rnaseq_mapping')
        self.run_rnaseq_mapping()

    def run_rnaseq_mapping(self):
        if self.option('datatype') == 'rawdata':
            if self.option('qc_soft') == 'fastp':
                fastq_dir = self.fastp_rna.option('sickle_dir')
            elif self.option('qc_soft') == 'seqprep':
                fastq_dir = self.hiseq_qc.option('sickle_dir')
        elif self.option('datatype') == 'cleandata':
            fastq_dir = self.option('qc_dir')
        self.rnaseq_mapping.set_options({
            'ref_genome': self.option('ref_genome'),
            'genome_version': self.genome_version,
            'genome_annot_version': self.annot_version,
            'mapping_method': self.option('align_method').lower(),
            'seq_method': self.option('fq_type'),
            'fastq_dir': fastq_dir,
            'assemble_method': self.option('assemble_method').lower(),
            'strand_specific': self.option('strand_specific')
        })
        self.rnaseq_mapping.on('start', self.set_step, {'start': self.step.rnaseq_mapping})
        self.rnaseq_mapping.on('end', self.set_step, {'end': self.step.rnaseq_mapping})
        self.rnaseq_mapping.on('end', self.set_output, 'rnaseq_mapping')
        self.rnaseq_mapping.on('end', self.check_mapping)
        self.rnaseq_mapping.run()

    def check_mapping(self):
        if self.option('mapping_stop'):
            if self.option('align_method').lower() == "hisat":
                n = 0.0
                for i, stat in enumerate(glob.glob(os.path.join(self.rnaseq_mapping.output_dir, 'stat/*.stat'))):
                    if float(open(stat).readlines()[-2].split('%')[0]) < float(self.option('mapping_ratio')):
                        n += 1
                else:
                    if n / (i + 1) * 100 > float(self.option('mapping_sample_percent')):
                        self.stop('mapping')
                    else:
                        self.run_stage_3()
            elif self.option('align_method').lower() == "tophat":
                n = 0.0
                for i, stat in enumerate(glob.glob(os.path.join(self.rnaseq_mapping.output_dir, 'stat/*.stat'))):
                    if float(open(stat).readlines()[8].split('%')[0]) < float(self.option('mapping_ratio')):
                        n += 1
                else:
                    if n / (i + 1) * 100 > float(self.option('mapping_sample_percent')):
                        self.stop('mapping')
                    else:
                        self.run_stage_3()
            elif self.option('align_method').lower() == "star":
                n = 0.0
                i = 0
                stat = os.path.join(self.rnaseq_mapping.output_dir, 'Comparison_results')
                with open(stat, "r") as f1:
                    header = f1.readline()
                    for line in f1:
                        i += 1
                        if float(line.split("(")[1].split('%')[0]) < float(self.option('mapping_ratio')):
                            n += 1
                    else:
                        if n / i * 100 > float(self.option('mapping_sample_percent')):
                            self.stop('mapping')
                        else:
                            self.run_stage_3()
        else:
            self.run_stage_3()

    def run_stage_3(self):
        if "mapping" in self.analysis_content:
            if self.option('datatype') == 'rawdata':
                if self.option('qc_soft') == 'fastp':
                    self.fq_list = self.fastp_rna.option('fq_list').path
                elif self.option('qc_soft') == 'seqprep':
                    self.fq_list = self.hiseq_qc.option('fq_list').path
            else:
                dct = dict()
                fq_path = self.option('qc_dir').path
                for line in open(os.path.join(fq_path, 'list.txt')):
                    items = line.strip().split('\t')
                    if items[1] in dct:
                        dct[items[1]][items[2]] = os.path.join(fq_path, items[0])
                        flag = 1
                    else:
                        dct[items[1]] = {items[2]: os.path.join(fq_path, items[0])}
                        flag = 0
                else:
                    self.fq_list = os.path.join(fq_path, 'fq_list.txt')
                    open(self.fq_list, 'w').writelines(['{}\t{l}\t{r}\n'.format(k, **v) for k, v in dct.items()] if flag \
                                                           else ['{}\t{s}\n'.format(k, **v) for k, v in dct.items()])
            self.map_assessment = self.add_module('ref_rna_v3.map_assessment')
            self.rely = [self.map_assessment]
        if "annotation" in self.analysis_content:
            self.annot_filter_ref = self.add_module('ref_rna_v2.annot_filter')
            self.annot_class_beta_ref = self.add_module('ref_rna_v2.annot_class_beta')
            self.gene_fa = self.add_tool('ref_rna_v2.gene_fa')
            self.detail = self.add_tool('ref_rna_v3.database.detail')
            self.annot_merge = self.add_tool('ref_rna_v2.annotation.annot_merge')
            self.rely.append(self.annot_merge)
            if self.option('is_assemble'):
                self.refrna_assemble = self.add_module('ref_rna_v2.refrna_assemble')
                self.annot_mapdb = self.add_module('ref_rna_v2.annot_mapdb')
                self.annot_orfpfam = self.add_module('ref_rna_v2.annot_orfpfam')
                self.annot_filter_new = self.add_module('ref_rna_v2.annot_filter')
                self.annot_class_beta_new = self.add_module('ref_rna_v2.annot_class_beta')
                self.rely.append(self.refrna_assemble)
                self.on_rely([self.annot_mapdb, self.annot_orfpfam], self.run_annot_filter_new)
                self.on_rely([self.gene_fa, self.annot_orfpfam], self.run_detail)
                self.on_rely([self.annot_class_beta_ref, self.annot_class_beta_new], self.run_annot_merge)
                self.run_refrna_assemble()
            else:
                self.transcript_abstract = self.add_tool('ref_rna_v2.transcript_abstract')
                self.run_transcript_abstract()
                self.on_rely([self.annot_class_beta_ref, self.detail], self.run_annot_merge)
        if "quantification" in self.analysis_content:
            self.quant = self.add_module('ref_rna_v2.quant')
            self.rely.append(self.quant)
            if self.option('sample_num') == 'multiple':
                group_spname = self.option("group_table").get_group_spname()
                group_snum = [len(group_spname[g]) for g in group_spname]
                min_group_num = min(group_snum)
                group_dict = self.option("group_table").prop['group_dict']
                if len(group_dict) > 1:
                    self.exp_venn = self.add_tool('ref_rna_v2.exp_venn')
                    self.rely.append(self.exp_venn)
                if self.option('group_table').prop['sample_number'] > 2:
                    self.exp_pca = self.add_tool('ref_rna_v2.exp_pca')
                    self.exp_corr = self.add_tool('ref_rna_v2.exp_corr')
                    self.rely.extend([self.exp_corr, self.exp_pca])
                if min_group_num >= 3:
                    self.ellipse = self.add_tool('graph.ellipse')
                    self.rely.append(self.ellipse)

        if "other" in self.analysis_content:
            if self.option('sample_num') == 'multiple':
                self.diffexp = self.add_tool('ref_rna_v3.batch.diffexp_batch')
                self.rely.append(self.diffexp)
            if self.option('is_snp') == 'True':
                if self.option('snp_method').lower() == 'samtools':
                    self.sam_rna = self.add_module('ref_rna_v3.sam_rna')
                    self.rely.append(self.sam_rna)
                elif self.option('snp_method').lower() == 'gatk':
                    self.snp_rna = self.add_module('ref_rna_v3.snp_rna')
                    self.rely.append(self.snp_rna)
                elif self.option('snp_method').lower() == 'sentieon':
                    self.call_snp_indel = self.add_module('ref_rna_v3.call_snp_indel_sentieon')
                    self.rely.append(self.call_snp_indel)
            if self.option('is_as') == 'True':
                self.rmats = self.add_module('ref_rna_v3.rmats')
                self.rely.append(self.rmats)
        self.logger.info("analysis_content: {}".format(self.analysis_content))
        self.logger.info("self.rely: {}".format(self.rely))
        self.on_rely(self.rely, self.set_db)
        if "mapping" in self.analysis_content:
            self.run_map_assessment()
        if "annotation" in self.analysis_content:
            self.run_annot_filter_ref()

    def run_map_assessment(self):
        self.map_assessment.set_options({
            'bam': self.rnaseq_mapping.option('bam_output'),
            'bed': self.file_check.option('bed'),
            'analysis': self.option('map_assess_method')
        })
        self.map_assessment.on('start', self.set_step, {'start': self.step.map_assessment})
        self.map_assessment.on('end', self.set_step, {'end': self.step.map_assessment})
        self.map_assessment.on('end', self.set_output, 'map_assessment')
        self.map_assessment.run()

    def run_annot_filter_ref(self):
        self.annot_filter_ref.set_options({
            'blast_nr_xml': os.path.join(self.ref_annot_dir, 'annot_mapdb/nr/blast.xml'),
            'blast_eggnog_xml': os.path.join(self.ref_annot_dir, 'annot_mapdb/eggnog/blast.xml'),
            'blast_kegg_xml': os.path.join(self.ref_annot_dir, 'annot_mapdb/kegg/blast.xml'),
            'blast_swissprot_xml': os.path.join(self.ref_annot_dir, 'annot_mapdb/swissprot/blast.xml'),
            'pfam_domain': os.path.join(self.ref_annot_dir, 'annot_orfpfam/pfam_domain'),
            'blast2go_annot': os.path.join(self.ref_annot_dir, 'annot_mapdb/GO/blast2go_merge.xls'),
            'nr_evalue': self.option('nr_evalue'),
            'nr_identity': self.option('nr_identity'),
            'nr_similarity': self.option('nr_similarity'),
            'swissprot_evalue': self.option('swissprot_evalue'),
            'swissprot_identity': self.option('swissprot_identity'),
            'swissprot_similarity': self.option('swissprot_similarity'),
            'eggnog_evalue': self.option('cog_evalue'),
            'eggnog_identity': self.option('cog_identity'),
            'eggnog_similarity': self.option('cog_similarity'),
            'kegg_evalue': self.option('kegg_evalue'),
            'kegg_identity': self.option('kegg_identity'),
            'kegg_similarity': self.option('kegg_similarity'),
            'pfam_evalue': self.option('pfam_evalue')
        })
        self.annot_filter_ref.on('start', self.set_step, {'start': self.step.annot_filter_ref})
        self.annot_filter_ref.on('end', self.set_step, {'end': self.step.annot_filter_ref})
        self.annot_filter_ref.on('end', self.set_output, 'annot_filter_ref')
        self.annot_filter_ref.on('end', self.run_annot_class_beta_ref)
        self.annot_filter_ref.run()

    def run_annot_class_beta_ref(self):
        self.step.add_steps('annot_class_beta_ref')
        options = {
            'type': 'ref',
            'gtf': self.file_check.option('gtf').path,
            'fasta': self.ref_genome,
            'g2t2p': self.g2t2p,
            'des': self.des,
            'des_type': self.des_type,
            'enterz': self.entrez,
            'blast_nr_xml': os.path.join(self.annot_filter_ref.output_dir, 'nr/blast.xml.filter.xml'),
            'blast_kegg_xml': os.path.join(self.annot_filter_ref.output_dir, 'kegg/blast.xml.filter.xml'),
            'known_ko': self.known_ko,
            'taxonomy': self.option('kegg_database'),
            'link_bgcolor': 'yellow',
            'png_bgcolor': 'FFFF00',
            'blast_eggnog_xml': os.path.join(self.annot_filter_ref.output_dir, 'eggnog/blast.xml.filter.xml'),
            'blast_swissprot_xml': os.path.join(self.annot_filter_ref.output_dir, 'swissprot/blast.xml.filter.xml'),
            'pfam_domain': os.path.join(self.annot_filter_ref.output_dir, 'pfam/pfam_domain.filter.xls'),
            'blast2go_annot': os.path.join(self.annot_filter_ref.output_dir, 'go/blast2go_merge.xls.filter.xls'),
            'kegg_version': self.option('kegg_version'),
            'kegg_subtax1': self.option('kegg_subtax1'),
            'kegg_subtax2': self.option('kegg_subtax2'),
            'kegg_species': self.option('kegg_specific')
        }
        if os.path.exists(os.path.join(self.ref_annot_dir, 'annot_class/kegg/kegg_table.xls')):
            options.update({"known_ko_merge": os.path.join(self.ref_annot_dir, 'annot_class/kegg/kegg_table.xls')})
        self.annot_class_beta_ref.set_options(options)
        self.annot_class_beta_ref.on('start', self.set_step, {'start': self.step.annot_class_beta_ref})
        self.annot_class_beta_ref.on('end', self.set_step, {'end': self.step.annot_class_beta_ref})
        self.annot_class_beta_ref.on('end', self.set_output, 'annot_class_beta_ref')
        self.annot_class_beta_ref.run()

    def run_refrna_assemble(self):
        self.step.add_steps('refrna_assemble')
        if self.option('strand_specific'):
            fr_stranded = 'fr-stranded'
            if self.option('strand_dir').startswith('R'):
                strand_direct = 'firststrand'
            elif self.option('strand_dir').startswith('F'):
                strand_direct = 'secondstrand'
        else:
            fr_stranded = 'fr-unstranded'
            strand_direct = 'none'
        self.refrna_assemble.set_options({
            'sample_bam_dir': self.rnaseq_mapping.option('bam_output'),
            'assemble_method': self.option('assemble_method'),
            'ref_gtf': self.file_check.option('gtf'),
            'ref_fa': self.ref_genome,
            'fr_stranded': fr_stranded,
            'strand_direct': strand_direct
        })
        self.refrna_assemble.on('start', self.set_step, {'start': self.step.refrna_assemble})
        self.refrna_assemble.on('end', self.set_step, {'end': self.step.refrna_assemble})
        self.refrna_assemble.on('end', self.set_output, 'refrna_assemble')
        self.refrna_assemble.on('end', self.run_gene_fa)
        self.refrna_assemble.on('end', self.run_annot_mapdb)
        self.refrna_assemble.on('end', self.run_annot_orfpfam)
        if "quantification" in self.analysis_content:
            self.refrna_assemble.on('end', self.run_quant)
        if self.option('is_snp') == 'True' and 'other' in self.analysis_content:
            if self.option('snp_method').lower() == 'samtools':
                self.refrna_assemble.on('end', self.run_sam_rna)
            elif self.option('snp_method').lower() == 'gatk':
                self.refrna_assemble.on('end', self.run_snp_rna)
            elif self.option('snp_method').lower() == 'sentieon':
                self.refrna_assemble.on('end', self.run_call_snp_indel)
        if self.option('is_as') == 'True' and 'other' in self.analysis_content:
            self.refrna_assemble.on('end', self.run_rmats)
        self.refrna_assemble.run()

    def run_transcript_abstract(self):
        self.transcript_abstract.set_options({
            'ref_genome': self.ref_genome,
            'ref_genome_gtf': self.ref_gtf
        })
        self.transcript_abstract.on('start', self.set_step, {'start': self.step.transcript_abstract})
        self.transcript_abstract.on('end', self.set_step, {'end': self.step.transcript_abstract})
        self.transcript_abstract.on('end', self.set_output, 'transcript_abstract')
        self.transcript_abstract.on('end', self.run_gene_fa)
        self.transcript_abstract.on('end', self.run_quant)
        if self.option('sample_num') == 'multiple':
            if self.option('is_as') == 'True' and 'other' in self.analysis_content:
                self.transcript_abstract.on('end', self.run_rmats)
        if self.option('is_snp') == 'True' and 'other' in self.analysis_content:
            if self.option('snp_method').lower() == 'samtools':
                self.transcript_abstract.on('end', self.run_sam_rna)
            elif self.option('snp_method').lower() == 'gatk':
                self.transcript_abstract.on('end', self.run_snp_rna)
            elif self.option('snp_method').lower() == 'sentieon':
                self.transcript_abstract.on('end', self.run_call_snp_indel)
        self.transcript_abstract.run()

    def run_gene_fa(self):
        self.step.add_steps('gene_fa')
        if self.option('is_assemble'):
            ref_new_gtf = self.refrna_assemble.option('ref_and_new_gtf').path
        else:
            ref_new_gtf = self.ref_gtf
        self.gene_fa.set_options({
            'ref_new_gtf': ref_new_gtf,
            'ref_genome_custom': self.ref_genome
        })
        self.gene_fa.on('start', self.set_step, {'start': self.step.gene_fa})
        self.gene_fa.on('end', self.set_step, {'end': self.step.gene_fa})
        self.gene_fa.on('end', self.set_output, 'gene_fa')
        if not self.option('is_assemble'):
            self.gene_fa.on('end', self.run_detail)
        self.gene_fa.run()

    def run_detail(self):
        self.step.add_steps('detail')
        opts = {
            'gene_fa': self.gene_fa.option('gene_fa').path,
            'biomart_file': self.des,
            'biomart_type': self.des_type,
            'known_cds': self.known_cds,
            'known_pep': self.known_pep
        }
        if self.option('is_assemble'):
            opts.update({
                'txpt_fa': self.refrna_assemble.option('all_transcripts_fa').path,
                't2g': self.refrna_assemble.option('trans2gene').path,
                'novel_cds': os.path.join(self.annot_orfpfam.output_dir, 'new_transcripts.fa.transdecoder.cds'),
                'novel_pep': os.path.join(self.annot_orfpfam.output_dir, 'new_transcripts.fa.transdecoder.pep')
            })
        else:
            opts.update({
                'txpt_fa': self.transcript_abstract.option('trans_fa').path,
                't2g': self.transcript_abstract.option('trans2gene').path
            })
        self.detail.set_options(opts)
        self.detail.on('start', self.set_step, {'start': self.step.detail})
        self.detail.on('end', self.set_step, {'end': self.step.detail})
        self.detail.on('end', self.set_output, 'detail')
        self.detail.run()

    def run_annot_mapdb(self):
        self.step.add_steps('annot_mapdb')
        self.annot_mapdb.set_options({
            'query': self.refrna_assemble.option('new_transcripts_fa'),
            'nr_db': self.option('nr_database'),
            'kegg_version': self.option('kegg_version')
        })
        self.annot_mapdb.on('start', self.set_step, {'start': self.step.annot_mapdb})
        self.annot_mapdb.on('end', self.set_step, {'end': self.step.annot_mapdb})
        self.annot_mapdb.on('end', self.set_output, 'annot_mapdb')
        self.annot_mapdb.run()

    def run_annot_orfpfam(self):
        self.step.add_steps('annot_orfpfam')
        self.annot_orfpfam.set_options({
            'fasta': self.refrna_assemble.option('new_transcripts_fa'),
            'gtf': self.refrna_assemble.option('new_transcripts_gtf')
        })
        self.annot_orfpfam.on('start', self.set_step, {'start': self.step.annot_orfpfam})
        self.annot_orfpfam.on('end', self.set_step, {'end': self.step.annot_orfpfam})
        self.annot_orfpfam.on('end', self.set_output, 'annot_orfpfam')
        self.annot_orfpfam.run()

    def run_annot_filter_new(self):
        self.step.add_steps('annot_filter_new')
        self.annot_filter_new.set_options({
            'blast_nr_xml': os.path.join(self.annot_mapdb.output_dir, 'nr/blast.xml'),
            'blast_eggnog_xml': os.path.join(self.annot_mapdb.output_dir, 'eggnog/blast.xml'),
            'blast_kegg_xml': os.path.join(self.annot_mapdb.output_dir, 'kegg/blast.xml'),
            'blast_swissprot_xml': os.path.join(self.annot_mapdb.output_dir, 'swissprot/blast.xml'),
            'pfam_domain': os.path.join(self.annot_orfpfam.output_dir, 'pfam_domain'),
            'blast2go_annot': os.path.join(self.annot_mapdb.output_dir, 'GO/blast2go_merge.xls'),
            'nr_evalue': self.option('nr_evalue'),
            'nr_identity': self.option('nr_identity'),
            'nr_similarity': self.option('nr_similarity'),
            'swissprot_evalue': self.option('swissprot_evalue'),
            'swissprot_identity': self.option('swissprot_identity'),
            'swissprot_similarity': self.option('swissprot_similarity'),
            'eggnog_evalue': self.option('cog_evalue'),
            'eggnog_identity': self.option('cog_identity'),
            'eggnog_similarity': self.option('cog_similarity'),
            'kegg_evalue': self.option('kegg_evalue'),
            'kegg_identity': self.option('kegg_identity'),
            'kegg_similarity': self.option('kegg_similarity'),
            'pfam_evalue': self.option('pfam_evalue')
        })
        self.annot_filter_new.on('start', self.set_step, {'start': self.step.annot_filter_new})
        self.annot_filter_new.on('end', self.set_step, {'end': self.step.annot_filter_new})
        self.annot_filter_new.on('end', self.set_output, 'annot_filter_new')
        self.annot_filter_new.on('end', self.run_annot_class_beta_new)
        self.annot_filter_new.run()

    def run_annot_class_beta_new(self):
        self.step.add_steps('annot_class_beta_new')
        self.annot_class_beta_new.set_options({
            'type': 'new',
            'gene2trans': os.path.join(self.annot_orfpfam.output_dir, 'all_tran2gen.txt'),
            'des': self.des,
            'des_type': self.des_type,
            'enterz': self.entrez,
            'blast_nr_xml': os.path.join(self.annot_filter_new.output_dir, 'nr/blast.xml.filter.xml'),
            'blast_kegg_xml': os.path.join(self.annot_filter_new.output_dir, 'kegg/blast.xml.filter.xml'),
            'taxonomy': self.option('kegg_database'),
            'link_bgcolor': 'green',
            'png_bgcolor': '00CD00',
            'blast_eggnog_xml': os.path.join(self.annot_filter_new.output_dir, 'eggnog/blast.xml.filter.xml'),
            'blast_swissprot_xml': os.path.join(self.annot_filter_new.output_dir, 'swissprot/blast.xml.filter.xml'),
            'pfam_domain': os.path.join(self.annot_filter_new.output_dir, 'pfam/pfam_domain.filter.xls'),
            'blast2go_annot': os.path.join(self.annot_filter_new.output_dir, 'go/blast2go_merge.xls.filter.xls'),
            'kegg_version': self.option('kegg_version'),
            'kegg_subtax1': self.option('kegg_subtax1'),
            'kegg_subtax2': self.option('kegg_subtax2'),
            'kegg_species': self.option('kegg_specific')
        })
        self.annot_class_beta_new.on('start', self.set_step, {'start': self.step.annot_class_beta_new})
        self.annot_class_beta_new.on('end', self.set_step, {'end': self.step.annot_class_beta_new})
        self.annot_class_beta_new.on('end', self.set_output, 'annot_class_beta_new')
        self.annot_class_beta_new.run()

    def run_annot_merge(self):
        self.step.add_steps('annot_merge')
        opts = {
            'ref_class_dir': self.annot_class_beta_ref.output_dir,
            'is_assemble': self.option('is_assemble'),
            'kegg_version': self.option('kegg_version')
        }
        if self.option('is_assemble'):
            opts.update({
                'new_class_dir': self.annot_class_beta_new.output_dir,
                'new_mapdb_dir': self.annot_mapdb.output_dir
            })
        self.annot_merge.set_options(opts)
        self.annot_merge.on('start', self.set_step, {'start': self.step.annot_merge})
        self.annot_merge.on('end', self.set_step, {'end': self.step.annot_merge})
        self.annot_merge.on('end', self.set_output, 'annot_merge')
        self.annot_merge.run()

    def run_quant(self):
        if self.option('datatype') == 'rawdata':
            if self.option('qc_soft') == 'fastp':
                fastq = self.fastp_rna.option('fq_list').path
            elif self.option('qc_soft') == 'seqprep':
                fastq = self.hiseq_qc.option('fq_list').path
        elif self.option('datatype') == 'cleandata':
            fastq = self.fq_list
        if self.option('strand_specific'):
            if self.option('strand_dir').startswith('R'):
                if self.option('fq_type') == 'PE':
                    libtype = 'rf'
                elif self.option('fq_type') == 'SE':
                    libtype = 'r'
            elif self.option('strand_dir').startswith('F'):
                if self.option('fq_type') == 'PE':
                    libtype = 'fr'
                elif self.option('fq_type') == 'SE':
                    libtype = 'f'
        else:
            libtype = None
        if self.option('is_assemble'):
            transcriptome = self.refrna_assemble.option('all_transcripts_fa')
            t2g = self.refrna_assemble.option('trans2gene').path
        else:
            transcriptome = self.transcript_abstract.option('trans_fa')
            t2g = self.transcript_abstract.option('trans2gene').path
        self.quant.set_options({
            'fastq': fastq,
            'method': self.option('express_method'),
            'libtype': libtype,
            'transcriptome': transcriptome,
            't2g': t2g,
            'ref_gtf': self.file_check.option('gtf').path
        })
        self.quant.on('start', self.set_step, {'start': self.step.quant})
        self.quant.on('end', self.set_step, {'end': self.step.quant})
        self.quant.on('end', self.set_output, 'quant')
        if self.option('sample_num') == 'multiple':
            if len(self.option('group_table').prop['group_dict']) > 1:
                self.quant.on('end', self.run_exp_venn)
            if self.option('group_table').prop['sample_number'] > 2:
                self.quant.on('end', self.run_exp_pca)
                self.quant.on('end', self.run_exp_corr)
            if "other" in self.analysis_content:
                self.quant.on('end', self.run_diffexp)
        self.quant.run()

    def run_exp_venn(self):
        if self.option('exp_way').lower() == 'fpkm':
            express_matrix = self.quant.option('ref_gene_fpkm').path
        else:
            express_matrix = self.quant.option('ref_gene_tpm').path
        group_dict = self.option('group_table').prop['group_dict']
        if len(group_dict) <= 6:
            group_table = self.option('group_table').path
        else:
            group_table = '{}.6'.format(self.option('group_table').path)
            lines = ['#sample\tgroup\n']
            for i, (g, ss) in enumerate(group_dict.items()):
                if i < 6:
                    lines.extend('{}\t{}\n'.format(s, g) for s in ss)
            else:
                open(group_table, 'w').writelines(lines)
        self.exp_venn.set_options({
            'express_matrix': express_matrix,
            'group_table': group_table,
            'threshold': 1
        })
        self.exp_venn.on('start', self.set_step, {'start': self.step.exp_venn})
        self.exp_venn.on('end', self.set_step, {'end': self.step.exp_venn})
        self.exp_venn.on('end', self.set_output, 'exp_venn')
        self.exp_venn.run()

    def run_exp_pca(self):
        if self.option('exp_way').lower() == 'fpkm':
            exp = self.quant.option('ref_gene_fpkm').path
        else:
            exp = self.quant.option('ref_gene_tpm').path
        self.exp_pca.set_options({'exp': exp})
        self.exp_pca.on('start', self.set_step, {'start': self.step.exp_pca})
        self.exp_pca.on('end', self.set_step, {'end': self.step.exp_pca})
        self.exp_pca.on('end', self.set_output, 'exp_pca')
        if hasattr(self, 'ellipse'):
            self.exp_pca.on('end', self.run_ellipse)
        self.exp_pca.run()

    def run_ellipse(self):
        self.ellipse.set_options({
            'analysis': 'pca',
            'group_table': self.option('group_table').prop['path'],
            'pc_table': os.path.join(self.exp_pca.output_dir, 'PCA.xls'),
        })
        self.ellipse.on('start', self.set_step, {'start': self.step.ellipse})
        self.ellipse.on('end', self.set_step, {'end': self.step.ellipse})
        self.ellipse.on('end', self.set_output, 'exp_pca')
        self.ellipse.run()

    def run_exp_corr(self):
        if self.option('exp_way').lower() == 'fpkm':
            exp = self.quant.option('ref_gene_fpkm').path
        else:
            exp = self.quant.option('ref_gene_tpm').path
        self.exp_corr.set_options({'exp': exp})
        self.exp_corr.on('start', self.set_step, {'start': self.step.exp_corr})
        self.exp_corr.on('end', self.set_step, {'end': self.step.exp_corr})
        self.exp_corr.on('end', self.set_output, 'exp_corr')
        self.exp_corr.run()

    def run_diffexp(self):
        if self.option('exp_way').lower() == 'fpkm':
            exp = self.quant.option('ref_gene_fpkm').path
        else:
            exp = self.quant.option('ref_gene_tpm').path
        opts = {
            'count': self.quant.option('ref_gene_count').path,
            'exp': exp,
            'group': self.option('group_table'),
            'cmp': self.option('control_file'),
            'fc': float(self.option('fc')),
            'method': self.option('diff_method'),
            'exp_type': self.option('exp_way'),
            'tpm_filter_threshold': self.option('filter_tpm')
        }

        if self.option("diff_method").lower() in ["degseq", "edger", "deseq2", 'limma']:
            opts.update({
                'pvalue_padjust': self.option('pvalue_padjust'),
                'pvalue': float(self.option('diff_fdr_ci')),
                'padjust_way': self.option('padjust_way'),
            })
            if self.option('pair_table').is_set:
                opts.update({'is_batch': True, 'has_batch': True, 'batch_matrix': self.option('pair_table').path})
            self.diffexp.set_options(opts)
        if self.option('diff_method').lower() == 'noiseq':
            opts.update({
                self.option('pvalue_padjust'): float(self.option('diff_fdr_ci')),
            })
            if self.option('pair_table').is_set:
                opts.update({'is_batch': True, 'has_batch': True, 'batch_matrix': self.option('pair_table').path})
            self.diffexp.set_options(opts)

        self.diffexp.on('start', self.set_step, {'start': self.step.diffexp})
        self.diffexp.on('end', self.set_step, {'end': self.step.diffexp})
        self.diffexp.on('end', self.set_output, 'diffexp')
        self.diffexp.run()

    def run_sam_rna(self):
        if self.option('is_assemble'):
            ref_gtf = self.refrna_assemble.option('ref_and_new_gtf').path
        else:
            ref_gtf = self.ref_gtf
        self.sam_rna.set_options({
            'ref_genome': 'customer_mode',
            'ref_genome_custom': self.ref_genome,
            'ref_gtf': ref_gtf,
            'bamlist': self.rnaseq_mapping.option('bamlist'),
            'des': self.des,
            'des_type': self.des_type
        })
        self.sam_rna.on('start', self.set_step, {'start': self.step.sam_rna})
        self.sam_rna.on('end', self.set_step, {'end': self.step.sam_rna})
        self.sam_rna.on('end', self.set_output, 'sam_rna')
        self.sam_rna.run()

    def run_snp_rna(self):
        if self.option('is_assemble'):
            ref_gtf = self.refrna_assemble.option('ref_and_new_gtf').path
        else:
            ref_gtf = self.ref_gtf
        self.snp_rna.set_options({
            'ref_genome_custom': self.ref_genome,
            'ref_gtf': ref_gtf,
            'in_bam': self.rnaseq_mapping.option('bam_output'),
            'des': self.des,
            'des_type': self.des_type
        })
        self.snp_rna.on('start', self.set_step, {'start': self.step.snp_rna})
        self.snp_rna.on('end', self.set_step, {'end': self.step.snp_rna})
        self.snp_rna.on('end', self.set_output, 'snp_rna')
        self.snp_rna.run()

    # def run_bam_realign(self):
    #     self.bam_realign.set_options({
    #         'fa_file': self.ref_genome,
    #         'in_bam': self.rnaseq_mapping.option('bam_output')
    #     })
    #     self.bam_realign.on('start', self.set_step, {'start': self.step.bam_realign})
    #     self.bam_realign.on('end', self.set_step, {'end': self.step.bam_realign})
    #     self.bam_realign.on('end', self.set_output, 'bam_realign')
    #     self.bam_realign.on('end', self.run_call_snp_indel)
    #     self.bam_realign.run()
    #
    # def run_call_snp_indel(self):
    #     if self.option('is_assemble'):
    #          ref_gtf = self.refrna_assemble.option('ref_and_new_gtf').path
    #     else:
    #         ref_gtf = self.ref_gtf
    #     self.call_snp_indel.set_options({
    #         'ref_fasta': self.ref_genome,
    #         'bam_list': os.path.join(self.rnaseq_mapping.output_dir,"bamlist"),
    #         'des': self.des,
    #         'des_type': self.des_type,
    #         'ref_gtf': ref_gtf,
    #         # 'analysis_format': "cram"
    #     })
    #     self.call_snp_indel.on('start', self.set_step, {'start': self.step.call_snp_indel})
    #     self.call_snp_indel.on('end', self.set_step, {'end': self.step.call_snp_indel})
    #     self.call_snp_indel.on('end', self.set_output, 'call_snp_indel')
    #     self.call_snp_indel.run()

    def run_call_snp_indel(self):
        if self.option('is_assemble'):
            ref_gtf = self.refrna_assemble.option('ref_and_new_gtf').path
        else:
            ref_gtf = self.ref_gtf
        opts = {
            'ref_fasta': self.ref_genome,
            'bam_list': os.path.join(self.rnaseq_mapping.output_dir, "bamlist"),
            'des': self.des,
            'des_type': self.des_type,
            'ref_gtf': ref_gtf,
            "align_method": self.option("align_method").lower()
        }
        large_chr = {"Pisum_sativum": ["v1a"], "Ginkgo_biloba": ["v1.0"],
                     "Triticum_turgidum": ["ensembl_45", "iwgsc_refseq"],
                     "Triticum_aestivum": ["ensemble_41", "iwgsc_refseqv1.1"]}
        if self.organism_name in large_chr and self.annot_version in large_chr[self.organism_name]:
            opts.update({"analysis_format": "cram"})
        self.call_snp_indel.set_options(opts)
        self.call_snp_indel.on('start', self.set_step, {'start': self.step.call_snp_indel})
        self.call_snp_indel.on('end', self.set_step, {'end': self.step.call_snp_indel})
        self.call_snp_indel.on('end', self.set_output, 'call_snp_indel')
        self.call_snp_indel.run()

    def run_rmats(self):
        self.step.add_steps('rmats')
        if self.option('fq_type') == 'PE':
            seq_type = 'paired'
        elif self.option('fq_type') == 'SE':
            seq_type = 'single'
        if self.option('strand_specific'):
            if self.option('strand_dir').startswith('R'):
                lib_type = 'fr-firststrand'
            elif self.option('strand_dir').startswith('F'):
                lib_type = 'fr-secondstrand'
        else:
            lib_type = 'fr-unstranded'
        if self.option('is_assemble'):
            input_gtf = self.refrna_assemble.option('ref_and_new_gtf')
        else:
            input_gtf = self.ref_gtf
        self.rmats.set_options({
            'control_table': self.option('control_file').path,
            'group_table': self.option('group_table').path,
            'bam_input': self.rnaseq_mapping.option('bam_output'),
            'input_gtf': input_gtf,
            'seq_type': seq_type,
            'lib_type': lib_type
        })
        self.rmats.on('start', self.set_step, {'start': self.step.rmats})
        self.rmats.on('end', self.set_step, {'end': self.step.rmats})
        self.rmats.on('end', self.set_output, 'rmats')
        self.rmats.run()

    def stop(self, reason):
        assert reason in ['rrna', 'mapping']
        self.IMPORT_REPORT_DATA = True
        self.IMPORT_REPORT_AFTER_END = False
        self.export_task_info()
        self.export_genome_info()
        if self.option('datatype') == 'rawdata':
            self.export_ref_rna_qc_before()
        self.export_ref_rna_qc_after()
        if reason == 'rrna':
            self.logger.warn('Workflow will stop because the rRNA ratio is not up to par')
        elif reason == 'mapping':
            self.export_ref_rna_qc_alignment()
            self.logger.warn('Workflow will stop because the alignment rate is not up to par')
        db = Config().get_mongo_client(mtype='project')[Config().get_mongo_dbname('project')]
        email = db['sg_task_email']
        email.update({'task_id': self.task_id}, {'$set': {'status': '5'}}, upsert=True)
        super(RefrnaWorkflow, self).end()

    def set_output(self, event):
        obj = event['bind_object']
        if event['data'] in ['fastp_rna', 'hiseq_qc']:
            self.move2outputdir(obj.output_dir, 'QC_stat')
        if event['data'] == 'hiseq_reads_stat_raw':
            self.move2outputdir(obj.output_dir, 'QC_stat/before_qc')
        if event['data'] == 'hiseq_reads_stat_use':
            self.move2outputdir(obj.output_dir, 'QC_stat/after_qc')
        if event['data'] == 'rnaseq_mapping':
            self.move2outputdir(obj.output_dir, 'mapping')
        if event['data'] == 'map_assessment':
            self.move2outputdir(obj.output_dir, 'map_qc')
        if event['data'] == 'refrna_assemble':
            self.move2outputdir(obj.output_dir, 'assembly')
        if event['data'] in ['sam_rna', 'snp_rna', 'call_snp_indel']:
            self.move2outputdir(obj.output_dir, 'snp')
        if event['data'] == 'quant':
            self.move2outputdir(obj.output_dir, 'express')
        if event['data'] == 'exp_pca':
            self.move2outputdir(obj.output_dir, 'exp_pca')
        if event['data'] == 'exp_corr':
            self.move2outputdir(obj.output_dir, 'exp_corr')
        if event['data'] == 'diffexp':
            self.move2outputdir(obj.output_dir, 'diffexpress')
        if event['data'] == 'rmats':
            self.move2outputdir(obj.output_dir, 'altersplicing')
        if event['data'] == 'annot_mapdb':
            self.move2outputdir(obj.output_dir, 'annot_mapdb')
        if event['data'] == 'annot_orfpfam':
            self.move2outputdir(obj.output_dir, 'annot_orfpfam')
        if event['data'] == 'annot_merge':
            self.move2outputdir(obj.output_dir, 'annot_merge')
        if event['data'] == 'transcript_abstract':
            self.move2outputdir(obj.output_dir, 'abstract_transcripts')
        if event['data'] == 'annot_class_beta_new':
            self.move2outputdir(obj.output_dir, 'annot_class_new')
        if event['data'] == 'run_annot_class_beta_ref':
            self.move2outputdir(obj.output_dir, 'annot_class_ref')
        if event['data'] == 'annot_filter_new':
            self.move2outputdir(obj.output_dir, 'annot_filter_new')
        if event['data'] == 'annot_filter_ref':
            self.move2outputdir(obj.output_dir, 'annot_filter_ref')

    @workfuncdeco
    def move2outputdir(self, olddir, newname):
        if not os.path.isdir(olddir):
            self.set_error('can not find source directory -> (%s)', variables=(olddir), code="13700337")
        newdir = os.path.join(self.output_dir, newname)
        if not os.path.exists(newdir):
            os.makedirs(newdir)
        allfiles = os.listdir(olddir)
        oldfiles = [os.path.join(olddir, i) for i in allfiles]
        newfiles = [os.path.join(newdir, i) for i in allfiles]
        for newfile in newfiles:
            if os.path.isfile(newfile) and os.path.exists(newfile):
                os.remove(newfile)
            elif os.path.isdir(newfile) and os.path.exists(newfile):
                shutil.rmtree(newfile)
        for i in range(len(allfiles)):
            self.move_file(oldfiles[i], newfiles[i])

    def move_file(self, src, dst):
        if os.path.isfile(src):
            os.link(src, dst)
        else:
            os.mkdir(dst)
            for file in os.listdir(src):
                old_path = os.path.join(src, file)
                new_path = os.path.join(dst, file)
                self.move_file(old_path, new_path)
        # self.logger.info('succeed in moving {} to {}'.format(src, dst))

    def set_db(self):
        self.IMPORT_REPORT_DATA = True
        self.IMPORT_REPORT_AFTER_END = False
        self.stop_timeout_check()
        if "mapping" in self.analysis_content:
            self.export_task_info()
            self.export_genome_info()
            if self.option('datatype') == 'rawdata':
                self.export_ref_rna_qc_before()
            self.export_ref_rna_qc_after()
            self.export_ref_rna_qc_alignment()
            self.export_ref_rna_qc_assessment()
        if "annotation" in self.analysis_content:
            if self.option('is_assemble'):
                self.export_ref_assembly()
            self.export_annotation()
        if "quantification" in self.analysis_content:
            self.export_all_exp_matrix()
            if self.option('sample_num') == 'multiple':
                self.export_all_exp_distribution()
                if len(self.option('group_table').prop['group_dict']) > 1:
                    self.export_add_exp_venn()
                if self.option('group_table').prop['sample_number'] > 2:
                    self.export_all_exp_pca()
                    self.export_all_exp_corr()
                self.export_gene_detail()
        if "other" in self.analysis_content:
            if self.option('sample_num') == 'multiple':
                self.export_all_exp_diff()
                if self.option('is_as') == 'True':
                    self.export_rmats()
                    self.export_rmats_count()
            if self.option('is_snp') == 'True':
                self.export_snp()
        self.set_upload()

    @workfuncdeco
    def set_upload(self):
        if "quantification" in self.analysis_content:
            self.merge_annotation_exp_matrix()  # 表达量表增加注释信息
        if "other" in self.analysis_content:
            if self.option('sample_num') == 'multiple':
                self.merge_annotation_diffexp_matrix()  # 差异表达量表增加注释信息
        if self.option("upload_offline"):
            # 将质控结果文件和比对结果文件，传输至线下服务器
            self.offline_results = os.path.join(self.work_dir, self.task_id)
            if os.path.isdir(self.offline_results):
                shutil.rmtree(self.offline_results)
            os.mkdir(self.offline_results)
            # os.mkdir(os.path.join(self.offline_results, "QC"))
            # if self.option('qc_soft') == 'fastp':
            #     fastq = self.fastp_rna.option('fq_list').path
            # elif self.option('qc_soft') == 'seqprep':
            #     fastq = self.hiseq_qc.option('fq_list').path
            # with open(fastq, "r") as f:
            #     for line in f:
            #         items = line.strip().split("\t")[1:]
            #         for item in items:
            #             os.link(item, os.path.join(self.offline_results, "QC", os.path.basename(item)))
            os.mkdir(os.path.join(self.offline_results, "Mapping"))
            bam_files = glob.glob(self.rnaseq_mapping.output_dir + "/bam/*.bam")
            for bam in bam_files:
                os.link(bam, os.path.join(self.offline_results, "Mapping", os.path.basename(bam)))
        # 页面交互运行所需中间结果文件，不在结果目录中呈现
        self.intermediate_result = os.path.join(self.work_dir, 'intermediate_results')
        if os.path.isdir(self.intermediate_result):
            shutil.rmtree(self.intermediate_result)
        os.mkdir(self.intermediate_result)
        if "mapping" in self.analysis_content:
            ## AlignBam
            os.makedirs(os.path.join(self.intermediate_result, 'Align/AlignBam'))
            for b in os.listdir(os.path.join(self.output_dir, 'mapping/bam')):
                os.link(os.path.join(self.output_dir, 'mapping/bam', b),
                        os.path.join(self.intermediate_result, 'Align/AlignBam', b))
        if "annotation" in self.analysis_content:
            ## Annotation
            os.makedirs(os.path.join(self.intermediate_result, 'Annotation'))
            CopyFile().linkdir(os.path.join(self.output_dir, 'annot_merge'),
                               os.path.join(self.intermediate_result, 'Annotation'))
            rm_files = glob.glob(os.path.join(self.intermediate_result, 'Annotation/*/*/*/*.html.mark')) + \
                       glob.glob(os.path.join(self.intermediate_result, 'Annotation/*/*/*/*.KOs.txt')) + \
                       glob.glob(os.path.join(self.intermediate_result, 'Annotation/*/*/*/*.pdf')) + \
                       glob.glob(os.path.join(self.intermediate_result, 'Annotation/*/cog/summary.*.tsv')) + \
                       glob.glob(os.path.join(self.intermediate_result, 'Annotation/*/kegg/kegg_layer_*.xls'))
            for rm_file in rm_files:
                os.remove(rm_file)
            ## Transcripts
            os.makedirs(os.path.join(self.intermediate_result, 'Transcripts'))
            if not self.option('is_assemble'):
                os.link(os.path.join(self.transcript_abstract.work_dir, 'trans2gene'),
                        os.path.join(self.intermediate_result, 'Transcripts/trans2gene.txt'))
                os.link(os.path.join(self.transcript_abstract.work_dir, 'exons.fa'),
                        os.path.join(self.intermediate_result, 'Transcripts/all_transcripts.fa'))
            ## Stringtie for ASprofile
            if self.option('is_assemble'):
                gtf_dir = os.path.join(self.output_dir, 'assembly/Stringtie/')
                files = glob.glob(gtf_dir + '/' + '*.gtf')
                os.makedirs(os.path.join(self.intermediate_result, 'Stringtie'))
                for file in files:
                    os.link(file, os.path.join(self.intermediate_result, 'Stringtie', os.path.basename(file)))
                gtf_path = os.path.join(self.intermediate_result, 'Stringtie/')
                gtfs = os.listdir(gtf_path)
                gtf_sample = os.path.join(gtf_path, 'list')
                with open(gtf_sample, 'w') as file1:
                    for gtf in gtfs:
                        sample = re.findall(r'(.*?)_out', gtf)[0]
                        file1.write(gtf + '\t' + sample + '\n')

        if "quantification" in self.analysis_content:
            ## SequenceDatabase
            os.mkdir(os.path.join(self.intermediate_result, 'SequenceDatabase'))
            seq_db = self.detail.option('database').path
            os.link(seq_db, os.path.join(self.intermediate_result, 'SequenceDatabase', os.path.basename(seq_db)))
            ## Express
            os.makedirs(os.path.join(self.intermediate_result, 'Express/ExpAnnalysis'))
            if self.option('express_method') == 'RSEM':
                os.link(os.path.join(self.quant.output_dir, 'gene.tpm.matrix'),
                        os.path.join(self.intermediate_result, 'Express/ExpAnnalysis/gene.tpm.matrix.xls'))
                os.link(os.path.join(self.quant.output_dir, 'gene.fpkm.matrix'),
                        os.path.join(self.intermediate_result, 'Express/ExpAnnalysis/gene.fpkm.matrix.xls'))
                os.link(os.path.join(self.quant.output_dir, 'gene.count.matrix'),
                        os.path.join(self.intermediate_result, 'Express/ExpAnnalysis/gene.count.matrix.xls'))
                os.link(os.path.join(self.quant.output_dir, 'gene.tpm.matrix.annot.xls'),
                        os.path.join(self.intermediate_result, 'Express/ExpAnnalysis/gene.tpm.matrix.annot.xls'))
                os.link(os.path.join(self.quant.output_dir, 'gene.fpkm.matrix.annot.xls'),
                        os.path.join(self.intermediate_result, 'Express/ExpAnnalysis/gene.fpkm.matrix.annot.xls'))
                os.link(os.path.join(self.quant.output_dir, 'gene.count.matrix.annot.xls'),
                        os.path.join(self.intermediate_result, 'Express/ExpAnnalysis/gene.count.matrix.annot.xls'))
                if self.option('level').lower() == 'transcript':
                    os.link(os.path.join(self.quant.output_dir, 'transcript.tpm.matrix'),
                            os.path.join(self.intermediate_result, 'Express/ExpAnnalysis/transcript.tpm.matrix.xls'))
                    os.link(os.path.join(self.quant.output_dir, 'transcript.fpkm.matrix'),
                            os.path.join(self.intermediate_result, 'Express/ExpAnnalysis/transcript.fpkm.matrix.xls'))
                    os.link(os.path.join(self.quant.output_dir, 'transcript.count.matrix'),
                            os.path.join(self.intermediate_result, 'Express/ExpAnnalysis/transcript.count.matrix.xls'))
                    os.link(os.path.join(self.quant.output_dir, 'transcript.tpm.matrix.annot.xls'),
                            os.path.join(self.intermediate_result,
                                         'Express/ExpAnnalysis/transcript.tpm.matrix.annot.xls'))
                    os.link(os.path.join(self.quant.output_dir, 'transcript.fpkm.matrix.annot.xls'),
                            os.path.join(self.intermediate_result,
                                         'Express/ExpAnnalysis/transcript.fpkm.matrix.annot.xls'))
                    os.link(os.path.join(self.quant.output_dir, 'transcript.count.matrix.annot.xls'),
                            os.path.join(self.intermediate_result,
                                         'Express/ExpAnnalysis/transcript.count.matrix.annot.xls'))
        if "other" in self.analysis_content:
            if self.option('sample_num') == 'multiple':
                ## Diffexpress
                os.makedirs(os.path.join(self.intermediate_result, 'Diffexpress'))
                diff_output = self.diffexp.output_dir
                files = glob.glob(diff_output + '/' + '*_vs_*.normalize.xls') + glob.glob(
                    diff_output + '/' + '*_vs_*.sizeFactor.xls')
                for file in files:
                    os.link(file, os.path.join(self.intermediate_result, 'Diffexpress', os.path.basename(file)))
                ## SNP
                os.makedirs(os.path.join(self.intermediate_result, 'SNP'))
                if self.option('is_snp') == 'True':
                    if self.option('snp_method').lower() == 'samtools':
                        final_vcf = os.path.join(self.sam_rna.work_dir, "VcfFilterSamtools/output/final.vcf")
                    elif self.option('snp_method').lower() == 'gatk':
                        final_vcf = os.path.join(self.snp_rna.work_dir, "VcfFilterGatk/output/final.vcf")
                    else:
                        final_vcf = os.path.join(self.call_snp_indel.work_dir, "VcfFilterGatk/output/final.vcf")
                    os.link(final_vcf, os.path.join(self.intermediate_result, 'SNP', os.path.basename(final_vcf)))
                ## AS
                if self.option('is_as') == 'True':
                    shutil.copytree(os.path.join(self.output_dir, 'altersplicing'),
                                    os.path.join(self.intermediate_result, 'AS'))

        # 项目结果目录中呈现文件
        self.output_dir = self.output_dir
        self.target_dir = os.path.join(self.work_dir, 'upload')
        if os.path.isdir(self.target_dir):
            shutil.rmtree(self.target_dir)
        os.mkdir(self.target_dir)
        # 01Background
        os.mkdir(os.path.join(self.target_dir, '01Background'))
        ## genome_stat
        genome_stat = pd.read_table(self.genome_stat, header=0)
        genome_stat.rename(columns={'Chr': 'Chromosome', 'Size(Mb)': 'Length(MB)'}, inplace=True)
        genome_stat.to_csv(os.path.join(self.target_dir, '01Background', self.organism_name + ".genome_info.xls"),
                           sep="\t", header=True, index=False)
        ## software_info
        software_info = os.path.join(self.target_dir, '01Background', "software_info.xls")
        db = Config().get_mongo_client(mtype='ref_rna_v2')[Config().get_mongo_dbname('ref_rna_v2')]
        my_collection = db['sg_software_database']
        my_results = my_collection.find({})
        with open(software_info, "w") as w:
            w.write("\t".join(["Soft/Database", "Version", "Analysis", "Source"]) + "\n")
            for collection in my_results:
                w.write("\t".join(
                    [str(collection["software_database"]), str(collection["version"]), str(collection["usage"]),
                     str(collection["source"])]) + "\n")
        ## sample_info
        sample_info = os.path.join(self.target_dir, '01Background', "sample_info.xls")
        if self.option('sample_num') == 'multiple':
            group_table = self.option('group_table').prop["path"]
        else:
            group_table = os.path.join(self.work_dir, 'group.txt')
        with open(sample_info, "w") as w, open(group_table, "r") as f:
            w.write("\t".join(["Species Latin Name", "Sample Name", "Group Name"]) + "\n")
            for line in f:
                if line.startswith("#"):
                    pass
                else:
                    w.write("\t".join(
                        [self.organism_name, line.strip().split("\t")[0], line.strip().split("\t")[1]]) + "\n")
        # 02QC
        os.mkdir(os.path.join(self.target_dir, '02QC'))
        if self.option('datatype') == 'rawdata':
            raw_stat = os.path.join(self.output_dir, 'QC_stat/before_qc/fastq_stat.xls')
            os.link(raw_stat, os.path.join(self.target_dir, '02QC/rawdata_statistics.xls'))
        clean_stat = os.path.join(self.output_dir, 'QC_stat/after_qc/fastq_stat.xls')
        os.link(clean_stat, os.path.join(self.target_dir, '02QC/cleandata_statistics.xls'))
        if "mapping" in self.analysis_content:
            # 03Align
            os.mkdir(os.path.join(self.target_dir, '03Align'))
            align_stat = os.path.join(self.rnaseq_mapping.output_dir, 'Comparison_results')
            os.link(align_stat, os.path.join(self.target_dir, '03Align/align_stat.xls'))
            ## QualityAssessment
            os.makedirs(os.path.join(self.target_dir, '03Align/QualityAssessment'))
            chr_distribution = os.path.join(self.target_dir, '03Align/QualityAssessment', 'chr_distribution.xls')
            chr_stat_files = sorted(
                glob.glob("{}/*.bam_chr_stat.xls".format(self.map_assessment.output_dir + "/chr_stat")))
            dict = {}
            samples = {}
            chr = {}
            for file in chr_stat_files:
                sample_name = os.path.basename(file).split(".")[0]
                samples[sample_name] = 1
                with open(file, "r") as f:
                    f.readline()
                    for line in f:
                        items = line.strip().split("\t")
                        if items[0] not in chr:
                            chr[items[0]] = 1
                            dict[items[0]] = {}
                        dict[items[0]][sample_name] = items[1]
            with open(chr_distribution, "w") as w:
                w.write('Chromosome' + "\t" + "\t".join(sorted(samples.keys())) + "\n")
                for chr in sorted(chr.keys()):
                    w.write(chr)
                    for sample in sorted(samples.keys()):
                        if sample in dict[chr]:
                            w.write("\t" + dict[chr][sample])
                        else:
                            w.write("\t0")
                    w.write("\n")
            region_distribution = os.path.join(self.target_dir, '03Align/QualityAssessment', 'region_distribution.xls')
            region_stat_files = sorted(
                glob.glob("{}/*.reads_distribution.txt".format(self.map_assessment.output_dir + "/distribution")))
            dict = {}
            samples = {}
            distributions = ["CDS", "5'UTR", "3'UTR", "Introns", "Intergenic"]
            for file in region_stat_files:
                values = []
                sample_name = os.path.basename(file).split(".")[0]
                samples[sample_name] = 1
                with open(file, "r") as f:
                    f.readline()
                    f.next()
                    f.next()
                    f.next()
                    f.next()
                    for line in f:
                        if re.match(r"==", line):
                            continue
                        else:
                            line = line.strip().split()
                            values.append(float(line[2]))
                    values_new = values[:4]
                    values_new.append(sum([values[6], values[9]]))
                    total = sum(values_new)
                    for n, dis in enumerate(distributions):
                        if sample_name not in dict:
                            dict[sample_name] = {}
                        dict[sample_name][dis] = str(values_new[n]) + "(" + str(
                            float("%0.4f" % (values_new[n] / total)) * 100) + "%)"
            with open(region_distribution, "w") as w:
                w.write('Sample' + "\t" + "\t".join(distributions) + "\n")
                for sample in sorted(samples.keys()):
                    w.write(sample)
                    for dis in distributions:
                        w.write("\t" + dict[sample][dis])
                    w.write("\n")
        if "annotation" in self.analysis_content:
            # Assemble
            if self.option('is_assemble'):
                set_assembly(os.path.join(self.output_dir, 'assembly'), os.path.join(self.target_dir, '04Assemble'))
            trans2gene = os.path.join(self.target_dir, '04Assemble', 'Sequence', 'trans2gene.txt')
            if not os.path.exists(os.path.join(self.intermediate_result, 'Transcripts', 'trans2gene.txt')):
                self.move_file(trans2gene, os.path.join(self.intermediate_result, 'Transcripts', 'trans2gene.txt'))
            if os.path.exists(trans2gene):
                os.remove(trans2gene)
            # Annotation
            os.makedirs(os.path.join(self.target_dir, '05Annotation'))
            annot_file = RefAnnotation()
            merge_annot_v3 = os.path.join(self.output_dir, 'annot_merge')
            if "quantification" in self.analysis_content:
                gene_exp = self.quant.output_dir + "/gene.tpm.matrix"
                trans_exp = self.quant.output_dir + "/transcript.tpm.matrix"
            else:
                gene_exp = None
                trans_exp = None
            annot_dir = self.annot_merge.output_dir
            if not self.option("is_assemble"):
                self.api_annotation.has_new = False
                gene2trans = None
                gene2trans_ref = annot_dir + "/refannot_class/all_tran2gene.txt"
            else:
                gene2trans = annot_dir + "/newannot_class/all_tran2gene.txt"
                gene2trans_ref = annot_dir + "/refannot_class/all_tran2gene.txt"
            annot_file.run(merge_annot_v3, gene2trans, gene2trans_ref, gene_exp=gene_exp, trans_exp=trans_exp,
                           output_dir=os.path.join(self.target_dir, '05Annotation'))

            if self.option('is_assemble'):
                os.system("cat {} {} > {}".format(
                    self.known_pep,
                    os.path.join(self.annot_orfpfam.output_dir, 'new_transcripts.fa.transdecoder.pep'),
                    os.path.join(self.target_dir, '04Assemble/Sequence/all_pep.fa')
                ))
                os.system("cat {} {} > {}".format(
                    self.known_cds,
                    os.path.join(self.annot_orfpfam.output_dir, 'new_transcripts.fa.transdecoder.cds'),
                    os.path.join(self.target_dir, '04Assemble/Sequence/all_cds.fa')
                ))
                with open(os.path.join(self.target_dir, '04Assemble/Sequence/all_id.xls'), 'w') as fo, \
                        open(os.path.join(self.annot_merge.output_dir, "allannot_class/all_tran2gene.txt"), 'r') as fin:
                    fo.write("gene_id\ttranscript_id\tprotein_id\n")
                    for line in fin:
                        cols = line.strip("\n").split("\t")
                        fo.write("{}\t{}\t{}\n".format(cols[1], cols[0], cols[4]))

            else:
                os.makedirs(os.path.join(self.target_dir, '04Assemble'))
                os.makedirs(os.path.join(self.target_dir, '04Assemble', "Sequence"))
                os.link(self.known_cds,
                        os.path.join(self.target_dir, '04Assemble/Sequence/all_cds.fa'))
                os.link(self.known_pep,
                        os.path.join(self.target_dir, '04Assemble/Sequence/all_pep.fa'))

                with open(os.path.join(self.target_dir, '04Assemble/Sequence/all_id.xls'), 'w') as fo, \
                        open(os.path.join(self.annot_merge.output_dir, "refannot_class/all_tran2gene.txt"), 'r') as fin:
                    fo.write("gene_id\ttranscript_id\tprotein_id\n")
                    for line in fin:
                        cols = line.strip("\n").split("\t")
                        fo.write("{}\t{}\t{}\n".format(cols[1], cols[0], cols[4]))

        if "quantification" in self.analysis_content:
            # Expression
            os.makedirs(os.path.join(self.target_dir, '06Express/ExpAnnalysis'))
            if self.option('express_method') == 'RSEM':
                os.link(os.path.join(self.quant.output_dir, 'gene.count.matrix.annot.xls'),
                        os.path.join(self.target_dir, '06Express/ExpAnnalysis/gene.count.matrix.annot.xls'))
                if self.option('exp_way').lower() == 'tpm':
                    os.link(os.path.join(self.quant.output_dir, 'gene.tpm.matrix.annot.xls'),
                            os.path.join(self.target_dir, '06Express/ExpAnnalysis/gene.tpm.matrix.annot.xls'))
                if self.option('exp_way').lower() == 'fpkm':
                    os.link(os.path.join(self.quant.output_dir, 'gene.fpkm.matrix.annot.xls'),
                            os.path.join(self.target_dir, '06Express/ExpAnnalysis/gene.fpkm.matrix.annot.xls'))
                if self.option('level').lower() == 'transcript':
                    os.link(os.path.join(self.quant.output_dir, 'transcript.count.matrix.annot.xls'),
                            os.path.join(self.target_dir, '06Express/ExpAnnalysis/transcript.count.matrix.annot.xls'))
                    if self.option('exp_way').lower() == 'tpm':
                        os.link(os.path.join(self.quant.output_dir, 'transcript.tpm.matrix.annot.xls'),
                                os.path.join(self.target_dir, '06Express/ExpAnnalysis/transcript.tpm.matrix.annot.xls'))
                    if self.option('exp_way').lower() == 'fpkm':
                        os.link(os.path.join(self.quant.output_dir, 'transcript.fpkm.matrix.annot.xls'),
                                os.path.join(self.target_dir,
                                             '06Express/ExpAnnalysis/transcript.fpkm.matrix.annot.xls'))
            else:
                os.link(os.path.join(self.quant.output_dir, 'gene.tpm.matrix.annot.xls'),
                        os.path.join(self.target_dir, '06Express/ExpAnnalysis/gene.tpm.matrix.annot.xls'))
                os.link(os.path.join(self.quant.output_dir, 'gene.count.matrix.annot.xls'),
                        os.path.join(self.target_dir, '06Express/ExpAnnalysis/gene.count.matrix.annot.xls'))
                if self.option('level').lower() == 'transcript':
                    os.link(os.path.join(self.quant.output_dir, 'transcript.tpm.matrix.annot.xls'),
                            os.path.join(self.target_dir, '06Express/ExpAnnalysis/transcript.tpm.matrix.annot.xls'))
                    os.link(os.path.join(self.quant.output_dir, 'transcript.count.matrix.annot.xls'),
                            os.path.join(self.target_dir, '06Express/ExpAnnalysis/transcript.count.matrix.annot.xls'))
            if self.option('sample_num') == 'multiple':
                # os.makedirs(os.path.join(self.target_dir, '06Express/ExpCorr'))
                # os.link(os.path.join(self.exp_corr.output_dir, 'sample_correlation.xls'),
                #         os.path.join(self.target_dir, '06Express/ExpCorr/sample_correlation.xls'))
                if self.option('group_table').prop['sample_number'] > 2:
                    os.makedirs(os.path.join(self.target_dir, '06Express/ExpCorr'))
                    os.link(os.path.join(self.exp_corr.output_dir, 'sample_correlation.xls'),
                            os.path.join(self.target_dir, '06Express/ExpCorr/sample_correlation.xls'))#modify by fwy 两个样本时不进行相关性分析
                    os.makedirs(os.path.join(self.target_dir, '06Express/ExpPCA'))
                    # os.link(os.path.join(self.exp_pca.output_dir, 'PCA.xls'),
                    #         os.path.join(self.target_dir, '06Express/ExpPCA/PCA.xls'))
                    os.link(os.path.join(self.exp_pca.output_dir, 'Explained_variance_ratio.xls'),
                            os.path.join(self.target_dir, '06Express/ExpPCA/Explained_variance_ratio.xls'))
        if "other" in self.analysis_content:
            # DiffExpress
            if self.option('sample_num') == 'multiple':
                os.makedirs(os.path.join(self.target_dir, '07DiffExpress_G'))
                files = glob.glob(self.diffexp.output_dir + "/*.annot.xls") + glob.glob(
                    self.diffexp.output_dir + "/diff_summary_*.xls")
                for b in files:
                    if not os.path.exists(os.path.join(self.target_dir, '07DiffExpress_G', os.path.basename(b))):
                        os.link(b, os.path.join(self.target_dir, '07DiffExpress_G', os.path.basename(b)))
            # SNP
            if self.option('sample_num') == 'multiple' and self.option('is_snp') == 'True':
                os.makedirs(os.path.join(self.target_dir, '08SNP'))
                CopyFile().linkdir(os.path.join(self.work_dir, 'SnpTmp'), os.path.join(self.target_dir, '08SNP'))
                rm_files = [os.path.join(self.target_dir, '08SNP/snp_annotation.xls'),
                            os.path.join(self.target_dir, '08SNP/data_anno_pre.xls')]
                for rm_file in rm_files:
                    if os.path.exists(rm_file):
                        os.remove(rm_file)
                # SNP_vcf add by fwy 20200509
                os.makedirs(os.path.join(self.target_dir, '08SNP/SNP_vcf'))
                if self.option('is_snp') == 'True':
                    if self.option('snp_method').lower() == 'samtools':
                        final_vcf = os.path.join(self.sam_rna.work_dir, "VcfFilterSamtools/output/final.vcf")
                    elif self.option('snp_method').lower() == 'gatk':
                        final_vcf = os.path.join(self.snp_rna.work_dir, "VcfFilterGatk/output/final.vcf")
                    else:
                        final_vcf = os.path.join(self.call_snp_indel.work_dir, "VcfFilterGatk/output/final.vcf")
                    os.link(final_vcf, os.path.join(self.target_dir, '08SNP/SNP_vcf', os.path.basename(final_vcf)))
            # AS
            if self.option('sample_num') == 'multiple' and self.option('is_as') == 'True':
                set_rmats(os.path.join(self.output_dir, 'altersplicing'), os.path.join(self.target_dir, '09AS'),
                          self.task_id)
        self.def_upload()

    @workfuncdeco
    def def_upload(self):
        # transfer = MultiFileTransfer()
        intermediate_dir = self._sheet.output.replace('workflow_results', 'intermediate_results/')
        self.upload_to_s3(self.intermediate_result, intermediate_dir)
        # transfer.add_upload(self.intermediate_result, intermediate_dir)
        # transfer.perform()
        if self.option("upload_offline"):
            # 将质控结果文件和比对结果文件传输至线下服务器
            self.logger.info("开始向线下服务器传递比对bam文件，请耐心等待")
            cmd = "scp -r -i ~/.ssh/id_rsa {} dongmei.fu@192.168.10.46:/mnt/ilustre/centos7users/meng.luo/sanger_data".format(
                self.offline_results)
            code = os.system(cmd)
            if code == 0:
                self.logger.info("命令{}执行成功！".format(cmd))
            else:
                self.logger.info("命令{}执行失败！".format(cmd))

        sdir = self.add_upload_dir(self.target_dir)
        sdir.add_regexp_rules([
            [r'01Background/.*\.genome_info\.xls', 'xls', '基因组注释信息表', 0, "211628"],
            [r'03Align/AlignBam/.*\.bam', 'bam', '样本比对bam文件', 1, "211629"],
            [r'07DiffExpress_G/.*_vs_.*\.xls', 'xls', '差异分析结果表', 0, "211630"],
            [r'07DiffExpress_G/.*\.DE\.list', 'xls', '差异基因列表', 0, "211434"],
            [r'07DiffExpress_G/.*summary.*\.xls', 'xls', '差异表达基因统计表', 0, "211435"],
            [r'07DiffExpress_G/.*total_diff_stat.*\.xls', 'xls', '差异表达基因详情总表', 0, "211436"],
            [r'09AS/.*_vs_.*', '', '差异组别', 0, "211437"],
            [r'09AS/.*_vs_.*/JC', '', 'JC定量', 0, "211438"],
            [r'09AS/.*_vs_.*/JCEC', '', 'JCEC定量', 0, "211439"],
            [r'09AS/.*_vs_.*/JC/SE.detail.xls', 'xls', 'SE可变剪切事件详情表（JC）', 0, "211440"],
            [r'09AS/.*_vs_.*/JCEC/SE.detail.xls', 'xls', 'SE可变剪切事件详情表（JCEC）', 0, "211441"],
            [r'09AS/.*_vs_.*/JC/MXE.detail.xls', 'xls', 'MXE可变剪切事件详情表（JC）', 0, "211442"],
            [r'09AS/.*_vs_.*/JCEC/MXE.detail.xls', 'xls', 'MXE可变剪切事件详情表（JCEC）', 0, "211443"],
            [r'09AS/.*_vs_.*/JC/A3SS.detail.xls', 'xls', 'A3SS可变剪切事件详情表（JC）', 0, "211444"],
            [r'09AS/.*_vs_.*/JCEC/A3SS.detail.xls', 'xls', 'A3SS可变剪切事件详情表（JCEC）', 0, "211445"],
            [r'09AS/.*_vs_.*/JC/A5SS.detail.xls', 'xls', 'A5SS可变剪切事件详情表（JC）', 0, "211446"],
            [r'09AS/.*_vs_.*/JCEC/A5SS.detail.xls', 'xls', 'A5SS可变剪切事件详情表（JCEC）', 0, "211447"],
            [r'09AS/.*_vs_.*/JC/RI.detail.xls', 'xls', 'RI可变剪切事件详情表（JC）', 0, "211448"],
            [r'09AS/.*_vs_.*/JCEC/RI.detail.xls', 'xls', 'RI可变剪切事件详情表（JCEC）', 0, "211449"],
            [r'09AS/.*_vs_.*/diff_event_stats.xls', 'xls', '组内差异可变剪切事件统计表', 0, "211450"],
            [r'09AS/.*_vs_.*/diff_pattern_stats.JC.xls', 'xls', '组内差异可变剪切模式变化统计表（JC）', 0, "211451"],
            [r'09AS/.*_vs_.*/diff_pattern_stats.JCEC.xls', 'xls', '组内差异可变剪切模式变化统计表（JCEC）', 0, "211452"]
        ])
        sdir.add_relpath_rules([
            ['.', '', '流程分析结果目录', 0, "211453"],
            ['01Background', '', '项目背景结果目录', 0, "211454"],
            ['01Background/sample_info.xls', 'xls', '样本信息表', 0, "211455"],
            ['01Background/software_info.xls', 'xls', '软件信息表', 0, "211456"],
            ['02QC', '', '测序数据质控结果目录', 0, "211457"],
            ['02QC/rawdata_statistics.xls', 'xls', '原始数据统计表', 0, "211458"],
            ['02QC/cleandata_statistics.xls', 'xls', '质控数据统计表', 0, "211459"],
            ['03Align', '', '序列比对结果目录', 0, '211030'],
            ['03Align/align_stat.xls', 'xls', '比对结果统计表', 0, "211460"],
            ['03Align/QualityAssessment', '', '比对结果整体评估', 0, "211461"],
            ['03Align/QualityAssessment/chr_distribution.xls', 'xls', '不同染色体Reads分布统计表', 0, "211462"],
            ['03Align/QualityAssessment/region_distribution.xls', 'xls', '不同区域Reads分布统计表', 0, "211463"],
            ['04Assemble', '', '组装结果目录', 0, "211464"],
            ['04Assemble/length_distribution.200.xls', 'xls', '转录本长度分布表-步长200', 0, "211465"],
            ['04Assemble/length_distribution.300.xls', 'xls', '转录本长度分布表-步长300', 0, "211466"],
            ['04Assemble/length_distribution.600.xls', 'xls', '转录本长度分布表-步长600', 0, "211467"],
            ['04Assemble/length_distribution.1000.xls', 'xls', '转录本长度分布表-步长1000', 0, "211468"],
            ['04Assemble/classcode_statistics.xls', 'xls', '新转录本类型统计表', 0, "211469"],
            ['04Assemble/Sequence', '', '转录本序列文件', 0, "211470"],
            ['04Assemble/Sequence/all_transcripts.fa', 'fasta', '组装结果序列文件', 0, "211471"],
            ['04Assemble/Sequence/new_transcripts.fa', 'fasta', '新转录本序列文件', 0, "211472"],
            ['04Assemble/Sequence/all_cds.fa', 'fasta', 'CDS序列文件', 0],
            ['04Assemble/Sequence/all_pep.fa', 'fasta', '蛋白序列文件', 0],
            ['04Assemble/Sequence/all_id.xls', 'xls', '基因转录本蛋白ID对应关系文件', 0],
            ['04Assemble/Sequence/all_transcripts.gtf', 'gtf', '组装结果GTF文件', 0, "211473"],
            ['04Assemble/Sequence/new_transcripts.gtf', 'gtf', '新转录本GTF文件', 0, "211474"],
            ['04Assemble/Sequence/trans2gene.txt', 'txt', '转录本与基因的对应关系文件', 0, "211475"],
            ['05Annotation', '', '功能注释结果目录', 0, "211476"],
            ['05Annotation/AnnotDetail', '', '注释结果详情', 0, "211477"],
            ['05Annotation/AnnotDetail/all_gene_annot_detail.xls', 'xls', '所有基因注释结果详情表', 0, "211478"],
            ['05Annotation/AnnotDetail/all_transcript_annot_detail.xls', 'xls', '所有转录本注释结果详情表', 0, "211479"],
            ['05Annotation/AnnotDetail/ref_gene_annot_detail.xls', 'xls', '已知基因注释结果详情表', 0, "211480"],
            ['05Annotation/AnnotDetail/ref_transcript_annot_detail.xls', 'xls', '已知转录本注释结果详情表', 0, "211481"],
            ['05Annotation/AnnotDetail/new_gene_annot_detail.xls', 'xls', '新基因注释结果详情表', 0, "211482"],
            ['05Annotation/AnnotDetail/new_transcript_annot_detail.xls', 'xls', '新转录本注释结果详情表', 0, "211483"],
            ['05Annotation/AnnotStatistics', '', '注释结果统计', 0, "211484"],
            ['05Annotation/AnnotStatistics/all_annot_statistics.xls', 'xls', '所有基因/转录本结果统计表', 0, "211485"],
            ['05Annotation/AnnotStatistics/ref_annot_statistics.xls', 'xls', '已知基因/转录本结果统计表', 0, "211486"],
            ['05Annotation/AnnotStatistics/new_annot_statistics.xls', 'xls', '新基因/转录本结果统计表', 0, "211487"],
            ['06Express', '', '表达量分析结果目录', 0, "211488"],
            ['06Express/ExpAnnalysis', '', '表达定量结果', 0, "211489"],
            ['06Express/ExpAnnalysis/gene.count.matrix.xls', 'xls', '基因count表达定量结果表', 0, "211490"],
            ['06Express/ExpAnnalysis/gene.tpm.matrix.xls', 'xls', '基因tpm表达定量结果表', 0, "211491"],
            ['06Express/ExpAnnalysis/gene.fpkm.matrix.xls', 'xls', '基因fpkm表达定量结果表', 0, "211492"],
            ['06Express/ExpAnnalysis/transcript.count.matrix.xls', 'xls', '转录本count表达定量结果表', 0, "211493"],
            ['06Express/ExpAnnalysis/transcript.tpm.matrix.xls', 'xls', '转录本tpm表达定量结果表', 0, "211494"],
            ['06Express/ExpAnnalysis/transcript.fpkm.matrix.xls', 'xls', '转录本fpkm表达定量结果表', 0, "211495"],
            ['06Express/ExpAnnalysis/gene.tpm.matrix.annot.xls', 'xls', '基因tpm表达定量注释结果表', 0, "211496"],
            ['06Express/ExpAnnalysis/gene.fpkm.matrix.annot.xls', 'xls', '基因fpkm表达定量注释结果表', 0, "211497"],
            ['06Express/ExpAnnalysis/gene.count.matrix.annot.xls', 'xls', '基因count表达定量注释结果表', 0, "211498"],
            ['06Express/ExpAnnalysis/transcript.tpm.matrix.annot.xls', 'xls', '转录本tpm表达定量注释结果表', 0, "211499"],
            ['06Express/ExpAnnalysis/transcript.fpkm.matrix.annot.xls', 'xls', '转录本fpkm表达定量注释结果表', 0, "211500"],
            ['06Express/ExpAnnalysis/transcript.count.matrix.annot.xls', 'xls', '转录本count表达定量注释结果表', 0, "211501"],
            ['06Express/ExpCorr', '', '样本间相关性分析', 0, "211502"],
            ['06Express/ExpCorr/sample_correlation.xls', 'xls', '样本间相关性分析矩阵表', 0, "211503"],
            ['06Express/ExpPCA', '', '样本间PCA分析', 0, "211504"],
            # ['06Express/ExpPCA/PCA.xls', '', '样本间PCA分析结果表', 0, '211401'],
            ['06Express/ExpPCA/Explained_variance_ratio.xls', 'xls', '样本间PCA主成分解释表', 0, "211505"],
            ['07DiffExpress_G', '', '表达量差异分析结果目录', 0, "211506"],
            ['08SNP', '', 'SNP/InDel分析结果目录', 0, "211507"],
            ['08SNP/SNP_vcf', '', 'SNP鉴定vcf结果目录', 0],
            ['08SNP/SNP_vcF/final.vcf', 'vcf', 'SNP鉴定vcf表', 0],
            ['08SNP/snp_anno.xls', 'xls', 'SNP分析结果注释详情表', 0, "211508"],
            ['08SNP/indel_anno.xls', 'xls', 'InDel分析结果注释详情表', 0],
            ['08SNP/snp_transition_tranversion_statistics.xls', 'xls', 'SNP类型统计结果表', 0, "211510"],
            ['08SNP/snp_freq_statistics.xls', 'xls', 'SNP频率统计结果表', 0, "211511"],
            ['08SNP/snp_depth_statistics.xls', 'xls', 'SNP深度统计结果表', 0, "211512"],
            ['08SNP/snp_position_distribution.xls', 'xls', 'SNP不同区域布析结果表', 0, "211513"],
            ['08SNP/indel_position_distribution.xls', 'xls', 'InDel不同区域布析结果表', 0, "211514"],
            ['09AS', '', '可变剪切分析结果目录', 0, "211515"],
            ['09AS/event_type.JC.xls', 'xls', '可变剪切事件统计表（JC）', 0, "211516"],
            ['09AS/event_type.JCEC.xls', 'xls', '可变剪切事件统计表（JCEC）', 0, "211517"]
        ])
        self.update_collections()

    @workfuncdeco
    def update_collections(self):
        intermediate_dir = self._sheet.output.replace('workflow_results', 'intermediate_results/')
        db = Config().get_mongo_client(mtype='ref_rna_v2')[Config().get_mongo_dbname('ref_rna_v2')]
        col0 = db['sg_task']
        col0.update({'task_id': self.task_id},
                    {'$set': {'refrna_seqdb': os.path.join(intermediate_dir, 'SequenceDatabase/refrna_seqs.db')}},
                    upsert=True)
        col0.update({'task_id': self.task_id}, {'$set': {'ref_gtf': self.ref_gtf}}, upsert=True)
        col0.update({'task_id': self.task_id}, {'$set': {'ref_genome': self.ref_genome}}, upsert=True)
        col0.update({'task_id': self.task_id}, {'$set': {'genome_id': self.genome_id}}, upsert=True)
        col0.update({'task_id': self.task_id}, {'$set': {'genome_id': self.genome_id}}, upsert=True)
        col0.update({'task_id': self.task_id}, {'$set': {'fq_type': self.option('fq_type')}}, upsert=True)
        col0.update({'task_id': self.task_id}, {'$set': {'strand_specific': self.option('strand_specific')}},
                    upsert=True)
        col0.update({'task_id': self.task_id}, {'$set': {'strand_dir': self.option('strand_dir')}}, upsert=True)
        col0.update({'task_id': self.task_id}, {'$set': {'version': 'v3.1'}}, upsert=True)
        col0.update({'task_id': self.task_id}, {'$set': {'analysis_strategy': self.option('analysis_strategy')}},
                    upsert=True)
        if "annotation" in self.analysis_content:
            col0.update({'task_id': self.task_id},
                        {'$set': {'database_version': {"kegg": self.option("kegg_version")}}}, upsert=True)
            if self.option('is_assemble'):
                col0.update({'task_id': self.task_id},
                            {'$set': {'assemble_t2g': os.path.join(intermediate_dir, 'Transcripts/trans2gene.txt')}},
                            upsert=True)
                col0.update({'task_id': self.task_id},
                            {'$set': {
                                'assemble_fa': os.path.join(self._sheet.output,
                                                            '04Assemble/Sequence/all_transcripts.fa')}},
                            upsert=True)
                col0.update({'task_id': self.task_id},
                            {'$set': {
                                'as_gtf': os.path.join(self._sheet.output, '04Assemble/Sequence/all_transcripts.gtf')}},
                            upsert=True)
                col0.update({'task_id': self.task_id},
                            {'$set': {
                                'sample_gtf': os.path.join(intermediate_dir, 'Stringtie/')}},
                            upsert=True)
            else:
                col0.update({'task_id': self.task_id},
                            {'$set': {'assemble_t2g': os.path.join(intermediate_dir, 'Transcripts/trans2gene.txt')}},
                            upsert=True)
            if self.option('is_assemble'):
                col0.update({'task_id': self.task_id},
                            {'$set': {'assemble_t2g': os.path.join(intermediate_dir, 'Transcripts/trans2gene.txt')}},
                            upsert=True)
                col0.update({'task_id': self.task_id},
                            {'$set': {
                                'assemble_fa': os.path.join(self._sheet.output,
                                                            '04Assemble/Sequence/all_transcripts.fa')}},
                            upsert=True)
                col0.update({'task_id': self.task_id},
                            {'$set': {
                                'as_gtf': os.path.join(self._sheet.output, '04Assemble/Sequence/all_transcripts.gtf')}},
                            upsert=True)
                col0.update({'task_id': self.task_id},
                            {'$set': {
                                'sample_gtf': os.path.join(intermediate_dir, 'Stringtie/')}},
                            upsert=True)
            else:
                col0.update({'task_id': self.task_id},
                            {'$set': {'assemble_t2g': os.path.join(intermediate_dir, 'Transcripts/trans2gene.txt')}},
                            upsert=True)
                col0.update({'task_id': self.task_id},
                            {'$set': {'assemble_fa': os.path.join(intermediate_dir, 'Transcripts/all_transcripts.fa')}},
                            upsert=True)
                col0.update({'task_id': self.task_id}, {'$set': {'as_gtf': self.ref_gtf}}, upsert=True)
            col1 = db['sg_annotation_stat']
            col1.update({'task_id': self.task_id},
                        {'$set': {'result_dir': os.path.join(intermediate_dir, 'Annotation')}}, upsert=True)
        if "quantification" in self.analysis_content:
            col2 = db['sg_exp']
            col2.update({'task_id': self.task_id, 'exp_level': 'G'}, {
                '$set': {'count_file': os.path.join(intermediate_dir,
                                                    'Express/ExpAnnalysis/gene.count.matrix.xls')}}, upsert=True)
            col2.update({'task_id': self.task_id, 'exp_level': 'T'}, {
                '$set': {'count_file': os.path.join(intermediate_dir,
                                                    'Express/ExpAnnalysis/transcript.count.matrix.xls')}}, upsert=True)
        super(RefrnaWorkflow, self).end()

    @workfuncdeco
    def export_task_info(self):
        api = self.api.api('task_info.ref_rna_v2')
        api.add_task_info()

    @workfuncdeco
    def export_genome_info(self):
        api = self.api.api('ref_rna_v2.genome_info')
        api.add_genome_info(file_path=self.genome_stat, species_name=self.option('ref_genome'), species=self.species,
                            ref_anno_version=self.genome_version, hyperlink=self.hyperlink)

    @workfuncdeco
    def export_ref_rna_qc_before(self):
        api = self.api.api('ref_rna_v2.ref_rna_qc')
        api.add_samples_info(qc_stat=self.hiseq_reads_stat_raw.output_dir, fq_type=self.option('fq_type').lower(),
                             about_qc='before')
        api.add_gragh_info(quality_stat=os.path.join(self.hiseq_reads_stat_raw.output_dir, 'qualityStat'),
                           about_qc='before')

    @workfuncdeco
    def export_ref_rna_qc_after(self):
        api = self.api.api('ref_rna_v2.ref_rna_qc')
        api.add_samples_info(qc_stat=self.hiseq_reads_stat_use.output_dir, fq_type=self.option('fq_type').lower(),
                             about_qc='after')
        api.add_gragh_info(quality_stat=os.path.join(self.hiseq_reads_stat_use.output_dir, 'qualityStat'),
                           about_qc='after')
        if self.option('sample_num') == 'multiple':
            if self.option("group_table").is_set:
                self.group_id, specimen_names, category_names = api.add_specimen_group(self.option('group_table').path)
            if self.option('control_file').is_set:
                self.control_id, compare_detail = api.add_control_group(self.option('control_file').path, self.group_id)
        else:
            sp_set = set()
            if self.option('datatype') == 'rawdata':
                fastq_dir = self.option('fastq_dir').path
            else:
                fastq_dir = self.option('qc_dir').path
            for line in open(os.path.join(fastq_dir, 'list.txt')):
                sp_set.add(line.strip().split('\t')[1])
            if len(sp_set) != 1:
                self.set_error('invalid sample number')
            sample = list(sp_set)[0]
            group_table = os.path.join(self.work_dir, 'group.txt')
            open(group_table, 'w').write('#sample\tgroup\n{}\t{}'.format(sample, sample))
            self.group_id, specimen_names, category_names = api.add_specimen_group(group_table)
        intermediate_dir = self._sheet.output.replace('workflow_results', 'intermediate_results/')
        api.add_bam_path(intermediate_dir)

    @workfuncdeco
    def export_ref_rna_qc_alignment(self):
        api = self.api.api('ref_rna_v2.ref_rna_qc')
        if self.option('align_method').lower() == 'hisat':
            api.add_hisat_mapping_stat(os.path.join(self.rnaseq_mapping.output_dir, 'stat'))
        elif self.option('align_method').lower() == 'tophat':
            api.add_tophat_mapping_stat(os.path.join(self.rnaseq_mapping.output_dir, 'stat'))
        elif self.option('align_method').lower() == 'star':
            api.add_star_mapping_stat(os.path.join(self.rnaseq_mapping.output_dir, 'stat'))

    @workfuncdeco
    def export_ref_rna_qc_assessment(self):
        api = self.api.api('ref_rna_v2.ref_rna_qc')
        if 'saturation' in self.option('map_assess_method'):
            api.add_rpkm_table(os.path.join(self.map_assessment.output_dir, 'saturation'))
        if 'coverage' in self.option('map_assess_method'):
            api.add_coverage_table(os.path.join(self.map_assessment.output_dir, 'coverage'))
        if 'distribution' in self.option('map_assess_method'):
            api.add_distribution_table(os.path.join(self.map_assessment.output_dir, 'distribution'))
        if 'chr_stat' in self.option('map_assess_method'):
            api.add_chrom_distribution_table(os.path.join(self.map_assessment.output_dir, 'chr_stat'))

    @workfuncdeco
    def export_ref_assembly(self):
        api = self.api.api('ref_rna_v2.ref_assembly')
        params = json.dumps({'task_id': self.task_id, 'submit_location': 'transcripts', 'task_type': 2}, sort_keys=True)
        if self.option('assemble_method').lower() == 'stringtie':
            all_gtf_path = os.path.join(self.refrna_assemble.output_dir, 'Stringtie')
            merged_path = os.path.join(self.refrna_assemble.output_dir, 'StringtieMerge')
        elif self.option('assemble_method').lower() == 'cufflinks':
            all_gtf_path = os.path.join(self.refrna_assemble.output_dir, 'Cufflinks')
            merged_path = os.path.join(self.refrna_assemble.output_dir, 'Cuffmerge')
        statistics_path = os.path.join(self.refrna_assemble.output_dir, 'Statistics')
        api.add_assembly_result(params=params, all_gtf_path=all_gtf_path, merged_path=merged_path,
                                statistics_path=statistics_path)

    @workfuncdeco
    def export_annotation(self):
        self.api_annotation = self.api.api("ref_rna_v2.ref_annotation")
        annot_dir = self.annot_merge.output_dir
        if not self.option("is_assemble"):
            self.api_annotation.has_new = False
            trans2gene = None
            trans2gene_ref = annot_dir + "/refannot_class/all_tran2gene.txt"
        else:
            trans2gene = annot_dir + "/newannot_class/all_tran2gene.txt"
            trans2gene_ref = annot_dir + "/refannot_class/all_tran2gene.txt"
        self.api_annotation.species_name = self.option("ref_genome")
        self.api_annotation.has_new = self.option('is_assemble')
        params_dict = {
            "nr_evalue": str(self.option("nr_evalue")),
            "nr_similarity": self.option("nr_similarity"),
            "nr_identity": self.option("nr_identity"),
            "swissprot_evalue": str(self.option("swissprot_evalue")),
            "swissprot_similarity": self.option("swissprot_similarity"),
            "swissprot_identity": self.option("swissprot_identity"),
            "cog_evalue": str(self.option("cog_evalue")),
            "cog_similarity": self.option("cog_similarity"),
            "cog_identity": self.option("cog_identity"),
            "kegg_evalue": str(self.option("kegg_evalue")),
            "kegg_similarity": self.option("kegg_similarity"),
            "kegg_identity": self.option("kegg_identity"),
            "pfam_evalue": str(self.option("pfam_evalue")),
        }
        if "quantification" in self.analysis_content:
            gene_exp = self.quant.output_dir + "/gene.tpm.matrix"
            trans_exp = self.quant.output_dir + "/transcript.tpm.matrix"
        else:
            gene_exp = None
            trans_exp = None
        self.api_annotation.run(
            annot_dir,
            trans2gene,
            trans2gene_ref,
            params_dict=params_dict,
            taxonomy=self.option("kegg_database"),
            exp_level=self.option("level").lower(),
            version="v3",
            gene_exp=gene_exp,
            trans_exp=trans_exp,
        )

        '''
        api = self.api.api('ref_rna_v2.annotation')
        api.species_name = self.option('ref_genome')
        annot_merge_output_dir = self.annot_merge.output_dir
        params_dict = {
            'task_id': self.task_id,
            'submit_location': 'annotationstat',
            'task_type': 2,
            'nr_evalue': self.option('nr_evalue'),
            'nr_identity': self.option('nr_identity'),
            'nr_similarity': self.option('nr_similarity'),
            'swissprot_evalue': self.option('swissprot_evalue'),
            'swissprot_identity': self.option('swissprot_identity'),
            'swissprot_similarity': self.option('swissprot_similarity'),
            'cog_evalue': self.option('cog_evalue'),
            'cog_identity': self.option('cog_identity'),
            'cog_similarity': self.option('cog_similarity'),
            'kegg_evalue': self.option('kegg_evalue'),
            'kegg_identity': self.option('kegg_identity'),
            'kegg_similarity': self.option('kegg_similarity'),
            'pfam_evalue': self.option('pfam_evalue')
        }
        taxonomy = self.option('kegg_database')
        exp_level = self.option('level').lower()
        api.has_new = self.option('is_assemble')
        api.run(annot_merge_output_dir, params_dict, taxonomy, exp_level)
        '''

    @workfuncdeco
    def export_all_exp_matrix(self):
        api = self.api.api('ref_rna_v2.all_exp')
        exp_type = self.option('exp_way').upper()
        exp_matrix = {'T': os.path.join(self.quant.output_dir, 'transcript.{}.matrix'.format(exp_type.lower())),
                      'G': os.path.join(self.quant.output_dir, 'gene.{}.matrix'.format(exp_type.lower()))}
        quant_method = self.option('express_method')
        lib_type = self.option('strand_dir')
        if self.option('sample_num') == 'multiple':
            group_dict = self.option('group_table').prop['group_dict']
        else:
            group_table = os.path.join(self.work_dir, 'group.txt')
            for line in open(group_table):
                if line.strip() and line[0] != '#':
                    sample = line.strip().split('\t')[1]
            group_dict = {sample: [sample]}
        group_id = self.group_id
        project_sn = self.project_sn,
        task_id = self.task_id
        params = json.dumps({
            'task_id': task_id,
            'submit_location': 'exp_detail',
            'task_type': 2,
            'method': quant_method,
            'exp_type': exp_type
        }, sort_keys=True, separators=(',', ':'))
        self.exp_ids = dict()
        if self.option('level').lower() == 'transcript':
            self.exp_ids['T'] = api.add_exp(exp_matrix=exp_matrix['T'], quant_method=quant_method, exp_level='T',
                                            lib_type=lib_type, group_dict=group_dict, group_id=group_id,
                                            exp_type=exp_type, add_distribution=False, project_sn=project_sn,
                                            task_id=task_id, params=params)
        self.exp_ids['G'] = api.add_exp(exp_matrix=exp_matrix['G'], quant_method=quant_method, exp_level='G',
                                        lib_type=lib_type, group_dict=group_dict, group_id=group_id,
                                        exp_type=exp_type, add_distribution=False, project_sn=project_sn,
                                        task_id=task_id, params=params)

    @workfuncdeco
    def export_all_exp_distribution(self):
        api = self.api.api('ref_rna_v2.all_exp')
        task_id = self.task_id
        quant = self.quant
        exp_way = self.option('exp_way')

        def exp_matrix(exp_level):
            return quant.option('ref_{}_{}'.format(exp_level, exp_way)).path

        group_dict = self.option('group_table').prop['group_dict']
        exp_ids = self.exp_ids
        group_id = self.group_id

        def params(exp_level):
            return json.dumps({
                'task_id': task_id,
                'submit_location': 'expgraph',
                'task_type': 2,
                'exp_id': str(exp_ids[exp_level]),
                'group_dict': group_dict,
                'group_id': str(group_id),
                'exp_level': exp_level,
                'type': 'ref'
            }, sort_keys=True, separators=(',', ':'))

        quant_method = self.option('express_method')
        project_sn = self.project_sn
        if self.option('level').lower() == 'transcript':
            api.add_distribution(exp_matrix=exp_matrix('transcript'), group_dict=group_dict, params=params('T'),
                                 exp_level='T', quant_method=quant_method, project_sn=project_sn, task_id=task_id)
        api.add_distribution(exp_matrix=exp_matrix('gene'), group_dict=group_dict, params=params('G'), exp_level='G',
                             quant_method=quant_method, project_sn=project_sn, task_id=task_id)

    @workfuncdeco
    def export_add_exp_venn(self):
        api = self.api.api('ref_rna_v2.all_exp')
        graph_table = os.path.join(self.exp_venn.output_dir, 'venn_graph.xls')
        group_dict = self.option('group_table').prop['group_dict']
        if len(group_dict) > 6:
            group_dict = OrderedDict(group_dict.items()[:6])
        params = json.dumps(dict(
            task_id=self.task_id,
            submit_location='expvenn',
            task_type=2,
            exp_id=str(self.exp_ids['G']),
            group_id=str(self.group_id),
            exp_level='G',
            group_dict=group_dict,
            threshold='1',
            type='ref',
        ), sort_keys=True, separators=(',', ':'))
        import datetime
        time_now = datetime.datetime.now()
        name = 'ExpVenn_G_{}_{}_{}'.format(
            self.option('express_method'), self.option('exp_way').upper(), time_now.strftime('%Y%m%d_%H%M%S'))
        main_info = dict(
            project_sn=self.project_sn,
            task_id=self.task_id,
            version='v3',
            name=name,
            created_ts=time_now.strftime('%Y-%m-%d %H:%M:%S'),
            exp_id=str(self.exp_ids['G']),
            desc='Expression venn analysis main table',
            params=params,
            status='start'
        )
        main_id = api.create_db_table('sg_exp_venn', [main_info])
        api.add_exp_venn(graph_table, main_id=main_id)

    @workfuncdeco
    def export_all_exp_corr(self):
        api = self.api.api('ref_rna_v2.all_exp')
        corr_work_dir = self.exp_corr.work_dir
        quant_method = self.option('express_method')
        task_id = self.task_id
        exp_ids = self.exp_ids
        group_dict = self.option('group_table').prop['group_dict']
        group_id = self.group_id

        def params(exp_level):
            return json.dumps({
                'task_id': task_id,
                'submit_location': 'expcorr',
                'task_type': 2,
                'exp_id': str(exp_ids[exp_level]),
                'group_dict': group_dict,
                'group_id': str(group_id),
                'exp_level': exp_level,
                'scm': 'complete',
                'scd': 'euclidean',
                'corr_method': 'pearson',
                'type': 'ref'
            }, sort_keys=True, separators=(',', ':'))

        project_sn = self.project_sn
        api.add_exp_corr2(corr_work_dir, exp_level='G', quant_method=quant_method, params=params('G'),
                          project_sn=project_sn, task_id=task_id)

    @workfuncdeco
    def export_all_exp_pca(self):
        api = self.api.api('ref_rna_v2.all_exp')
        pca_output_dir = self.exp_pca.output_dir
        quant_method = self.option('express_method')
        task_id = self.task_id
        exp_ids = self.exp_ids
        exp_way = self.option('exp_way')
        group_dict = self.option('group_table').prop['group_dict']
        group_id = self.group_id

        def params(exp_level):
            return json.dumps({
                'task_id': task_id,
                'submit_location': 'exppca',
                'task_type': 2,
                'exp_id': str(exp_ids[exp_level]),
                'group_dict': group_dict,
                'group_id': str(group_id),
                'exp_level': exp_level,
                'type': 'ref',
                'Draw_in_groups': "no"
            }, sort_keys=True, separators=(',', ':'))

        project_sn = self.project_sn
        main_id = api.add_exp_pca2(pca_output_dir, quant_method=quant_method, exp_id=exp_ids['G'], exp_level='G',
                                   params=params('G'), project_sn=project_sn, task_id=task_id)
        if hasattr(self, 'ellipse'):
            api.insert_ellipse_table(os.path.join(self.ellipse.work_dir, 'ellipse_out.xls'), main_id)

    @workfuncdeco
    def export_all_exp_diff(self):
        api = self.api.api('ref_rna_v2.all_exp')
        diff_output = self.diffexp.output_dir
        exp_ids = self.exp_ids
        group_dict = self.option('group_table').prop['group_dict']
        group_id = self.group_id
        quant_method = self.option('express_method')
        diff_method = self.option('diff_method')
        project_sn = self.project_sn
        task_id = self.task_id
        control_id = self.control_id
        fc = str(float(self.option('fc')))
        # if '.' in fc:
        #     if fc.split('.')[1] == '0':
        #         fc = str(int(float(fc)))
        correct_method = self.option('padjust_way')
        stat_type = self.option('pvalue_padjust')
        stat_cutoff = str(self.option('diff_fdr_ci'))
        tpm_filter_threshold = str(float(self.option('filter_tpm')))

        # if '.' in tpm_filter_threshold:
        #     if tpm_filter_threshold.split('.')[1] == '0':
        #         tpm_filter_threshold = str(int(float(tpm_filter_threshold)))

        def params(exp_level):
            if diff_method.lower() in ["degseq", "edger", "deseq2", 'limma', 'svaseqlimma']:
                params_dict = {
                    'task_id': task_id,
                    'submit_location': 'diff_detail',
                    'task_type': 2,
                    'exp_id': str(exp_ids[exp_level]),
                    'group_id': str(group_id),
                    'control_id': str(control_id),
                    'exp_level': exp_level,
                    'group_dict': group_dict,
                    'fc': fc,
                    'tpm_filter_threshold': tpm_filter_threshold,
                    'stat_type': stat_type,
                    'stat_cutoff': stat_cutoff,
                    'diff_method': diff_method,
                    'type': 'ref',
                    'is_batch': 'False',
                }
                if stat_type == 'padjust':
                    params_dict.update({'correct_method': correct_method})
            else:
                params_dict = {
                    'task_id': task_id,
                    'submit_location': 'diff_detail',
                    'task_type': 2,
                    'exp_id': str(exp_ids[exp_level]),
                    'group_id': str(group_id),
                    'control_id': str(control_id),
                    'exp_level': exp_level,
                    'group_dict': group_dict,
                    'fc': fc,
                    'tpm_filter_threshold': tpm_filter_threshold,
                    'stat_cutoff': stat_cutoff,
                    'diff_method': diff_method,
                    'type': 'ref',
                    'is_batch': 'False',
                    'prob': float(self.option('diff_fdr_ci'))
                }
            return json.dumps(params_dict, sort_keys=True, separators=(',', ':'))

        if diff_method.lower() in ["degseq", "edger", "deseq2", 'limma', 'svaseqlimma']:
            api.add_diffexp(diff_output, exp_id=exp_ids['G'], group_dict=group_dict, group_id=group_id, exp_level='G',
                            quant_method=quant_method, diff_method=diff_method, project_sn=project_sn, task_id=task_id,
                            params=params('G'), pvalue_padjust=stat_type)
        else:
            api.add_diffexp_noiseq(diff_output, exp_id=exp_ids['G'], group_dict=group_dict, group_id=group_id,
                                   exp_level='G',
                                   quant_method=quant_method, diff_method=diff_method, project_sn=project_sn,
                                   task_id=task_id,
                                   params=params('G'))

    @workfuncdeco
    def export_gene_detail(self):
        api = self.api.api('ref_rna_v3.gene_detail')
        refrna_seqdb = self.detail.option('database').path
        if self.option('is_assemble'):
            t2g_file = self.refrna_assemble.option('trans2gene').path
            txpt_fa = self.refrna_assemble.option('all_transcripts_fa').path
            new_cds = os.path.join(self.annot_orfpfam.output_dir, 'new_transcripts.fa.transdecoder.cds')
            new_pep = os.path.join(self.annot_orfpfam.output_dir, 'new_transcripts.fa.transdecoder.pep')
        else:
            t2g_file = self.transcript_abstract.option('trans2gene').path
            txpt_fa = self.transcript_abstract.option('trans_fa').path
            new_cds = None
            new_pep = None
        txpt_bed = self.gene_fa.option('transcript_bed').path
        gene_bed = self.gene_fa.option('gene_bed').path
        gene_fa = self.gene_fa.option('gene_fa').path
        biomart_file = self.des
        biomart_type = self.des_type
        species_urls = self.hyperlink
        api.add_gene_detail(refrna_seqdb, t2g_file, txpt_bed, txpt_fa, gene_bed, gene_fa,
                            biomart_file, biomart_type, species_urls, new_cds, new_pep)

    @workfuncdeco
    def export_snp(self):
        api = self.api.api('ref_rna_v3.ref_snp')
        task_id = self.task_id
        project_sn = self.project_sn
        new_output = os.path.join(self.work_dir, 'SnpTmp')
        if os.path.exists(new_output):
            shutil.rmtree(new_output)
        os.mkdir(new_output)
        if self.option('snp_method').lower() == 'gatk':
            snp_anno = self.snp_rna.output_dir
            if os.path.exists(snp_anno + "/snp_annotation_statistics.xls"):
                params = dict(
                    task_id=task_id,
                    submit_location='snp',
                    task_type=2,
                    method_type='gatk'
                )
                api.add_snp_main(snp_anno=snp_anno, params=params, task_id=task_id, method_type='gatk',
                                 project_sn=project_sn, new_output=new_output)
        if self.option('snp_method').lower() == 'samtools':
            snp_anno = self.sam_rna.output_dir
            if os.path.exists(snp_anno + "/snp_annotation_statistics.xls"):
                params = dict(
                    task_id=task_id,
                    submit_location='snp',
                    task_type=2,
                    method_type='samtools'
                )
                api.add_snp_main(snp_anno=snp_anno, params=params, task_id=task_id, method_type='samtools',
                                 project_sn=project_sn, new_output=new_output)
        if self.option('snp_method').lower() == 'sentieon':
            snp_anno = self.call_snp_indel.output_dir + '/predeal'
            if os.path.exists(snp_anno + "/snp_annotation_statistics.xls"):
                params = dict(
                    task_id=task_id,
                    submit_location='snp',
                    task_type=2,
                    method_type='sentieon'
                )
                api.add_snp_main(snp_anno=snp_anno, params=params, task_id=task_id, method_type='sentieon',
                                 project_sn=project_sn, new_output=new_output)
        # if os.path.exists(os.path.join(self.work_dir, 'SnpTmp/snp_anno.xls')):
        #     os.remove(os.path.join(self.work_dir, 'SnpTmp/snp_anno.xls'))
        # os.link(os.path.join(snp_anno, 'data_anno_pre.xls'), os.path.join(self.work_dir, 'SnpTmp/snp_anno.xls'))

    @workfuncdeco
    def export_rmats(self):
        api = self.api.api('ref_rna_v3.rmats')
        for p in glob.glob(os.path.join(self.rmats.output_dir, '*')):
            if os.path.isdir(p):
                outpath = p
                ctrl, test = os.path.basename(outpath).split('_vs_')
                group_dict = {ctrl: self.option('group_table').prop['group_dict'][ctrl],
                              test: self.option('group_table').prop['group_dict'][test]}
                compare_plan = '{}|{}'.format(ctrl, test)
                params = json.dumps({
                    'task_id': self.task_id,
                    'submit_location': 'splicingrmats',
                    'task_type': 2,
                    'group_id': str(self.group_id),
                    'group_dict': group_dict,
                    'control_id': str(self.control_id),
                    'compare_plan': compare_plan
                }, sort_keys=True, separators=(',', ':'))
                api.add_sg_splicing_rmats(params, outpath)

    @workfuncdeco
    def export_rmats_count(self):
        api = self.api.api('ref_rna_v3.rmats_count')
        api.add_rmats_count(self.rmats.output_dir)

    def merge_annotation_exp_matrix(self):
        if self.option('sample_num') == 'multiple':
            group_dict = self.option('group_table').prop['group_dict']
        else:
            group_table = os.path.join(self.work_dir, 'group.txt')
            for line in open(group_table):
                if line.strip() and line[0] != '#':
                    sample = line.strip().split('\t')[1]
            group_dict = {sample: [sample]}
        exp_output = self.quant.output_dir
        if self.option('is_assemble'):
            annot = os.path.join(self.output_dir, 'annot_merge/allannot_class/all_annot.xls')
        else:
            annot = os.path.join(self.output_dir, 'annot_merge/refannot_class/all_annot.xls')
        all_annot = pd.read_table(annot, header=0, index_col=0)
        gene_annot_pd = all_annot[all_annot['is_gene'] == 'yes'].drop(
            columns=['transcript_id', 'is_gene', 'gene_name', 'description', 'length'])
        order = ["nr", "go", "KO_id", "KO_name", "paths", "cog", "cog_description", "pfam", "swissprot", "entrez"]
        gene_annot_pd = pd.DataFrame(gene_annot_pd, columns=order)
        gene_info_pd = all_annot[all_annot['is_gene'] == 'yes'][['gene_name', 'description', 'length']]
        trans_annot_pd = all_annot.reset_index().drop(
            columns=['gene_id', 'is_gene', 'gene_name', 'description', 'length']).set_index('transcript_id')
        trans_annot_pd = pd.DataFrame(trans_annot_pd, columns=order)
        trans_info_pd = all_annot[['transcript_id', 'gene_name', 'description', 'length']].reset_index().set_index(
            'transcript_id')
        # gene
        ## gene tpm
        gene_tpm_matrix = os.path.join(exp_output, 'gene.tpm.matrix')
        gene_tpm_pd = pd.read_table(gene_tpm_matrix, header=0, index_col=0)
        gene_tpm_dicts = gene_tpm_pd.to_dict('index')
        gene_group_tpm = OrderedDict()
        for seq_id in sorted(gene_tpm_dicts):
            tmp_exp_dict = gene_tpm_dicts[seq_id]
            for group in group_dict:
                if seq_id not in gene_group_tpm:
                    gene_group_tpm[seq_id] = dict()
                gene_group_tpm[seq_id].update(
                    {group: round(sum([tmp_exp_dict[x] for x in group_dict[group]]) / len(group_dict[group]), 4)})
        gene_group_pd = (pd.DataFrame(data=gene_group_tpm, columns=gene_group_tpm.keys())).T
        gene_tpm_result = pd.concat([gene_info_pd, gene_tpm_pd, gene_group_pd, gene_annot_pd], axis=1)
        gene_tpm_out = os.path.join(exp_output, 'gene.tpm.matrix.annot.xls')
        header = ['gene_id']
        header.extend(gene_tpm_result.columns.tolist())
        with open(gene_tpm_out, "w") as w:
            w.write("\t".join(header) + "\n")
        gene_tpm_result.to_csv(gene_tpm_out, header=False, index=True, sep='\t', mode='a')
        ## gene count
        gene_count_matrix = os.path.join(exp_output, 'gene.count.matrix')
        gene_count_pd = pd.read_table(gene_count_matrix, header=0, index_col=0)
        gene_count_dicts = gene_count_pd.to_dict('index')
        gene_group_count = OrderedDict()
        for seq_id in sorted(gene_count_dicts):
            tmp_exp_dict = gene_count_dicts[seq_id]
            for group in group_dict:
                if seq_id not in gene_group_count:
                    gene_group_count[seq_id] = dict()
                gene_group_count[seq_id].update(
                    {group: round(sum([tmp_exp_dict[x] for x in group_dict[group]]) / len(group_dict[group]), 4)})
        gene_group_pd = (pd.DataFrame(data=gene_group_count, columns=gene_group_count.keys())).T
        gene_count_result = pd.concat([gene_info_pd, gene_count_pd, gene_group_pd, gene_annot_pd], axis=1)
        gene_count_out = os.path.join(exp_output, 'gene.count.matrix.annot.xls')
        header = ['gene_id']
        header.extend(gene_count_result.columns.tolist())
        with open(gene_count_out, "w") as w:
            w.write("\t".join(header) + "\n")
        gene_count_result.to_csv(gene_count_out, header=False, index=True, sep='\t', mode='a')
        ## gene fpkm
        if self.option('express_method') == 'RSEM':
            gene_fpkm_matrix = os.path.join(exp_output, 'gene.fpkm.matrix')
            gene_fpkm_pd = pd.read_table(gene_fpkm_matrix, header=0, index_col=0)
            gene_fpkm_dicts = gene_fpkm_pd.to_dict('index')
            gene_group_fpkm = OrderedDict()
            for seq_id in sorted(gene_fpkm_dicts):
                tmp_exp_dict = gene_fpkm_dicts[seq_id]
                for group in group_dict:
                    if seq_id not in gene_group_fpkm:
                        gene_group_fpkm[seq_id] = dict()
                    gene_group_fpkm[seq_id].update(
                        {group: round(sum([tmp_exp_dict[x] for x in group_dict[group]]) / len(group_dict[group]), 4)})
            gene_group_pd = (pd.DataFrame(data=gene_group_fpkm, columns=gene_group_fpkm.keys())).T
            gene_fpkm_result = pd.concat([gene_info_pd, gene_fpkm_pd, gene_group_pd, gene_annot_pd], axis=1)
            gene_fpkm_out = os.path.join(exp_output, 'gene.fpkm.matrix.annot.xls')
            header = ['gene_id']
            header.extend(gene_fpkm_result.columns.tolist())
            with open(gene_fpkm_out, "w") as w:
                w.write("\t".join(header) + "\n")
            gene_fpkm_result.to_csv(gene_fpkm_out, header=False, index=True, sep='\t', mode='a')
        if self.option('level').lower() == 'transcript':
            ## transcript tpm
            transcript_tpm_matrix = os.path.join(exp_output, 'transcript.tpm.matrix')
            transcript_tpm_pd = pd.read_table(transcript_tpm_matrix, header=0, index_col=0)
            transcript_tpm_dicts = transcript_tpm_pd.to_dict('index')
            transcript_group_tpm = OrderedDict()
            for seq_id in sorted(transcript_tpm_dicts):
                tmp_exp_dict = transcript_tpm_dicts[seq_id]
                for group in group_dict:
                    if seq_id not in transcript_group_tpm:
                        transcript_group_tpm[seq_id] = dict()
                    transcript_group_tpm[seq_id].update(
                        {group: round(sum([tmp_exp_dict[x] for x in group_dict[group]]) / len(group_dict[group]), 4)})
            transcript_group_pd = (pd.DataFrame(data=transcript_group_tpm, columns=transcript_group_tpm.keys())).T
            transcript_tpm_result = pd.concat([trans_info_pd, transcript_tpm_pd, transcript_group_pd, trans_annot_pd],
                                              axis=1)
            transcript_tpm_out = os.path.join(exp_output, 'transcript.tpm.matrix.annot.xls')
            header = ['transcript_id']
            header.extend(transcript_tpm_result.columns.tolist())
            with open(transcript_tpm_out, "w") as w:
                w.write("\t".join(header) + "\n")
            transcript_tpm_result.to_csv(transcript_tpm_out, header=False, index=True, sep='\t', mode='a')
            ## transcript fpkm
            if self.option('express_method') == 'RSEM':
                transcript_fpkm_matrix = os.path.join(exp_output, 'transcript.fpkm.matrix')
                transcript_fpkm_pd = pd.read_table(transcript_fpkm_matrix, header=0, index_col=0)
                transcript_fpkm_dicts = transcript_fpkm_pd.to_dict('index')
                transcript_group_fpkm = OrderedDict()
                for seq_id in sorted(transcript_fpkm_dicts):
                    tmp_exp_dict = transcript_fpkm_dicts[seq_id]
                    for group in group_dict:
                        if seq_id not in transcript_group_fpkm:
                            transcript_group_fpkm[seq_id] = dict()
                        transcript_group_fpkm[seq_id].update({group: round(
                            sum([tmp_exp_dict[x] for x in group_dict[group]]) / len(group_dict[group]), 4)})
                transcript_group_pd = (pd.DataFrame(data=transcript_group_fpkm, columns=transcript_group_fpkm.keys())).T
                transcript_fpkm_result = pd.concat(
                    [trans_info_pd, transcript_fpkm_pd, transcript_group_pd, trans_annot_pd], axis=1)
                transcript_fpkm_out = os.path.join(exp_output, 'transcript.fpkm.matrix.annot.xls')
                header = ['transcript_id']
                header.extend(transcript_fpkm_result.columns.tolist())
                with open(transcript_fpkm_out, "w") as w:
                    w.write("\t".join(header) + "\n")
                transcript_fpkm_result.to_csv(transcript_fpkm_out, header=False, index=True, sep='\t', mode='a')
            ## transcript count
            transcript_count_matrix = os.path.join(exp_output, 'transcript.count.matrix')
            transcript_count_pd = pd.read_table(transcript_count_matrix, header=0, index_col=0)
            transcript_count_dicts = transcript_count_pd.to_dict('index')
            transcript_group_count = OrderedDict()
            for seq_id in sorted(transcript_count_dicts):
                tmp_exp_dict = transcript_count_dicts[seq_id]
                for group in group_dict:
                    if seq_id not in transcript_group_count:
                        transcript_group_count[seq_id] = dict()
                    transcript_group_count[seq_id].update(
                        {group: round(sum([tmp_exp_dict[x] for x in group_dict[group]]) / len(group_dict[group]), 4)})
            transcript_group_pd = (pd.DataFrame(data=transcript_group_count, columns=transcript_group_count.keys())).T
            transcript_count_result = pd.concat(
                [trans_info_pd, transcript_count_pd, transcript_group_pd, trans_annot_pd], axis=1)
            transcript_count_out = os.path.join(exp_output, 'transcript.count.matrix.annot.xls')
            header = ['transcript_id']
            header.extend(transcript_count_result.columns.tolist())
            with open(transcript_count_out, "w") as w:
                w.write("\t".join(header) + "\n")
            transcript_count_result.to_csv(transcript_count_out, header=False, index=True, sep='\t', mode='a')

    def merge_annotation_diffexp_matrix(self):
        if self.option("is_assemble"):
            annot = os.path.join(self.output_dir, 'annot_merge/allannot_class/all_annot.xls')
        else:
            annot = os.path.join(self.output_dir, 'annot_merge/refannot_class/all_annot.xls')
        all_annot = pd.read_table(annot, header=0, index_col=0)
        gene_annot_pd = all_annot[all_annot["is_gene"] == "yes"].drop(
            columns=['transcript_id', 'is_gene', 'gene_name', 'description', 'length'])
        order = ["nr", "go", "KO_id", "KO_name", "paths", "cog", "cog_description", "pfam", "swissprot", "entrez"]
        gene_annot_pd = pd.DataFrame(gene_annot_pd, columns=order)
        gene_info_pd = all_annot[all_annot['is_gene'] == 'yes'][['gene_name', 'description', 'length']]
        diff_output = self.diffexp.output_dir
        duplicate_files = glob.glob(diff_output + '/' + '*.annot.xls') + glob.glob(
            diff_output + '/' + '*_vs_*.normalize.xls') + glob.glob(diff_output + '/' + '*_vs_*.sizeFactor.xls')
        for file in duplicate_files:
            os.remove(os.path.join(diff_output, file))
        target_files = glob.glob(diff_output + "/*")
        for each in target_files:
            gene_pd = pd.read_table(each, header=0, index_col=0)
            gene_result = pd.concat([gene_info_pd, gene_pd, gene_annot_pd], join='inner', axis=1)
            gene_out = each.split('.xls')[0] + '.annot.xls'
            header = ['gene_id']
            header.extend(gene_result.columns.tolist())
            with open(gene_out, "w") as w:
                w.write("\t".join(header) + "\n")
            gene_result.to_csv(gene_out, header=False, index=True, sep='\t', mode='a')
