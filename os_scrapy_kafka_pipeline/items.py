# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapyKafkaPipelineItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    url = scrapy.Field()


class ExampleItem(scrapy.Item):
    # auto generated by os-scrapy-cookiecutter
    url = scrapy.Field()
    request_headers = scrapy.Field()
    response_headers = scrapy.Field()
    status = scrapy.Field()
    meta = scrapy.Field()
    body = scrapy.Field()
