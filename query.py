import os
import sys


import lucene

from java.nio.file import Paths
from org.apache.lucene.index import Term
from org.apache.lucene.search import BooleanClause, TermQuery, BooleanQuery, PhraseQuery
from org.apache.lucene.store import FSDirectory
from indexing import CustomAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.document import IntPoint
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.queryparser.flexible.standard import StandardQueryParser
from org.apache.lucene.analysis.tokenattributes import CharTermAttribute

import re


import time

import json

lucene.initVM()

class CustomQueryParser:
    def __init__(self, field, analyzer):
        self.field = field
        self.analyzer = analyzer

    def parse(self, string):
        string = string.upper()  # Convert to upper case
        tokens = re.split('( AND | OR | NOT |, )', string)  # Split the string into tokens

        # Initialize a BooleanQuery.Builder
        query_builder = BooleanQuery.Builder()

        # Initialize the occur variable with MUST as default
        occur = BooleanClause.Occur.MUST

        # Iterate over the tokens and add them to the query
        for token in tokens:
            if token.strip() == 'AND':
                occur = BooleanClause.Occur.MUST
            elif token.strip() == 'OR' or token.strip() == ',':
                occur = BooleanClause.Occur.SHOULD
            elif token.strip() == 'NOT':
                occur = BooleanClause.Occur.MUST_NOT
            else:
                stream = self.analyzer.tokenStream(self.field, token)
                term_att = stream.addAttribute(CharTermAttribute.class_)
                stream.reset()

                words = []
                while stream.incrementToken():
                    words.append(term_att.toString())

                stream.end()
                stream.close()

                if len(words) > 1:
                    # If the token contains more than one word, create a PhraseQuery
                    phrase_query = PhraseQuery.Builder()
                    for word in words:
                        phrase_query.add(Term(self.field, word))
                    query_builder.add(phrase_query.build(), occur)
                else:
                    # If the token contains only one word, create a TermQuery
                    query_builder.add(TermQuery(Term(self.field, words[0])), occur)

        return query_builder.build()


