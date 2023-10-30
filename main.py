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
import matplotlib.pyplot as plt


storeDir = "./index/"
topK = 20
searcher = Searher(store_dir = storeDir, topK = topK)
    
stop_words = ['abstract', 'approach', 'commitee', 'report', 'study', 'paper']


def describe(data: dict, title=None, xlabel=None, ylabel=None):
    years = list(data.keys())
    plt.figure(figsize=(10, 8), dpi=100)
    plt.xticks(years, years)
    counts = {}
    for year in years:
        for item in data[year]:
            if item[0] in counts:
                counts[item[0]].append(item[1])
            else:
                counts[item[0]] = [item[1]]
    
    for key, cnts in counts.items():
        plt.plot(years, cnts, label=key)
    
    plt.legend()
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.savefig(title)
    plt.show()


def getPivotAuthors():
    pass
    

def getConfHotspotsEvo(conf: str, start: int, end=2023, tok_k=5):
    confRes = searcher.searchByConf(conf, return_all=True, printing=False)
    keywords_glob = _getConfHotspots(confRes, start, end)[:tok_k]
    res = {}
    print('*'*10, 'Yearly Conference Hostspots Summary', '*'*10)
    print('Research hotspots since', start, 'to', end, 'are', keywords_glob)
    for i in range(start, end + 1):
        keywords = _getConfHotspots(confRes, i, i)
        res[i] = _intersect(keywords, keywords_glob)
        print(str(i) + ':', res[i])
    return res


def _intersect(src: list, filter: list):
    key = [item[0] for item in filter]
    return [i for i in src if i[0] in key]


def getConfHotspots(conf: str,  start: int, end=2023, top_k=5):
    confRes = searcher.searchByConf(conf, return_all=True, printing=False)
    keywordsMap = {}
    print('*'*10, 'Keywords Summary', '*'*10)
    for i in range(start, end + 1):
        keywords = _getConfHotspots(confRes, i, i)
        keywordsMap[i] = keywords[:top_k]
        print(i, ":", keywordsMap[i])
    return keywordsMap
     

def _getConfHotspots(confRes: list, start: int, end=2023):
    timeRes = searcher.searchByYearRange(start, end, return_all=True, printing=False)
    
    confUrl = {doc['url'] for doc in confRes if 'url' in doc}
    timeUrl = {doc['url'] for doc in timeRes if 'url' in doc}
    # Find the intersection of Urls
    intersected_urls = timeUrl.intersection(confUrl)
    
    res = [doc for doc in confRes if doc['url'] in intersected_urls]
    
    titles = [doc['title'] for doc in res]
    
    # print('*'*5, 'Index Done, Start Keyword Extraction', '*'*5)
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
    # keywords = getConfHotspots("AAAI", 2020)
    data = {2020: [('reinforcement learning', 13), ('supervised learning', 13), ('task learning', 11), ('machine learning', 8), ('shot learning', 8)],
            2021: [('supervised learning', 15), ('shot learning', 15), ('reinforcement learning', 14), ('task learning', 11), ('machine learning', 9)],
            2022: [('supervised learning', 15), ('reinforcement learning', 14), ('shot learning', 10), ('machine learning', 8), ('task learning', 6)],
            2023: [('supervised learning', 14), ('reinforcement learning', 10), ('machine learning', 8), ('task learning', 8), ('shot learning', 7)]}
    # res = getConfHotspotsEvo("AAAI", 2020)
    describe(data, title="Hotspots Evolution in AAAI", xlabel="Year", ylabel="Count")    
    

    
    
    