import os
import sys


import lucene

from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import Term
from org.apache.lucene.search import BooleanClause, TermQuery, BooleanQuery, PhraseQuery
from org.apache.pylucene.queryparser.classic import PythonQueryParser, PythonMultiFieldQueryParser
from org.apache.lucene.store import FSDirectory
from index import CustomAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import IndexSearcher, TermRangeQuery
from org.apache.lucene.document import IntPoint

import json

lucene.initVM()

class Searher(object):
    def __init__(self, store_dir: str, topK: int):
        # Analyzer
        self.analyzer = CustomAnalyzer()
        self.topK = 50

        # Create directory instance
        store = FSDirectory.open(Paths.get(storeDir))

        # Create DirectoryReader instance
        reader = DirectoryReader.open(store)

        # Create IndexSearcher
        self.searcher = IndexSearcher(reader)
    
    
    # def convertToList(self, scoreDocs):
    #     """ Convert scoreDocs to a list of dict
    #         scoreDocs: result

    #     Returns:
    #         list[map]: all docs within given year range [start, end)
    #     """
    #     reading_list = []
    #     for scoreDoc in scoreDocs:
    #         doc = self.searcher.doc(scoreDoc.doc)
    #         temp_dict = dict((field.name(), field.stringValue()) for field in doc.getFields())
    #         print(temp_dict)
    #         reading_list.append(temp_dict)
    #     return reading_list

    def printResult(self, scoreDocs, save_to_local:bool, file_name:str):
        """ Convert scoreDocs to a list of dict
            scoreDocs: result

        Returns:
            list[map]: all docs within given year range [start, end)
        """
        reading_list = []
        for index, scoreDoc in enumerate(scoreDocs):
            doc = self.searcher.doc(scoreDoc.doc)
            temp_dict = dict((field.name(), field.stringValue()) for field in doc.getFields())
            print(f'DocID: {scoreDoc.doc}')
            print(f'Score: {scoreDoc.score}')
            print(f'Rank: {index+1}')
            print(temp_dict)
            reading_list.append(temp_dict)

        if save_to_local:
            with open(file_name, "w", encoding="utf-8") as file:
                for item in reading_list:
                    file.write(json.dumps(item) + '\n')
            file.close()

        return reading_list


    def searchByYearRange(self, start: int, end: int, return_all=False, save_to_local=False):
        """
        Args:
            start (int): start year
            end (int): end year
            return_all(bool): should return all relevant result or TopK
            save_to_local(bool): shoulld save to local file?

        Returns:
            list[map]: all docs within given year range [start, end)
        """
        query = IntPoint.newRangeQuery("year", start, end)
        if return_all: 
            number = self.searcher.getIndexReader().numDocs()
        else:
            number = self.topK

        scoreDocs = self.searcher.search(query, number).scoreDocs
        # return self.convertToList(scoreDocs)
        return self.printResult(scoreDocs, save_to_local, f"yearrange-{start},{end}.json")


    def searchByConf(self, conf: str, return_all=False, save_to_local=False):
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

        booktitle_query = QueryParser('booktitle',self.analyzer).parse(conf)
        
        journal_query = QueryParser('journal', self.analyzer).parse(conf)

        boolean_query = BooleanQuery.Builder()
        boolean_query.add(key_query, BooleanClause.Occur.SHOULD)
        boolean_query.add(booktitle_query, BooleanClause.Occur.SHOULD)
        boolean_query.add(journal_query, BooleanClause.Occur.SHOULD)

        if return_all:
            number = self.searcher.getIndexReader().numDocs()
        else:
            number = self.topK

        scoreDocs = self.searcher.search(boolean_query.build(), number).scoreDocs

        # return self.convertToList(scoreDocs)
        return self.printResult(scoreDocs, save_to_local, f"conf-{conf}.json")

    
    def searchByKeyword(self, key:str, return_all=False, save_to_local=False):
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
        
        if return_all:
            number = self.searcher.getIndexReader().numDocs()
        else:
            number = self.topK

        scoreDocs = self.searcher.search(query, number).scoreDocs

        # return self.convertToList(scoreDocs)
        self.printResult(scoreDocs, save_to_local, f"keyword-{key}.json")
        

    def searchByAuthor(self, author:str, return_all=False, save_to_local=False):
        """
        Args:
            author (str): author name query
            return_all(bool): should return all relevant result or TopK
            save_to_local(bool): shoulld save to local file?

        Returns:
            list[map]: all docs within given year range [start, end)
        """
        query_parser = QueryParser('author', self.analyzer)
        query = query_parser.parse(key)
        
        if return_all:
            number = self.searcher.getIndexReader().numDocs()
        else:
            number = self.topK

        scoreDocs = self.searcher.search(query, number).scoreDocs
        # return self.convertToList(scoreDocs)
        # return self.printResult(scoreDocs, save_to_local)
        self.printResult(scoreDocs, save_to_local, f"author-{author}.json")


    def multiFieldSearch(self, start: int=None, end: int=None, conf: str=None, key :str=None, author :str=None, return_all=False, save_to_local=False):
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
        if return_all:
            number = self.searcher.getIndexReader().numDocs()
        else:
            number = self.topK

        scoreDocs = self.searcher.search(boolean_query.build(), number).scoreDocs

        self.printResult(scoreDocs, save_to_local, f"multi-{start}-{end}-{conf}-{key}-{author}.json")


    def multiField(self, return_all=False, save_to_local=False):
        # fields = ["title", "author"]
        # query_dict = {}
        # boolean_query = BooleanQuery.Builder()
        # for field in fields:
        #     query = input(f"Please enter your search query for {field} (or press Enter to skip): ")
        #     if query:
        #         query_parser = QueryParser(field, self.analyzer).parse(query)
        #         boolean_query.add(query_parser, BooleanClause.Occur.MUST)
        # conf = input(f"Please enter your search query for venue (or press Enter to skip): ")
        # if conf:
        #     key_query = TermQuery(Term('key',conf))
        #     booktitle_query = QueryParser('booktitle',self.analyzer).parse(conf)      
        #     journal_query = QueryParser('journal', self.analyzer).parse(conf)
        #     boolean_conf_query = BooleanQuery.Builder()
        #     boolean_conf_query.add(key_query, BooleanClause.Occur.SHOULD)
        #     boolean_conf_query.add(booktitle_query, BooleanClause.Occur.SHOULD)
        #     boolean_conf_query.add(journal_query, BooleanClause.Occur.SHOULD)
        #     boolean_query.add(boolean_conf_query.build(), BooleanClause.Occur.MUST)
        # starting_query = input(f"Please enter your search query for starting year (or press Enter to skip): ")
        # if starting_query:
        #     ending_query = input(f"Please enter your search query for ending year (or press Enter to skip): ")
        #     if ending_query:
        #         year_query = IntPoint.newRangeQuery("year", int(starting_query), int(ending_query))
        #     else:
        #         year_query = IntPoint.newRangeQuery("year", int(starting_query), int(starting_query))
        #     boolean_query.add(year_query, BooleanClause.Occur.MUST)
        # if return_all:
        #     number = self.searcher.getIndexReader().numDocs()
        # else:
        #     number = self.topK

        # scoreDocs = self.searcher.search(boolean_query.build(), number).scoreDocs

        # # return self.convertToList(scoreDocs)
        # return self.printResult(scoreDocs, save_to_local)
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
    # searcher.searchByYearRange(2020,2020,return_all=True)
    # searcher.searchByConf("AAAI")


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
            start_year = int(input("Please enter the start year: "))
            end_year = int(input("Please enter the end year: "))
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
            searcher.search_by_author(author)

        elif option == "5":
            ###########
            # Multifield Search
            searcher.multiField()



        elif option == "6":
            break
        else:
            print("Invalid option. Please try again.")



    # sys.stdout.close()
    # sys.stdout = sys.__stdout__


