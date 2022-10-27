# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import os
from KEGG.items import KeggItem, Keggimage, Keggkgml


def create_dir(path):
    """
    创建文件夹
    :return:
    """
    # 去除首位空格
    path = path.strip()
    # 去除尾部 \ 符号
    # path = path.rstrip("\\")
    path = path.rstrip("/")
    # 判断路径是否存在
    isExists = os.path.exists(path)
    # 判断结果
    if not isExists:
        # 如果不存在则创建目录
        # 创建目录操作函数
        os.makedirs(path)
        # print(path + ' 创建成功')
        return True
    else:
        # 如果目录存在则不创建，并提示目录已存在
        # print(path + ' 目录已存在')
        return False


class KeggPipeline:
    def process_item(self, item, spider):
        if isinstance(item, KeggItem):
            # 注释信息存放路径
            # apath = r"E:\\KEGG_Database\\Eukaryotes\\" + item['org'] + r"\\"
            apath = r"/mnt/ilustre/users/ruiyang.gao/Database/KEGG/Prokaryotes/" + item['org'] + r"/"
            # 物种注释信息文件
            wenjian = apath + item['id']
            create_dir(apath)
            with open(wenjian, 'w') as f:
                f.write(item['data'])
        elif isinstance(item, Keggimage):
            # 物种名字的文件夹
            apath = r"E:\\KEGG_Database\\Eukaryotes\\aaf\\"
            # 物种图片
            image = apath + item["id"] + '.png'
            with open(image, 'wb') as img:
                img.write(item['image'])
        elif isinstance(item, Keggkgml):
            apath = r"E:\\KEGG_Database\\Eukaryotes\\aaf\\"
            # 图片的xml格式
            kgml = apath + item['id'] + '.kgml'
            with open(kgml, 'wb') as xml:
                xml.write(item['kgml'])
        return item
