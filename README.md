# AI6122_SimpleSearchEngine
To index dblp xml file from database, using PyLucence, and create simple search engine to search through the database.

To use this, you need to do the indexing first, and run the search file later to do searching.

## Indexing database
The code will first detect whether the dblp database is downloaded or not. 

If the database is not downloaded before, the code will download the dataset automatically. 

After downloading, you should find "dblp.xml" and "dblp.dtd" inside your project folder.

To run the code:

```
python indexing.py
```
After indexing, you will find a folder named "index" inside the project folder.


## Search
YOU SHOULD RUN THE INDEXING FIRST


To run the code:

```
python query.py
```

### Using the searcher

You need to create the instance, mentioning the index directory and topK numbers before doing searching
```
    storeDir = "./index/"
    topK = 20
    searcher = Searher(store_dir = storeDir, topK = topK)
```
Provided function including 
```
    def printResult(self, scoreDocs, save_to_local:bool, file_name:str)
```
```
    def searchByYearRange(self, start: int, end: int, return_all=False, save_to_local=False)
```
```
    def searchByConf(self, conf: str, return_all=False, save_to_local=False)
```
```
    def searchByKeyword(self, key:str, return_all=False, save_to_local=False)
```
```
    def searchByAuthor(self, author:str, return_all=False, save_to_local=False)
```
```
    def multiFieldSearch(self, start: int=None, end: int=None, conf: str=None, key :str=None, author :str=None, return_all=False, save_to_local=False)
```
- return_all = True: means return all matching result
- return_all = False: means return topK matching result

- save_to_local: if the results need to be outputed to one json file:
- inside the output file: it is a list of dict, one line is one dict, like this structure:
```
{type:article, ..... , ......}
{type:article, ..... , ......}
```
to read back the file, you need to read the file LINE BY LINE and convert back to dict
