__author__ = 'salman'

import scrapy


class NewsItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    authors = scrapy.Field()
    publish_date = scrapy.Field()
    article_text = scrapy.Field()
    meta_description = scrapy.Field()
