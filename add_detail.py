# -*- coding: utf-8 -*-
# __author__ = 'liubinxu'
import random
import json
import datetime
import os
from bson.objectid import ObjectId
from mbio.workflows.single import SingleWorkflow
from biocluster.wsheet import Sheet
import sys
from mbio.packages.rna.annot_config import AnnotConfig

monogo_dic = {
    "_id" : ObjectId("62426e746c3293c999d9b3a9"),
    "status" : "true",
    "chloroplast" : "no",
    "medical" : True,
    "accession" : "GRCm39",
    "common_name" : "小鼠",
    "cds" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/cds/cds.fa",
    "go" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/GO/go.list",
    "organism_name" : "Mus_musculus",
    "size" : 2601.83568096161,
    "ensemble2entrez" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/NCBI/mmusculus_gene_ensembl_entrez.txt",
    "index" : "Mus_musculus.GRCm39.dna.primary_assembly",
    "lnc_dir" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/lncrna",
    "g2t2p" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/Annotation_v2/g2t2p.txt",
    "gtf" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/gtf/Mus_musculus.GRCm39.105.gtf",
    "transcript" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/dna/transcript.fa",
    "ribosome" : "yes",
    "pep" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/cds/pep.fa",
    "ensemble_web" : "http://asia.ensembl.org/Mus_musculus/Info/Index",
    "dna_index" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/dna/Mus_musculus.GRCm39.dna.primary_assembly",
    "secret" : "false",
    "version" : "v2",
    "kegg_genome_name" : "",
    "recommend" : "false",
    "taxon_id" : "10090",
    "cellranger_mkref" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/cellranger_mkref",
    "level_file" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/gtf/chr.list",
    "gene_stat" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/gtf/Mus_musculus.GRCm39.105.gtf.genome_stat.xls",
    "annot_version" : "ensembl_105",
    "kegg" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/KEGG/Mus_musculus.pathway",
    "assembly" : "GRCm39",
    "kegg_genome_abr" : "mmu",
    "bio_mart_annot" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/biomart/biomart.sortu.txt",
    "remark" : "20220328",
    "scrna" : True,
    "created_ts" : "2022-03-29 10:27:00",
    "dna_fa" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/dna/Mus_musculus.GRCm39.dna.primary_assembly.fa",
    "trans_biotype" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/biotype/trans_biotype.txt",
    "ensemble_class" : "vertebrates",
    "genome_id" : "GM1510",
    "anno_path_v2" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/Annotation_v2",
    "database_version" : {
        "pfam" : "34.0",
        "uniprot" : "202109",
        "kegg" : "202109",
        "eggnog" : "202006",
        "string" : "2019",
        "pir" : "202106",
        "swissprot" : "202106",
        "ncbi_taxonomy" : "202109",
        "cog" : "2020",
        "go" : "20210918",
        "rfam" : "14.6",
        "nr" : "202110"
    },
    "annot_group" : "REFRNA_GROUP_202110",
    "merge_type" : "partial",
    "kegg_use" : "mmu",
    "name" : "Mus_musculus",
    "level" : "Chromosome",
    "raw_input" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/workflow_results/raw.tar.gz",
    "mitochondria" : "yes",
    "RBC" : "yes",
    "taxon" : "Animal",
    "ensemble_release" : "GRCm39_ensembl_105_20220328",
    "gene_biotype" : "vertebrates/Mus_musculus/GRCm39_ensembl_105_20220328/biotype/gene_biotype.txt",
    "biomart_gene_annotype" : "type1",
    "ncbi_ensemble_tax" : "10090",
    "release_date" : ""
}




database_dir = "/mnt/lustre/users/sanger-dev/app/database/Genome_DB_finish/"

