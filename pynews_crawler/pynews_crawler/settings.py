#
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
MONGOBD_INDEX_FIELDS = [('title', 'text'), ('body', 'text')]
MONGODB_INDEX_WEIGHTS = {'title': 100, 'body': 25}
# MONGODB_DATA_BUFFER is not supported with MONGODB_UNIQUE_KEY. Please pick one.
# MONGODB_UNIQUE_KEY = 'url'
MONGODB_DATA_BUFFER = 10


# Responsible crawling :)
USER_AGENT = 'pynews bot (http://github.com/m-salman/isentia_test)'
CONCURRENT_REQUESTS = 16
DEPTH_LIMIT = 5
DOWNLOAD_DELAY = 5
CONCURRENT_REQUESTS_PER_DOMAIN = 16

# Configure item pipelines
ITEM_PIPELINES = {
    'pynews_crawler.pipelines.ExtractArticlePipeLine': 100,
    'pynews_crawler.pipelines.MongoDBPipeLine': 200
}

# Disable telnet console etc.
TELNETCONSOLE_ENABLED = False

# Configure HTTP caching
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [301, 404, 500, 501]
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
