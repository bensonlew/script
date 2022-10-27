# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class KeggItem(scrapy.Item):
    # define the fields for your item here like:
    org = scrapy.Field()
    id = scrapy.Field()
    data = scrapy.Field()
    spe_group = scrapy.Field()

class Keggimage(scrapy.Item):
    org = scrapy.Field()
    id = scrapy.Field()
    image = scrapy.Field()
    spe_group = scrapy.Field()


class Keggkgml(scrapy.Item):
    org = scrapy.Field()
    id = scrapy.Field()
    kgml = scrapy.Field()
    spe_group = scrapy.Field()


class Kegghtml(scrapy.Item):
    org = scrapy.Field()
    id = scrapy.Field()
    html = scrapy.Field()
    spe_group = scrapy.Field()
