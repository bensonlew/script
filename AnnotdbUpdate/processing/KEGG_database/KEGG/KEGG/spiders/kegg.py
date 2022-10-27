#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2021/7/22 12:31
# @Author  : U make me wanna surrender my soul
import scrapy
import pandas as pd

from KEGG.items import KeggItem, Keggimage, Keggkgml


class KeggSpider(scrapy.Spider):
    name = 'kegg'

    allowed_domains = ['rest.kegg.jp']

    # start_urls = ['http://rest.kegg.jp/get/']

    def start_requests(self):
        # org_df = pd.read_csv(r'E:\KEGG_Database\Eukaryotes\Eukaryotes.txt', header=None, sep='\t')
        # org_list = org_df[1].tolist()
        # # org_list = ['bbub', 'bacu','peu']
        # #
        # # for org in org_list:
        # #     yield scrapy.Request(
        # #         url='http://rest.kegg.jp/list/pathway/' + org,
        # #         callback=self.parse
        # #     )
        # for org in org_list:
        #     df_gene = pd.read_csv(r'E:\\KEGG_Database\\Eukaryotes\\' + org + r'\\' + org + '.txt', sep='\t',
        #                           header=None)
        #     # df_pathway = pd.read_csv(r'E:\KEGG_Database\Eukaryotes\aaf\pathway_aaf.txt', sep='\t', header=None)
        #     id_list = df_gene[0].tolist()
        #     # pathway_list = df_pathway[0].tolist()
        #     # id_list = []
        error_file = pd.read_csv(r'D:\PyChramProject\KEGG_database\Deal_Error.txt', sep='\t')
        error_list = error_file['ID'].tolist()
        for error in error_list:
            yield scrapy.Request(
                url=error,
                callback=self.parse1,
            )
            # yield scrapy.Request(
            #     url='http://rest.kegg.jp/get/' + pathway + '/image',
            #     callback=self.parse2
            # )
            # yield scrapy.Request(
            #     url='http://rest.kegg.jp/get/' + pathway + '/kgml',
            #     callback=self.parse3
            # )

    # 获取下载列表
    def parse(self, response, **kwargs):
        info_id = KeggItem()
        data = response.text
        id = response.url.split('/')[-1].split(':')[-1]
        print('pathway:', id)
        info_id['org'] = id
        info_id['data'] = data
        return info_id

    # 获取注释信息
    def parse1(self, response, **kwargs):
        info_id = KeggItem()
        data = response.text
        id = response.url.split('/')[-1].split(':')[-1]
        org = response.url.split('/')[-1].split(':')[0]
        print(org, ':', id)
        info_id['org'] = org
        info_id['id'] = id
        info_id['data'] = data
        return info_id

    # 获取图片
    def parse2(self, response, **kwargs):
        image_id = Keggimage()
        data = response.body
        id = response.url.split('/')[-2].split(':')[-1]
        print('image:', id)
        image_id['id'] = id
        image_id['image'] = data
        return image_id

    # 获取kgml
    def parse3(self, response, **kwargs):
        kgml_id = Keggkgml()
        data = response.body
        id = response.url.split('/')[-2].split(':')[-1]
        print('kgml:', id)
        kgml_id['id'] = id
        kgml_id['kgml'] = data
        return kgml_id
