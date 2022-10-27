#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/7/22 12:31
# @Author  : U make me wanna surrender my soul
import scrapy
import pandas as pd
import re
import os
from KEGG.items import KeggItem, Keggimage, Keggkgml, Kegghtml


class KeggSpider(scrapy.Spider):
    '''
    spe_list: 物种列表 
    kegg_type: 要下载的kegg数据类型
    scrapy crawl kegg -a spe_list=all_species.list -a kegg_type=check_all
    scrapy crawl kegg -a spe_list=all_euk_spe -a kegg_type=check_all -a spe_group=Eukaryotes
    nohup scrapy crawl kegg -a spe_list=all_species.list -a kegg_type=check_all > check_html_kgml.5.log
    '''
    name = 'kegg'
    allowed_domains = ['rest.kegg.jp']

    def start_requests(self):

        if hasattr(self, "spe_list"):
            org_df = pd.read_csv(self.spe_list, sep='\t')
            org_df = org_df.fillna('nan')
            org_list = org_df["spe"].tolist()
        # for org in org_list:
        #    yield scrapy.Request(
        #        url='http://rest.kegg.jp/list/pathway/' + org,
        #        callback=self.parse
        #    )

        if hasattr(self, "kegg_type"):
            kegg_type = getattr(self, "kegg_type")
        else:
            kegg_type = "png"

        if kegg_type == "map":
            map_file = '/mnt/ilustre/users/ruiyang.gao/Database/KEGG/Map/map.txt'
            df_pathway = pd.read_csv(
                map_file,
                sep='\t', header=None
            )
            pathway_list = df_pathway[0].tolist()
            for id in pathway_list:
                id = id.split(':')[-1]
                if os.path.exists("/mnt/ilustre/users/ruiyang.gao/Database/KEGG/Map/{}.html".format(id)):
                    print("{} exists".format(id))
                    continue
                else:
                    print('https://www.kegg.jp/kegg-bin/show_pathway?' + id)
                    yield scrapy.Request(
                        url='https://www.kegg.jp/kegg-bin/show_pathway?' + id,
                        callback=self.parse4
                    )
        spe_group = "Prokaryotes"
        if hasattr(self, "spe_group"):
            spe_group = self.spe_group
        else:
            self.spe_group = "Prokaryotes"
        
        for org in org_list:
            pathway_file = '/mnt/ilustre/users/ruiyang.gao/Database/KEGG/OrgPathway/{}/'.format(spe_group) + org + r'/' + 'pathway_' + org + '.txt'
            if os.path.exists(pathway_file):
                pass
            else:
                print("{}\tnot exists pathways{}".format(org, pathway_file))
                continue
            df_pathway = pd.read_csv(
                pathway_file,
                sep='\t', header=None)
            # df_pathway = pd.read_csv('Deal_Error.txt', sep='\t')  # 正常爬取时注释此行
            
            pathway_list = df_pathway[0].tolist()

            if kegg_type == "check_all":
                path_num = len(pathway_list)
                png_retain = []
                html_retain = []
                kgml_retain = []

                apath = "/mnt/ilustre/users/ruiyang.gao/Database/KEGG/OrgPathway/{}/".format(spe_group) + org
                pathway_files = os.listdir(apath)
                for pathway in pathway_list:
                    if pathway.split(":")[-1] + ".png" not in pathway_files:
                        png_retain.append(pathway)
                    if pathway.split(":")[-1] + ".html" not in pathway_files:
                        html_retain.append(pathway)
                    if pathway.split(":")[-1] + ".kgml" not in pathway_files:
                        kgml_retain.append(pathway)

                    
                    if len(png_retain) == 0:
                        print("{} png complete".format(org))
                    else:
                        print("{} png not complete, {} retain".format(org, png_retain))
                        for path in png_retain:
                            yield scrapy.Request(
                                url='http://rest.kegg.jp/get/' + path + '/image',
                                callback=self.parse2
                            )

                    if len(kgml_retain) == 0:
                        print("{} kgml complete".format(org))
                    else:
                        print("{} kgml not complete, {} retain".format(org, kgml_retain))
                        for path in kgml_retain:
                            yield scrapy.Request(
                                url='http://rest.kegg.jp/get/' + path + '/kgml',
                                callback=self.parse3
                            )

                    if len(html_retain) == 0:
                        print("{} png complete".format(org))
                    else:
                        print("{} html not complete, {} retain".format(org, html_retain))
                        for path in html_retain:
                            id = pathway.split(":")[-1]
                            yield scrapy.Request(
                                url='https://www.kegg.jp/kegg-bin/show_pathway?' + id,
                                callback=self.parse4
                            )
            
            # image&kgml download
            for id in pathway_list:
                if kegg_type == "gene":
                    yield scrapy.Request(
                        url='http://rest.kegg.jp/get/' + id,
                        callback=self.parse1,
                    )
                elif kegg_type == "png":
                    yield scrapy.Request(
                        url='http://rest.kegg.jp/get/' + id + '/image',
                        callback=self.parse2
                    )
                elif kegg_type == "kgml":
                    yield scrapy.Request(
                        url='http://rest.kegg.jp/get/' + id + '/kgml',
                        callback=self.parse3
                    )
                elif kegg_type == "html":
                    id = id.split(':')[-1]
                    yield scrapy.Request(
                        url='https://www.kegg.jp/kegg-bin/show_pathway?' + id,
                        callback=self.parse4
                    )

    # 获取下载列表
    def parse(self, response, **kwargs):
        info_id = KeggItem()
        data = response.text
        id = response.url.split('/')[-1].split(':')[-1]
        print('pathway:', id)
        info_id['org'] = id
        info_id['data'] = data
        info_id['spe_group'] = self.spe_group 
        return info_id

    # 获取注释信息
    def parse1(self, response, **kwargs):
        info_id = KeggItem()
        data = response.text
        id = response.url.split('/')[-1].split(':')[1]
        org = ''.join(re.findall(r'[A-Za-z]', id))
        print('ann:', org, '***', id)
        info_id['org'] = org
        info_id['id'] = id
        info_id['data'] = data
        info_id['spe_group'] = self.spe_group
        return info_id

    # 获取图片
    def parse2(self, response, **kwargs):
        image_id = Keggimage()
        data = response.body
        id = response.url.split('/')[-2]
        id = id.split(':')[1]
        org = ''.join(re.findall(r'[A-Za-z]', id))
        print('image:', org, '***', id)
        image_id['org'] = org
        image_id['id'] = id
        image_id['image'] = data
        image_id['spe_group'] = self.spe_group
        return image_id

    # 获取kgml
    def parse3(self, response, **kwargs):
        kgml_id = Keggkgml()
        data = response.body
        id = response.url.split('/')[-2]
        id = id.split(':')[1]
        org = ''.join(re.findall(r'[A-Za-z]', id))
        print('kgml:', org, '***', id)
        kgml_id['org'] = org
        kgml_id['id'] = id
        kgml_id['kgml'] = data
        kgml_id['spe_group'] = self.spe_group
        return kgml_id

    # 获取html
    def parse4(self, response, **kwargs):
        html_id = Kegghtml()
        data = response.body
        id = response.url.split('?')[-1]
        org = ''.join(re.findall(r'[A-Za-z]', id))
        print('html:', org, '***', id)
        html_id['org'] = org
        html_id['id'] = id
        html_id['html'] = data
        html_id['spe_group'] = self.spe_group
        return html_id
