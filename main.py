""" Trend Explorer 

Dependency
----------
The implementation of explorer would require following document properties:
    * conference
    * year
    * authors
    * keyword (may acquire from title & abstract?)
    
Trends
------
* Conference Hotspot (yearly): 5 keywords to describe each year <-- keyword, conference, year
* Outstanding Authors (yearly): each keyword a list of outstanding authors, ranked by #papers <-- author
* Hotspot Evolution (yearly): the change of research focus for specific keyword

Usage
-----
>>> getConfHotspots("AAAI", 2010)
<return a list of hotspots of "AAAI" since 2010>

>>> getPivotAuthors("AAAI", "Computer Vision", 2010)
<retrun a list of authors ranked by #papers related to "Computer Vision" published in "AAAI" since 2010>

>>> getHotspotsEvo("AAAI", "Computer Vision", 2010)
<return a list of #papers related to "Computer Vision" published in "AAAI" since 2010>
"""

import lucene
from query import *
from rake_nltk import Rake
# import matplotlib.pyplot as plt


storeDir = "./index/"
topK = 20
searcher = Searher(store_dir = storeDir, topK = topK)
    
stop_words = ['abstract', 'approach', 'commitee', 'report', 'study']

def getConfHostspots(conf: str, start: int, end=2023):
    confRes = searcher.searchByConf(conf, return_all=True, printing=False)
    timeRes = searcher.searchByYearRange(start, end, return_all=True, printing=False)
    
    confUrl = {doc['url'] for doc in confRes if 'url' in doc}
    timeUrl = {doc['url'] for doc in timeRes if 'url' in doc}
    # Find the intersection of Urls
    intersected_urls = timeUrl.intersection(confUrl)
    
    res = [doc for doc in confRes if doc['url'] in intersected_urls]
    
    titles = [doc['title'] for doc in res]
    
    print('*'*5 + ' Index Done, Start Keyword Extraction' + '*'*5)
    rake = Rake(min_length=2, max_length=4)
    rake.extract_keywords_from_sentences(titles)
    keywords = rake.get_ranked_phrases()
    
    cnt = {}
    for word in keywords:
        if any(ele in word for ele in stop_words):
            continue
        if word in cnt:
            cnt[word] += 1
        else:
            cnt[word] = 1
            
    cnt = sorted(cnt.items(), key=lambda item: item[1], reverse=True)
    
    return cnt


if __name__ == "__main__":
    keywords = getConfHostspots("AAAI", 2022)
    print(keywords[:10])
    
    
    

    
    
    