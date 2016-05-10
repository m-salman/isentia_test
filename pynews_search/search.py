__author__ = 'salman'

import logging
from flask import Flask, request, render_template, abort
from flask.ext.pymongo import PyMongo

import werkzeug.exceptions as exceptions

username = 'apiuser'
password = 'secret'
database = 'crawlerdb'
host = '0.0.0.0'
port = 5000

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://' \
                          + username + ':' \
                          + password \
                          + '@aws-us-east-1-portal.11.dblayer.com:27786,aws-us-east-1-portal.10.dblayer.com:11136/' \
                          + database

mongo = PyMongo(app)

logger = logging.getLogger(app.name)


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
    phrase_search = 'off'

    if request.method == 'POST':
        keyword = request.form['keyword']
        phrase_search = request.form.get('phrase')
    elif request.method == 'GET':
        keyword = request.args.get('keyword')
        phrase_search = request.args.get('phrase')

    if not keyword:
        abort(403)

    if phrase_search == 'on':
        keyword = '\"' + keyword + '\"'

    logger.debug('Search keyword={0}'.format(keyword))

    # TODO: Paginate the results
    cursor = mongo.db.news.find(
        {'$text': {'$search': keyword }}
    )

    documents = []

    if cursor.count():
        for document in cursor:
            documents.append(document)
    else:
        documents = None

    return render_template('results.html', keyword=keyword, documents=documents)


if __name__ == "__main__":
    app.run(host=host, port=port, debug=False)