def run_annot(monogo_dic):
    if monogo_dic["ensemble_class"].lower() in ["animals", "vertebrates"]:
        taxonomy = "Animals"
    elif monogo_dic["ensemble_class"].lower() == "plants":
        taxonomy = "Plants"
    elif monogo_dic["ensemble_class"].lower() == "protists":
        taxonomy = "Protists"
    else:
        taxonomy = "Fungi"


    if monogo_dic["annot_group"] in ["REFRNA_GROUP_202110"]:
        diamond_version = "v2.0.13"
    else:
        diamond_version = "v0.9.24.125"

    annot_config_dict = AnnotConfig().get_group_option_detail(mongo_dict["annot_group"])

    data = {
        'id': 'scrna_annot_{}_{}'.format(monogo_dic["genome_id"], random.randint(1000, 9999)),
        'type': 'module',
        'name': 'ref_genome_db_medical.ref_db_annotation',
        'instant': False,
        'options': {
            'ref_fa': database_dir + monogo_dic["dna_fa"],
            'gtf': database_dir + monogo_dic["gtf"],
            'pep': database_dir + monogo_dic["pep"],
            'species_name': monogo_dic["organism_name"],
            'biomart': database_dir + monogo_dic["bio_mart_annot"],
            'biomart_type': monogo_dic["biomart_gene_annotype"],
            'enterz': database_dir + monogo_dic["ensemble2entrez"],
            'taxonomy': taxonomy,
            'species_class': monogo_dic["ensemble_class"],
            'trans': database_dir + monogo_dic["transcript"],
            "known_ko": database_dir + monogo_dic["kegg"],
            "known_go": database_dir + monogo_dic["go"],
            'g2t2p': database_dir + monogo_dic["g2t2p"],
            'diamond_version': diamond_version,
            'kegg_version': annot_config_dict['kegg']['version'],
            "nr_version" : annot_config_dict['nr']['version'],
            "eggnog_version" : annot_config_dict['eggnog']['version'],
            "string_version" : annot_config_dict['string']['version'],
            "pir_version" : annot_config_dict['pir']['version'],
            "pfam_version" : annot_config_dict['pfam']['version'],
            "swissprot_version" : annot_config_dict['swissprot']['version']
        }
    }
    home = os.environ["HOME"]
    data["work_dir"] = os.path.join(home, "wpm2/workspace/{}/{}".format(datetime.datetime.now().strftime("20%y%m%d"), data["id"]))
    with open(home + "/app/bioinfo/test/test.model.json", 'r') as f:
        json_obj =  json.load(f)

    json_obj.update(data)


    with open(data["id"] + ".json", 'w') as f:
        f.write(json.dumps(json_obj, indent=4))
    os.system("~/wpm2/bin/run_work -j {}.json".format(data["id"]))

def run_detail(monogo_dic):
    data = {
        'id': 'scrna_detail_{}_{}'.format(monogo_dic["genome_id"], random.randint(1000, 9999)),
        'type': 'tool',
        'name': 'ref_genome_db_v2.detail',
        'instant': False,
        'options': {
            'ref_genome_custom':  database_dir + monogo_dic["dna_fa"],
            'ref_new_gtf': database_dir + monogo_dic["gtf"],
            'biomart_file': database_dir + monogo_dic["bio_mart_annot"],
            'annotation': database_dir + monogo_dic["anno_path_v2"] + '/annot_class_medical/all_annot_gene.xls',
            'biomart_type': monogo_dic["biomart_gene_annotype"],
            'known_cds': database_dir + monogo_dic["cds"],
            'known_pep': database_dir + monogo_dic["pep"],
            'txpt_fa':database_dir + monogo_dic["transcript"],
            'g2t2p': database_dir + monogo_dic["g2t2p"]

        }
    }
    home = os.environ["HOME"]
    data["work_dir"] = os.path.join(home, "wpm2/workspace/{}/{}".format(datetime.datetime.now().strftime("20%y%m%d"), data["id"]))
    with open(home + "/app/bioinfo/test/test.model.json", 'r') as f:
        json_obj =  json.load(f)

    json_obj.update(data)


    with open(data["id"] + ".json", 'w') as f:
        f.write(json.dumps(json_obj, indent=4))
    os.system("~/wpm2/bin/run_work -j {}.json".format(data["id"]))

if __name__ == '__main__':
    with open(sys.argv[2], 'r') as f:
        mongo_dict = json.load(f)
    if sys.argv[1] == "run_annot":
        run_annot(mongo_dict)
    elif sys.argv[1] == "run_detail":
        run_detail(mongo_dict)
    else:
        print("run_annot or run_detail")