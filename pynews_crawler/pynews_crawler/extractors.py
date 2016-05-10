__author__ = 'salman'

from goose import Goose


class ArticleExtractor:
    def __init__(self):
        self.goose = Goose()

    def article_from_url(self, url):
        return self.goose.extract(url=url)

    def article_from_html(self, html):
        return self.goose.extract(raw_html=html)
