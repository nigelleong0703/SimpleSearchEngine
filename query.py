import os
import sys


import lucene

from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import Term
from org.apache.lucene.search import BooleanClause, TermQuery, BooleanQuery, PhraseQuery
from org.apache.pylucene.queryparser.classic import PythonQueryParser, PythonMultiFieldQueryParser
from org.apache.lucene.store import FSDirectory
from indexing import CustomAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import IndexSearcher, TermRangeQuery
from org.apache.lucene.document import IntPoint

import time

import json

lucene.initVM()

class Searher(object):
    def __init__(self, store_dir: str, topK: int):
        # Analyzer
        self.analyzer = CustomAnalyzer()
        self.topK = topK

        # Create directory instance
        store = FSDirectory.open(Paths.get(storeDir))

        # Create DirectoryReader instance
        reader = DirectoryReader.open(store)

        # Create IndexSearcher
        self.searcher = IndexSearcher(reader)
    

    def printResult(self, query, return_all:bool, save_to_local:bool, file_name:str, printing:bool=True):
        """ Convert scoreDocs to a list of dict
            scoreDocs: result

        Returns:
            list[map]: all docs within given year range [start, end)
        """
        if return_all:
            number = self.searcher.getIndexReader().numDocs()
        else:
            number = self.topK

        start_time = time.time()
        scoreDocs = self.searcher.search(query, number).scoreDocs
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Elapsed time: {elapsed_time:6f} seconds")

        reading_list = []
        for index, scoreDoc in enumerate(scoreDocs):
            doc = self.searcher.doc(scoreDoc.doc)
            temp_dict = {}
            for field in doc.getFields():
                if field.name() == "author":    
                    if temp_dict.get(field.name()) == None:
                        temp_dict[field.name()] = list()
                    temp_dict[field.name()] = temp_dict.get(field.name()) + [field.stringValue()]
                else:
                    temp_dict[field.name()] = field.stringValue()
            if printing:
                print(f'DocID: {scoreDoc.doc}')
                print(f'Score: {scoreDoc.score}')
                print(f'Rank: {index+1}')
                
                for key, value in temp_dict.items():
                    if key == "key" or key == "mdate":
                        continue
                    elif key == "author":
                        print(f"{key}: {(', '.join(value))}")
                    else:
                        print(f"{key}: {value}")
                print()
            reading_list.append(temp_dict)

        if save_to_local:
            with open(file_name, "w", encoding="utf-8") as file:
                for item in reading_list:
                    file.write(json.dumps(item) + '\n')
            file.close()

        return reading_list


    def searchByYearRange(self, start: int, end: int, return_all=False, save_to_local=False, printing=True):
        """
        Args:
            start (int): start year
            end (int): end year
            return_all(bool): should return all relevant result or TopK
            save_to_local(bool): shoulld save to local file?

        Returns:
            list[map]: all docs within given year range [start, end)
        """
        if end:
            query = IntPoint.newRangeQuery("year", start, end)
        else:
            query = IntPoint.newRangeQuery("year", start, start)

        return self.printResult(query, return_all, save_to_local, f"yearrange-{start},{end}.json", printing)


    def searchByConf(self, conf: str, return_all=False, save_to_local=False, printing=True):
        """
        Args:
            conf (int): venue name
            return_all(bool): should return all relevant result or TopK
            save_to_local(bool): shoulld save to local file?

        Returns:
            list[map]: all docs within given year range [start, end)
        """
        # query_parser = QueryParser('key', self.analyzer)
        key_query = TermQuery(Term('key',conf))
        key_query.setBoost(2.0)

        booktitle_query = QueryParser('booktitle',self.analyzer).parse(conf)
        
        journal_query = QueryParser('journal', self.analyzer).parse(conf)

        boolean_query = BooleanQuery.Builder()
        boolean_query.add(key_query, BooleanClause.Occur.SHOULD)
        boolean_query.add(booktitle_query, BooleanClause.Occur.SHOULD)
        boolean_query.add(journal_query, BooleanClause.Occur.SHOULD)

        return self.printResult(boolean_query.build(), return_all, save_to_local, f"conf-{conf}.json", printing)

    
    def searchByKeyword(self, key:str, return_all=False, save_to_local=False, printing=True):
        """
        Args:
            key (str): keyword, or phrase
            return_all(bool): should return all relevant result or TopK
            save_to_local(bool): shoulld save to local file?

        Returns:
            list[map]: all docs within given year range [start, end)
        """
        query_parser = QueryParser('title', self.analyzer)
        query = query_parser.parse(key)

        self.printResult(query, return_all, save_to_local, f"keyword-{key}.json", printing)
        

    def searchByAuthor(self, author:str, return_all=False, save_to_local=False, printing=True):
        """
        Args:
            author (str): author name query
            return_all(bool): should return all relevant result or TopK
            save_to_local(bool): shoulld save to local file?

        Returns:
            list[map]: all docs within given year range [start, end)
        """
        query_parser = QueryParser('author', self.analyzer)
        query = query_parser.parse(author)

        self.printResult(query, return_all, save_to_local, f"author-{author}.json", printing)


    def multiFieldSearch(self, start: int=None, end: int=None, conf: str=None, key :str=None, author :str=None, return_all=False, save_to_local=False, printing=True):
        """
        Args:
            start (int): start year
            end (int): end year
            conf (str): conf/journal venue
            key (str): keyword search
            author (str): author name search 
            return_all(bool): should return all relevant result or TopK

        Returns:
            list[map]: all docs within given condition
        """
        boolean_query = BooleanQuery.Builder()
        if key:
            query_parser = QueryParser("title", self.analyzer).parse(key)
            boolean_query.add(query_parser, BooleanClause.Occur.MUST)
        if author:
            query_parser = QueryParser("author", self.analyzer).parse(author)
            boolean_query.add(query_parser, BooleanClause.Occur.MUST)        
        if conf:
            key_query = TermQuery(Term('key',conf))
            booktitle_query = QueryParser('booktitle',self.analyzer).parse(conf)      
            journal_query = QueryParser('journal', self.analyzer).parse(conf)
            boolean_conf_query = BooleanQuery.Builder()
            boolean_conf_query.add(key_query, BooleanClause.Occur.SHOULD)
            boolean_conf_query.add(booktitle_query, BooleanClause.Occur.SHOULD)
            boolean_conf_query.add(journal_query, BooleanClause.Occur.SHOULD)
            boolean_query.add(boolean_conf_query.build(), BooleanClause.Occur.MUST)
        if start:
            if end:
                year_query = IntPoint.newRangeQuery("year", start, end)
            else:
                year_query = IntPoint.newRangeQuery("year", start, start)
            boolean_query.add(year_query, BooleanClause.Occur.MUST)

        self.printResult(boolean_query.build(), return_all, save_to_local, f"multi-{start}-{end}-{conf}-{key}-{author}.json", printing)


    def multiField(self, return_all=False, save_to_local=False):
        title = input(f"Please enter your search query for title (or press Enter to skip): ")
        author = input(f"Please enter your search query for author (or press Enter to skip): ")
        conf = input(f"Please enter your search query for venue (or press Enter to skip): ")
        start = input(f"Please enter your search query for starting year (or press Enter to skip): ")
        end = input(f"Please enter your search query for ending year (or press Enter to skip): ")
        if start:
            start = int(start)
        if end:
            end = int(end)
        return self.multiFieldSearch(start=start, end=end, conf=conf, key=title, author=author)