class Searher(object):
    def __init__(self, store_dir: str, topK: int):
        # Analyzer
        self.analyzer = CustomAnalyzer()
        self.topK = topK

        # Create directory instance
        store = FSDirectory.open(Paths.get(store_dir))

        # Create DirectoryReader instance
        reader = DirectoryReader.open(store)

        # Create IndexSearcher
        self.searcher = IndexSearcher(reader)
    

    def printResult(self, query, return_all:bool, save_to_local:bool, file_name:str, topK:int, printing:bool=True):
        """ Convert scoreDocs to a list of dict
            scoreDocs: result

        Returns:
            list[map]: all docs within given year range [start, end)
        """
        if return_all:
            number = self.searcher.getIndexReader().numDocs()
        else:
            number = topK

        start_time = time.time()
        scoreDocs = self.searcher.search(query, number).scoreDocs
        

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
            
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"Elapsed time: {elapsed_time:6f} seconds")
        if save_to_local:
            with open(file_name, "w", encoding="utf-8") as file:
                for item in reading_list:
                    file.write(json.dumps(item) + '\n')
            file.close()

        return reading_list


    def searchByYearRange(self, start: int, end: int, return_all=False, save_to_local=False, printing=True, top_k=None):
        """
        Args:
            start (int): start year
            end (int): end year
            return_all(bool): should return all relevant result or TopK
            save_to_local(bool): shoulld save to local file?

        Returns:
            list[map]: all docs within given year range [start, end)
        """
        if top_k == None:
            top_k = self.topK
        if end:
            query = IntPoint.newRangeQuery("year", start, end)
        else:
            query = IntPoint.newRangeQuery("year", start, start)

        return self.printResult(query, return_all, save_to_local, f"yearrange-{start},{end}.json", top_k, printing)


    def searchByConf(self, conf: str, return_all=False, save_to_local=False, printing=True, top_k=None):
        """
        Args:
            conf (int): venue name
            return_all(bool): should return all relevant result or TopK
            save_to_local(bool): shoulld save to local file?

        Returns:
            list[map]: all docs within given year range [start, end)
        """
        if top_k == None:
            top_k = self.topK

        # query_parser = QueryParser('key', self.analyzer)
        key_query = TermQuery(Term('key',conf))
        # key_query.setBoost(2.0)

        booktitle_query = QueryParser('booktitle',self.analyzer).parse(conf)
        
        journal_query = QueryParser('journal', self.analyzer).parse(conf)

        boolean_query = BooleanQuery.Builder()
        boolean_query.add(key_query, BooleanClause.Occur.SHOULD)
        boolean_query.add(booktitle_query, BooleanClause.Occur.SHOULD)
        boolean_query.add(journal_query, BooleanClause.Occur.SHOULD)

        return self.printResult(boolean_query.build(), return_all, save_to_local, f"conf-{conf}.json", top_k, printing)

    
    def searchByKeyword(self, key:str, return_all=False, save_to_local=False, printing=True, top_k=None):
        """
        Args:
            key (str): keyword, or phrase
            return_all(bool): should return all relevant result or TopK
            save_to_local(bool): shoulld save to local file?

        Returns:
            list[map]: all docs within given year range [start, end)
        """
        if top_k == None:
            top_k = self.topK
        # query_parser = QueryParser('title', self.analyzer)
        queryParser = CustomQueryParser('title',self.analyzer)
        query = queryParser.parse(key)

        self.printResult(query, return_all, save_to_local, f"keyword-{key}.json", top_k, printing)
        

    def searchByAuthor(self, author:str, return_all=False, save_to_local=False, printing=True, top_k=None):
        """
        Args:
            author (str): author name query
            return_all(bool): should return all relevant result or TopK
            save_to_local(bool): shoulld save to local file?

        Returns:
            list[map]: all docs within given year range [start, end)
        """
        if top_k == None:
            top_k = self.topK
        query_parser = QueryParser('author', self.analyzer)
        query = query_parser.parse(author)

        self.printResult(query, return_all, save_to_local, f"author-{author}.json", top_k, printing)


    def multiFieldSearch(self, start: int=None, end: int=None, conf: str=None, key :str=None, author :str=None, return_all=False, save_to_local=False, printing=True, top_k = None):
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
        if top_k == None:
            top_k = self.topK
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

        self.printResult(boolean_query.build(), return_all, save_to_local, f"multi-{start}-{end}-{conf}-{key}-{author}.json", top_k, printing)


    def multiField(self, return_all=False, save_to_local=False):
        title = input(f"Please enter your search query for title (or press Enter to skip): ")
        author = input(f"Please enter your search query for author (or press Enter to skip): ")
        conf = input(f"Please enter your search query for venue (or press Enter to skip): ")
        start = input(f"Please enter your search query for starting year (or press Enter to skip): ")
        end = input(f"Please enter your search query for ending year (or press Enter to skip): ")
        top_k = input(f"Please enter the number of results returned (Default = {self.topK}, press Enter to skip): ")
        if top_k:
            top_k = int(top_k)
        if start:
            start = int(start)
        if end:
            end = int(end)
        return self.multiFieldSearch(start=start, end=end, conf=conf, key=title, author=author, return_all=return_all, save_to_local=save_to_local, top_k=top_k)


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
            top_k = input(f"Please enter the number of results returned (Default = {searcher.topK}, press Enter to skip): ")
            if top_k:
                top_k = int(top_k)
            else:
                top_k = None
            searcher.searchByYearRange(start_year, end_year, top_k=top_k)

        elif option == "2":
            key = input("Please enter the conference name: ")
            top_k = input(f"Please enter the number of results returned (Default = {searcher.topK}, press Enter to skip): ")
            if top_k:
                top_k = int(top_k)
            else:
                top_k = None
            searcher.searchByConf(key, top_k=top_k)

        elif option == "3":
            key = input("Please enter the title name: ")
            top_k = input(f"Please enter the number of results returned (Default = {searcher.topK}, press Enter to skip): ")
            if top_k:
                top_k = int(top_k)
            else:
                top_k = None
            # search_by_title()
            searcher.searchByKeyword(key, top_k=top_k)

        elif option == "4":
            author = input("Please enter the author name: ")
            top_k = input(f"Please enter the number of results returned (Default = {searcher.topK}, press Enter to skip): ")
            if top_k:
                top_k = int(top_k)
            else:
                top_k = None
            searcher.searchByAuthor(author, top_k=top_k)

        elif option == "5":
            searcher.multiField()

        elif option == "6":
            break
        else:
            print("Invalid option. Please try again.")



    # sys.stdout.close()
    # sys.stdout = sys.__stdout__


