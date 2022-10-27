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


class Keggimage(scrapy.Item):
    id = scrapy.Field()
    image = scrapy.Field()


class Keggkgml(scrapy.Item):
    id = scrapy.Field()
    kgml = scrapy.Field()
