import os
import sys

import lucene
from tqdm import tqdm
import time
from datetime import datetime

from utils import dblp
from lxml import etree
from org.apache.lucene.analysis.standard import StandardAnalyzer, StandardTokenizer
from org.apache.lucene.analysis import LowerCaseFilter, StopFilter
from org.apache.lucene.analysis.en import PorterStemFilter, EnglishAnalyzer
from org.apache.lucene.document import Document, Field, StringField, FieldType, TextField, IntPoint, SortedNumericDocValuesField, LongPoint, StoredField, NumericDocValuesField
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, IndexOptions
from org.apache.lucene.store import FSDirectory
from org.apache.lucene.analysis.miscellaneous import PerFieldAnalyzerWrapper
from java.io import File

# https://dblp.org/faq/16154937.html
features = {
        "address": "str",
        "author": "list",
        "booktitle": "str",
        "cdrom": "str",
        "chapter": "str",
        "cite": "list",
        "crossref": "str",
        "editor": "list",
        "ee": "list",
        "isbn": "str",
        "journal": "str",
        "month": "str",
        "note": "str",
        "number": "str",
        "pages": "str",
        "publisher": "str",
        "publnr": "str",
        "school": "str",
        "series": "str",
        "title": "str",
        "url": "str",
        "volume": "str",
        "year": "str",
    }

element_head = {
            "article",
            "inproceedings",
            "proceedings",
            "book",
            "incollection",
            "phdthesis",
            "mastersthesis",
            "www",
            "person",
            "data",
        }

store_field = {
    "publnr",
    "url",
    "ee",
    "cdrom"
}

string_field = {
    "type",
    "isbn",
    'volume',
}

# create a analyzer class, use to turn string -> token
class CustomAnalyzer(StandardAnalyzer):
    def __init__(self):
        StandardAnalyzer.__init__(self)

    def createComponents(self, fieldName):
        source = StandardTokenizer()
        filter = LowerCaseFilter(source)
        filter = PorterStemFilter(filter)
        filter = StopFilter(True, filter, EnglishAnalyzer.ENGLISH_STOP_WORDS_SET)

        analyzer_per_field = HashMap()
        source2 = StandardTokenizer
        key_filter = LowerCaseFilter(source)
        analyzer_per_field.put("key", key_filter)
        wrapper = PerFieldAnalyzerWrapper(self.TokenStreamComponents(source, filter), analyzer_per_field)

        # analyzer_per_field = HashMap()
        # analyzer_per_field.put("author",_____)
        wrapper = PerFieldAnalyzerWrapper(self.TokenStreamComponents(source, filter), analyzer_per_field)
        # return wrapper

        # return self.TokenStreamComponents(source, filter)


class Indexer(object):
    
    def __init__(self, root, storeDir):
        """Initialize the class, and run indexDocs after initializing
        
        Args:
            root: Directory of the project
            storeDir: Directory of the index store

        Return: None

        """
        # read database
        jsondir = os.path.join(root,"dblp.json")
        # self.database = self.ReadJson(jsondir)
        

        if not os.path.exists(storeDir):
            os.mkdir(storeDir)

        lucene.initVM()
        # Analyzer object - analyses based on basic grammar, remove stop words
        analyzer = CustomAnalyzer()

        # Index Writer Configuration object
        config = IndexWriterConfig(analyzer)
        config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)

        # create index store
        store = FSDirectory.open(File(storeDir).toPath())

        # create an inder writer
        self.writer = IndexWriter(store,config)

    def ending(self):
        self.writer.commit()
        self.writer.close()
        print('done')

    def IndexSingle(self, element):
        doc = Document()
        doc.add(Field("type", element.tag, StringField.TYPE_STORED))

        # doc.add(Field("mdate", element.attrib["mdate"],TextField.TYPE_STORED))
        doc.add(LongPoint('mdate', int(datetime.strptime(element.attrib["mdate"], '%Y-%m-%d').timestamp() * 1000)))
        doc.add(NumericDocValuesField('mdate', int(datetime.strptime(element.attrib["mdate"], '%Y-%m-%d').timestamp() * 1000)))
        doc.add(StoredField("mdate",  int(datetime.strptime(element.attrib["mdate"], '%Y-%m-%d').timestamp() * 1000)))

        # doc.add(Field("mdate", int(datetime.strptime(element.attrib["mdate"], '%Y-%m-%d').timestamp() * 1000), LongPoint.TYPE_STORED))
        doc.add(Field("key", element.attrib["key"], TextField.TYPE_STORED))
        # print(element.attrib["key"])
        if (element.get('publtype') is not None):
            doc.add(Field("publtype", element.attrib["publtype"], TextField.TYPE_STORED))
        item_cleared= False
        for sub_element in list(element):
            tag = sub_element.tag
            text = sub_element.text
            if (text== None):
                text = ''.join(t if t is not None else '' for t in sub_element.itertext()).strip()
            if tag not in features:
                continue
            if text is not None and len(text) > 0:
                if tag == "year":
                    doc.add(IntPoint(tag, int(text)))
                    doc.add(SortedNumericDocValuesField(tag, int(text)))
                    doc.add(StoredField(tag,int(text)))
                    # doc.add(Field(tag, int(text), SortedNumericDocValuesField.TYPE_STORED))
                elif tag in string_field:
                    doc.add(Field(tag, text, StringField.TYPE_STORED))
                elif tag in store_field:
                    doc.add(StoredField(tag, text))
                    # doc.add(Field(tag, text, StoredField.TYPE_STORED))
                elif tag == "title":
                    doc.add(Field(tag, text, TextField.TYPE_STORED))
                else:
                    doc.add(Field(tag, text, TextField.TYPE_STORED))
        self.writer.addDocument(doc)


    def indexing(self, dblp_path: str, save_path):
        if not os.path.exists(os.path.join(os.path.dirname(dblp_path), "dblp.dtd")):
            print("Warning! dblp.dtd not found")
        if not os.path.exists(dblp_path):
            print("Warning! dblp.xml not found")

        try:
            
            context = etree.iterparse(
                dblp_path,
                dtd_validation=False,
                load_dtd=True,
                no_network=False,
                encoding="ISO-8859-1",
                events = ("start","end"),
                # events = ("end",),
            )
            number = 0

            context = iter(context)
            event, root = next(context)
            # print(root.getprevious())

            start_time = time.time()
            # total_iterations = 6907631
            total_iterations = 10256078
            
            time_updated = False
            with tqdm(total=total_iterations) as pbar:
                for event, element in context:
                    if element.tag in element_head and event == "end":
                        temp_element = element
                        self.IndexSingle(temp_element)
                        number = number + 1
                        pbar.update(1)
                        if number > 1025607 and not time_updated:
                            end_time = time.time()
                            time_updated = True
                            elapsed_time = end_time - start_time
                            print(f"Elapsed time: {elapsed_time:.2f} seconds")
                        element.clear()
                        # if element.getprevious() is not None:
                        #     element.clear()3

            # Calculate the elapsed time
            elapsed_time = end_time - start_time

            print(f"Elapsed time: {elapsed_time:.2f} seconds")

        except IOError:
            print(
                'ERROR: Failed to load file "{}". Please check your XML and DTD files.'.format(
                    dblp_path
                )
            )
            sys.exit()


if __name__ == "__main__":
    
    indexer = Indexer(root="./", storeDir="./index/")
    dblp.download_dataset()
    indexer.indexing("dblp.xml", "dblp.json")
    indexer.ending()

