# -*- coding: utf-8 -*-
# Scrapy settings for pynews_crawler project
#

# BOT settings
BOT_NAME = 'pynews_crawler'

# Spiders
SPIDER_MODULES = ['pynews_crawler.spiders']
NEWSPIDER_MODULE = 'pynews_crawler.spiders'

# Logging settings
LOG_LEVEL = 'INFO'

# MongoDB settings
MONGODB_URI = 'mongodb://spider:secret@aws-us-east-1-portal.11.dblayer.com:27786,aws-us-east-1-portal.10.dblayer.com:11136/crawlerdb'
MONGODB_DATABASE = 'crawlerdb'
MONGODB_COLLECTION = 'news'
MONGODB_
MONGODB_DATA_BUFFER = 10
MONGOBD_INDEX_FIELDS = [('title', 'text'), ('body', 'text')]
MONGODB_INDEX_WEIGHTS = {'title': 100, 'body': 25}

USER_AGENT = 'pynews bot (http://github.com/pynews_crawler)'

# Concurrent requests
CONCURRENT_REQUESTS = 16
DEPTH_LIMIT = 5
DOWNLOAD_DELAY = 5
CONCURRENT_REQUESTS_PER_DOMAIN = 16

TELNETCONSOLE_ENABLED = False

# Configure item pipelines
ITEM_PIPELINES = {
    'pynews_crawler.pipelines.ExtractArticlePipeLine': 100,
    'pynews_crawler.pipelines.MongoDBPipeLine': 200
}

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [301, 404, 500, 501]
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'


# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
# NOTE: AutoThrottle will honour the standard settings for concurrency and delay
# AUTOTHROTTLE_ENABLED=True
# The initial download delay
# AUTOTHROTTLE_START_DELAY=5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY=60
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG=False
