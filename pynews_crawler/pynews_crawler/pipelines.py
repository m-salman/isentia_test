__author__ = 'salman'

import pymongo
import pymongo.errors

from scrapy import signals
from scrapy.exceptions import DropItem

import goose
import logging
import datetime

logger = logging.getLogger(__name__)


class ExtractArticlePipeLine(object):
    def __init__(self):
        self.goose = goose.Goose()

    def process_item(self, item, spider):
        logger.debug('Extracting article. Spider:<{0}> URL:<{1}>'.format(spider.name, item['url']))

        # Pass raw html Goose
        article = self.goose.extract(raw_html=item['article_text'].getvalue())

        if not article.cleaned_text:
            raise DropItem('Failed to extract cleaned text from {0}'.format(item['url']))

        # Depending on the spider and site, some feilds might not be populated
        item['title'] = article.title
        item['authors'] = ','.join(article.authors)
        item['publish_date'] = article.publish_date
        item['article_text'] = article.cleaned_text
        item['meta_description'] = article.meta_description

        logger.debug('Article extracted! URL:<{0}>'.format(item['url']))

        return item


class MongoDBPipeLine(object):

    # Default configuration options. Override using settings.py
    config = {
        'uri': 'mongodb://<user>:<password>@localhost:27017/<database>',
        'index_search_fields': None,
        'index_field_weights': None,
        'database': 'crawldb',
        'collection': 'news',
        'fsync': False,
        'write_concern': 0,
        'replica_set': None,
        'buffer_size': None,
        'add_time_stamp': False,
        'unique_key': None,
    }

    # Item buffer_size
    current_item = 0
    item_buffer = []

    def process_item(self, item, spider):
        if self.config['buffer_size']:
            self.current_item += 1

            item = dict(item)
            # Buffered items get time stamped now
            if self.config['add_time_stamp']:
                item['time_stamp'] = datetime.datetime.utcnow()

            self.item_buffer.append(item)

            if self.current_item == self.config['buffer_size']:
                self.current_item = 0
                # Push buffered items to MongoDB
                self.insert_item(self.item_buffer, spider)
                self.item_buffer = []
            return item

        # Insert and return a single item
        return self.insert_item(item, spider)

    def insert_item(self, item, spider):
        """ Insert item(s) to MongoDB

        :param item: A single item or list of buffered items to put into mongo
        :param spider: The spider running the queries
        :returns: Item object
        """
        is_buffered = isinstance(item, list)

        if not is_buffered and self.config['add_time_stamp']:
            item['time_stamp'] = datetime.datetime.utcnow()

        if self.config['unique_key']:

            if is_buffered:
                filter_key = {
                    self.config['unique_key']: [buffer_item[self.config['unique_key']] for buffer_item in item]}
                self.collection.update_many(filter_key, {"$set": item}, upsert=True)
            else:
                filter_key = {self.config['unique_key']: item[self.config['unique_key']]}
                self.collection.update_one(filter_key, {"$set": dict(item)}, upsert=True)

        else:

            try:
                self.collection.insert_many(item) if is_buffered else self.collection.insert_one(dict(item))
            except pymongo.errors.DuplicateKeyError:
                # the duplicate key error is a corner case where unique index was created on a field
                # and then not removed from mongodb
                raise DropItem('Duplicate key found. Dropping item. Key:{0}'.format(item[self.config['unique_key']]))

        logger.info(
            'Storing item(s) in MongoDB => [{0}/{1}]'.format(self.config['database'], self.config['collection']))
        return item

    def configure_settings(self):
        """ Configure the MongoDB connection """

        options = [
            ('uri', 'MONGODB_URI'),
            ('index_search_fields', 'MONGOBD_INDEX_FIELDS'),
            ('index_field_weights', 'MONGODB_INDEX_WEIGHTS'),
            ('database', 'MONGODB_DATABASE'),
            ('collection', 'MONGODB_COLLECTION'),
            ('fsync', 'MONGODB_FSYNC'),
            ('write_concern', 'MONGODB_REPLICA_SET_W'),
            ('replica_set', 'MONGODB_REPLICA_SET'),
            ('buffer_size', 'MONGODB_DATA_BUFFER'),
            ('add_time_stamp', 'MONGODB_ADD_TIMESTAMP'),
            ('unique_key', 'MONGODB_UNIQUE_KEY')
        ]

        for key, setting in options:
            if self.settings[setting]:
                self.config[key] = self.settings[setting]

        logger.info('Mongo pipeline configuration= {0}'.format(self.config))

        # Check for illegal configuration
        if self.config['buffer_size'] and self.config['unique_key']:
            logger.error('ConfigError: Cannot set both MONGODB_DATA_BUFFER and MONGODB_UNIQUE_KEY')
            raise SyntaxError('IllegalConfig: Setting both MONGODB_DATA_BUFFER and MONGODB_UNIQUE_KEY is not supported')

    #
    # Spider event handling for Mongo pipeline. Ensure that spider stops crawling if there's an issue
    # in MongoDB, too many duplicates etc. We already have duplicate filtering at crawl settings.
    #

    @classmethod
    def from_crawler(cls, crawler):
        """ Called when a crawler fires up. Use this to connect callbacks etc.

        :param crawler: the crawler object
        :return:
        """
        logger.info('Crawler class method invoked.')
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        """ Callback invoked when a spider is opened

        :param spider:The spider running the queries
        """
        logger.info('Spider opened: {0}'.format(spider.name))
        self.crawler = spider.crawler
        self.settings = spider.settings

        # Configure mongodb and enable replication
        logger.info('Configuring settings for spider: {0}'.format(spider.name))
        self.configure_settings()

        if self.config['replica_set'] is not None:
            connection = pymongo.MongoClient(self.config['uri'], replicaSet=self.config['replica_set'],
                                             w=self.config['write_concern'], fsync=self.config['fsync'],
                                             read_preference=pymongo.ReadPreference.PRIMARY_PREFERRED)
        else:
            # No replication, connect to MongoDB server normally
            connection = pymongo.MongoClient(self.config['uri'], fsync=self.config['fsync'],
                                             read_preference=pymongo.ReadPreference.PRIMARY)

        # Set up the collection
        database = connection[self.config['database']]
        # database.authenticate('scrapy', 'scrapy')
        self.collection = database[self.config['collection']]
        logger.info('Connected to MongoDB: {0}, "{1}/{2}"'.format(self.config['uri'],
                                                                  self.config['database'],
                                                                  self.config['collection']))

        if self.config['unique_key']:
            self.collection.create_index(self.config['unique_key'], unique=True)
            logger.info('Create unique index on key:{0}'.format(self.config['unique_key']))

            # Use search index for faster searching.
        if self.config['index_search_fields']:
            self.collection.create_index(self.config['index_search_fields'],
                                         weights=self.config['index_field_weights'],
                                         name='text_index')
            logger.info('Creating text search index for fields: {0}'.format(self.config['index_field_weights'].keys()))

    def spider_closed(self, spider):
        """ Callback invoked when spider is closed.
        Used to clean up or pump the buffered items to mongo.

        :param spider: The spider running the queries
        """
        logger.debug('Closed spider: {0}!'.format(spider.name))
        if self.item_buffer:
            self.insert_item(self.item_buffer, spider)
