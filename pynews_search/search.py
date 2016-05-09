__author__ = 'salman'

import os
import pprint
import logging
from flask import Flask, request, render_template, abort
from flask.ext.pymongo import PyMongo

import werkzeug.exceptions as exceptions

app = Flask(__name__)

user = 'apiuser'
pwd = 'secret'
database = 'crawlerdb'

app.config['MONGO_URI'] = 'mongodb://' \
                          + user + ':' \
                          + pwd \
                          + '@aws-us-east-1-portal.11.dblayer.com:27786,aws-us-east-1-portal.10.dblayer.com:11136/' \
                          + database

mongo = PyMongo(app)

logger = logging.getLogger(__name__)


class KeyWordRequired(exceptions.HTTPException):
    code = 403
    description = '<p>Keywork parameter is required. Call the query as follows:' \
                  'http://<host:port>/search?keyword=<your_keyword></p>'


abort.mapping[403] = KeyWordRequired


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/search/', methods=['GET', 'POST'])
def search():
    keyword = None

    if request.method == 'POST':
        keyword = request.form['keyword']
    elif request.method == 'GET':
        keyword = request.args.get('keyword')

    if not keyword:
        abort(403)

    # print 'Search keyword={0}'.format(keyword.split(','))

    cursor = mongo.db.news.find(
        {'$text': {'$search': keyword}}
    )

    # print '\n\n'.join(pprint.pformat(document) for document in cursor)

    documents = []
    for doc in cursor:
        documents.append(doc)

    return render_template('results.html', keyword=keyword, documents=documents)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
