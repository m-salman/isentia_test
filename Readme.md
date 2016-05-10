# Python News Crawler and Search

A news crawler written in python using Scrapy, Compose MongoDB and Flask.

## Getting Started

The project was built using Python 2.7.11, so it is recommended to use the latest 2.x version. Please see the diagram in docs/ folder to get a high level idea of the components involved. To get started, please grab a copy of both pynews_crawler and pynews_search code. It's always a good practice to setup a seperate virtual envionrment for eah project. To setup a virtual enviornment, in the project directory please go:

```
pip install virtualenv
virtualenv venv
```

This will create a virtual enviornment folder in the current directory which will contain the Python executable files, and a copy of the pip library which you can use to install other packages. To activate the virtual enviornment, go:

```
source venv/bin/activate
```


### Prerequisities

The pynews_crawler project requires Scrapy, PyMongo and Goose. The pynews_search project requires Flask-PyMongo.

The requirements.txt files in pynews_crawler and pynews_search folder can be used to install prerequisities for each project. To install prerequisities, go:

```
pip install -r pynews_crawl/requirements.txt
pip install -r pynews_search/requirements.txt
```

### Installing

###### pynews_crawler
There's a spider for BBC news already provided in pynews_crawler/spiders. You can generate your spiders as well. You can configure settings for the spiders using _settings.py_ file. You can configure crawl depth, number of consective requests and download delay. To run the spideer, go:

```
scrapy crawl bbcnews
```

###### pynews_search
pynews_search is built using Flask microframework. By default, it starts up on localhost using port 5000. The search app supports both GET and POST requests. pynews_search has read-only access to MongoDB.

To run pynews_search from the directory, go:
```
python search.py
```

Now you can fire up a browser and enter http://<host>:5000 to launch a bare bones search app.

You can also use the brilliant [python requests library](http://docs.python-requests.org/en/master/#) for python to send GET requests. 
Using the request library, you can go:
```
r = requests.get('https://localhost:5000/search?keyword=search_terms&phrase=off')
r.json()
```


## Authors

* **M Salman** - (https://github.com/m-salman/)
