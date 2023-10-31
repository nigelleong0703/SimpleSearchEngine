# AI6122_SimpleSearchEngine
To index dblp xml file from database, using PyLucence, and create simple search engine to search through the database.

To use this, you need to do the indexing first, and run the search file later to do searching.

## Quick Start
Since the search engine and the explorer is based on Pylucence, you should build Pylucence environment, which consists of Java, JCC, ANT, Pylucence.

It is actually a nightmare to build this environment from scratch, we recommend using docker image to run this project:

```
$ docker pull coady/pylucene
$ docker run -it coady/pylucene
```

Then, you can mount this directory, and build the indexes:

```
pip install -r requirements.txt
python indexing.py
```

The code will first detect whether the dblp database is downloaded or not. If the database is not downloaded before, the code will download the dataset automatically. 

After downloading, you can find "dblp.xml" and "dblp.dtd" inside your project folder. You can also find a folder named "index" inside the project folder.


## Search Docs
To run the search engine, you simply need one line of command:

```
python query.py
```

Then, follow the prompt to specify the function and key parameters, such as year range, author, conference, keyword.

It will return a list of documents, each one is a Python dict:

```
{
    'type': 'inproceedings',
    'mdate': '-1516881920',
    'key': 'conf/aaai/AmirSS15',
    'author': ['Ofra Amir','Guni Sharon','Roni Stern'],
    'title': 'Multi-Agent Pathfinding as a Combinatorial Auction.',
    'pages': '2003-2009',
    'year': '2015',
    'booktitle': 'AAAI',
    'ee': 'https://doi.org/10.1609/aaai.v29i1.9427',
    'crossref': 'conf/aaai/2015',
    'url': 'db/conf/aaai/aaai2015.html#AmirSS15'
}

```

## Visualize Trends

We offer three high-level functions to provide valuable insights into the chosen conference, you can list the apis via:

```
python main.py -h
```

For example, if you would like to explore hotspots evolution of "AAAI" in recent 10 years. You can run:

```
python main.py getHotspotsEvo --conference AAAI --start 2014
```

