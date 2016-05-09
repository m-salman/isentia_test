__author__ = 'salman'

import StringIO

import scrapy
import scrapy.spiders
from scrapy.linkextractors import LinkExtractor
from pynews_crawler.items import NewsItem


class BBCNewsSpider(scrapy.spiders.CrawlSpider):
    name = 'bbcnews'
    start_urls = ['http://www.bbc.com/news']
    allowed_domains = ['bbc.com', 'bbc.co.uk']
    rules = (
        scrapy.spiders.Rule(LinkExtractor(allow='news/.*'), callback='crawl_item', follow=True),
    )

    def crawl_item(self, response):
        self.logger.info('Scraping: <%s>' % response.url)
        item = NewsItem()
        item['url'] = response.url
        # Note that entire response is being thrown down the pipeline,
        # article extraction is done using Goose.
        item['article_text'] = StringIO.StringIO(response.body)
        return item
