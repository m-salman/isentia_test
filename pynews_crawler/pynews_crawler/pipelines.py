__author__ = 'salman'

import pymongo
import pymongo.errors

from scrapy import signals
from scrapy.exceptions import DropItem

import goose
import logging
import datetime


class ExtractArticlePipeLine(object):
    """
    Extract articles from crawled items.
    """

    def __init__(self):
        self.goose = goose.Goose()

    def process_item(self, item, spider):
        self.logger = logging.getLogger(spider.name)

        self.logger.info('Extracting :<{0}>'.format(item['url']))

        # Pass raw html Goose
        article = self.goose.extract(raw_html=item['article_text'].getvalue())

        if not article.cleaned_text:
            raise DropItem('Article extraction failure: <{0}>'.format(item['url']))

        # Depending on the spider and site, some feilds might not be populated
        item['title'] = article.title
        item['authors'] = ','.join(article.authors)
        item['publish_date'] = article.publish_date
        item['article_text'] = article.cleaned_text
        item['meta_description'] = article.meta_description

        self.logger.debug('Article extracted! Spider:<{0}> URL:<{1}>'.format(spider.name, item['url']))

        return item


class MongoDBPipeLine(object):
    """
    Insert processed news items into mongodb.
    """

    current_item = 0
    item_buffer = []

    # Default configuration options. Override using settings.py
    config = {
        'uri': 'mongodb://<user>:<password>@localhost:27017/<database>',
        'user': 'spider',
        'password': 'secret',
        'database': 'crawlerdb',
        'collection': 'news',
        'fsync': False,
        'write_concern': 0,
        'replica_set': None,
        'add_time_stamp': False,
        'unique_key': None,
        'data_buffer': None,
        'index_search_fields': None,
        'index_field_weights': None
    }

    def process_item(self, item, spider):
        """ Process the news item for mongodb.
        Insert the item into mongodb or insert it into the data buffer.

        :param item: the news item to process
        :param spider: the spider running the queries
        :return:
        """
        if self.config['data_buffer']:
            self.current_item += 1

            # Place the item in buffer. Add timestamp if applicable.
            item = dict(item)
            if self.config['add_time_stamp']:
                item['time_stamp'] = datetime.datetime.utcnow()

            self.item_buffer.append(item)

            if self.current_item == self.config['data_buffer']:
                self.current_item = 0
                self.insert_item(self.item_buffer, spider)
                self.item_buffer = []
            return item

        return self.insert_item(item, spider)

    def insert_item(self, item, spider):
        """ Insert item(s) to MongoDB

        :param item: A single item or list of buffered items to put into mongodb.
        :param spider: The spider running the queries
        :returns: Item object
        """
        is_buffered = isinstance(item, list)

        if not is_buffered and self.config['add_time_stamp']:
            item['time_stamp'] = datetime.datetime.utcnow()

        try:
            self.collection.insert_many(item) if is_buffered else self.collection.insert_one(dict(item))
        except pymongo.errors.DuplicateKeyError:
            # TODO: duplicate key error is a corner case (index created and then turned off),
            # TODO: drop the index when unique key not specified to fix this issue
            raise DropItem('Duplicate key error! Dropping item: {0}'.format(item[self.config['unique_key']]))

        stored_items = len(item) if is_buffered else 1
        self.logger.info('Storing {0} item(s) in MongoDB => [{1}/{2}]'.format(stored_items,
                                                                              self.config['database'],
                                                                              self.config['collection']))
        return item

    def configure_mongodb_settings(self):
        """ Configure MongoDB settings from scrapy settings

        :raise SyntaxError: Error raised for illegal configuration
        """
        options = [
            ('uri', 'MONGODB_URI'),
            ('user', 'MONGODB_USER'),
            ('password', 'MONGODB_PWD'),
            ('database', 'MONGODB_DATABASE'),
            ('collection', 'MONGODB_COLLECTION'),
            ('fsync', 'MONGODB_FSYNC'),
            ('write_concern', 'MONGODB_REPLICA_SET_W'),
            ('replica_set', 'MONGODB_REPLICA_SET'),
            ('data_buffer', 'MONGODB_DATA_BUFFER'),
            ('add_time_stamp', 'MONGODB_ADD_TIMESTAMP'),
            ('unique_key', 'MONGODB_UNIQUE_KEY'),
            ('index_search_fields', 'MONGOBD_INDEX_FIELDS'),
            ('index_field_weights', 'MONGODB_INDEX_WEIGHTS')
        ]

        for key, setting in options:
            if self.settings[setting]:
                self.config[key] = self.settings[setting]

        self.logger.info('MongoDB configuration = {0}'.format(self.config))

        if self.config['data_buffer'] and self.config['unique_key']:
            self.logger.error('ConfigError: Cannot set both MONGODB_DATA_BUFFER and MONGODB_UNIQUE_KEY')
            raise SyntaxError('IllegalConfig: Setting both MONGODB_DATA_BUFFER and MONGODB_UNIQUE_KEY is not supported')

    @classmethod
    def from_crawler(cls, crawler):
        """ Called when a crawler fires up. Use this to connect signals to your code

        :param crawler: The crawler being instantiated
        :return:
        """
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        """ Callback invoked when a spider starts running queries.

        :param spider: The spider running the queries
        """
        self.logger = logging.getLogger(spider.name)

        self.logger.info('Spider opened: {0}'.format(spider.name))
        self.crawler = spider.crawler
        self.settings = spider.settings
        self.configure_mongodb_settings()

        self.logger.debug('Connecting to MongoDB...')
        if self.config['replica_set'] is not None:
            connection = pymongo.MongoClient(self.config['uri'], replicaSet=self.config['replica_set'],
                                             w=self.config['write_concern'], fsync=self.config['fsync'],
                                             read_preference=pymongo.ReadPreference.PRIMARY_PREFERRED)
        else:
            connection = pymongo.MongoClient(self.config['uri'], fsync=self.config['fsync'],
                                             read_preference=pymongo.ReadPreference.PRIMARY)

        database = connection[self.config['database']]
        self.collection = database[self.config['collection']]
        self.logger.info('Connected to MongoDB! URI: {0}, <"{1}/{2}">'.format(self.config['uri'],
                                                                              self.config['database'],
                                                                              self.config['collection']))

        if self.config['unique_key']:
            self.collection.create_index(self.config['unique_key'], unique=True)
            self.logger.info('Create unique index on key:{0}'.format(self.config['unique_key']))

            # Use search index for faster searching.
        if self.config['index_search_fields']:
            self.collection.create_index(self.config['index_search_fields'],
                                         weights=self.config['index_field_weights'],
                                         name='text_index')
            self.logger.info(
                'Creating text search index for fields: {0}'.format(self.config['index_field_weights'].keys()))

    def spider_closed(self, spider):
        """ Callback invoked when spider is closed.

        Used to clean up or pump the buffered items to mongodb on spider closed.

        :param spider: The spider running the queries
        """
        self.logger.debug('Closed spider: {0}!'.format(spider.name))
        if self.item_buffer:
            self.insert_item(self.item_buffer, spider)