### need to do free text keyword queries, including single keyword query and phrase query, on 
### 1. title, publication venue
### Top N number is configurable

### Result should be returned in rank, scores, docID and snippets

### Support search for publications meeting multiple requirements:
# containing a keyword “search”, published in SIGIR conference, in the year of 2020.
### randomly choose a few queries (including both single keyword query and phrase queries), discuss whether results returned by search engine are as expected.
### record the time to process the query

if __name__ == "__main__":
    # log_file_name = "log_year_2020.txt"
    # sys.stdout = open(log_file_name, "w")
    storeDir = "./index/"
    topK = 20

    searcher = Searher(store_dir = storeDir, topK = topK)
    # searcher.multiFieldSearch(start=2021, conf='IEEE', return_all=True, save_to_local=True)

    while True:
        print()
        print("Please choose an option:")
        print("1. Search for all documents within year range")
        print("2. Search for all documents within specific conferences")
        print("3. Search for title")
        print("4. Search for author")
        print("5. Multifield Search")
        print("6. Exit")

        option = input()

        if option == "1":
            start_year = input("Please enter the start year: ")
            while not start_year:
                start_year = input("Please enter the start year: ")
            end_year = input("Please enter the end year (or press Enter to skip) : ")
            if start_year:
                start_year = int(start_year)
            else:
                start_year = None
            if end_year:
                end_year = int(end_year)
            else:
                end_year = None
            searcher.searchByYearRange(start_year, end_year)

        elif option == "2":
            key = input("Please enter the conference name: ")
            searcher.searchByConf(key)

        elif option == "3":
            key = input("Please enter the title name: ")
            # search_by_title()
            searcher.searchByKeyword(key)

        elif option == "4":
            author = input("Please enter the author name: ")
            searcher.searchByAuthor(author)

        elif option == "5":
            searcher.multiField()

        elif option == "6":
            break
        else:
            print("Invalid option. Please try again.")



    # sys.stdout.close()
    # sys.stdout = sys.__stdout__


