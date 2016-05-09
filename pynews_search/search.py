__author__ = 'salman'

import os
import pprint
import logging
from flask import Flask, request, redirect, abort
from flask.ext.pymongo import PyMongo

import werkzeug.exceptions as exceptions

app = Flask(__name__)

app.config[
    'MONGO_URI'] = 'mongodb://apiuser:secret@aws-us-east-1-portal.11.dblayer.com:27786,aws-us-east-1-portal.10.dblayer.com:11136/crawlerdb'

mongo = PyMongo(app)

logger = logging.getLogger(__name__)


class KeyWordRequired(exceptions.HTTPException):
    code = 403
    description = '<p>Keywork parameter is required. Call the query as follows:' \
                  'http://<host:port>/search?keyword=<your_keyword></p>'


abort.mapping[403] = KeyWordRequired


@app.route('/')
def welcome():
    abort(403)


@app.route('/search')
def search():
    print request.args
    keyword = request.args.get('keyword', None)

    if keyword is None:
        abort(403)

    logger.debug('Looking for keywords={0}'.format(keyword.split(',')))

    cursor = mongo.db.news.find(
        {'$text': {'$search': keyword}},
        fields=({'title': 1, 'body': 1, 'score': {'$meta': 'textScore'}})
    )
    return '<br><br>'.join(pprint.pformat(document) for document in cursor)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
