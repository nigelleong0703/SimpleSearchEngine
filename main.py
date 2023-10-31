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
from thefuzz import fuzz


storeDir = "./index/"
topK = 20
searcher = Searher(store_dir = storeDir, topK = topK)

FUZZY_THRESH = 80
    
stop_words = ['abstract', 'approach', 'commitee', 'report', 'study', 'paper']


def describe(data: dict, title=None, xlabel=None, ylabel=None):
    plt.rcParams.update({'axes.labelsize': 'large'})
    years = list(data.keys())
    plt.figure(figsize=(10, 8), dpi=100)
    plt.xticks(years, years)
    counts = {}
    for year in years:
        keywords = [item[0] for item in data[years[-1]]]
        for item in data[year]:
            if item[0] in counts:
                counts[item[0]].append(item[1])
            else:
                counts[item[0]] = [item[1]]
            keywords.remove(item[0])
        if len(keywords):
            for key in keywords:
                if key in counts:
                    counts[key].append(0)
                else:
                    counts[key] = [0]
        
    
    for key, cnts in counts.items():
        plt.plot(years, cnts, label=key)
    
    fontsize = 14
    plt.xticks(fontsize=fontsize)
    plt.yticks(fontsize=fontsize)
    plt.legend(fontsize=str(fontsize))
    plt.xlabel(xlabel, fontsize=fontsize)
    plt.ylabel(ylabel, fontsize=fontsize)
    plt.savefig(title)
    plt.show()


def getPivotAuthors(keyword: str, start: int, end=2023, conf=None):
    # 1. Get keyword of this doc
    docs = searcher.multiFieldSearch(start, end, conf, printing=False, top_k=1000000)
    rake = Rake(min_length=2, max_length=4)
    authors = {}
    for doc in docs:
        rake.extract_keywords_from_text(doc['title'])
        keywords = rake.get_ranked_phrases()
        for k in keywords:
            if fuzz.token_set_ratio(k, keyword) < FUZZY_THRESH:
                continue
            # 2. If match given keyword, fields['author']++
            if 'author' not in doc:
                continue
            for author in doc['author']:
                if author in authors:
                    authors[author] += 1
                else:
                    authors[author] = 1
            continue
    return sorted(authors.items(), key=lambda x: x[1], reverse=True)
    

def getConfHotspotsEvo(conf: str, start: int, end=2023, top_k=5):
    keywords_glob = _getConfHotspots(conf, start, end)[:top_k]
    res = {}
    print('*'*10, 'Yearly Conference Hostspots Summary', '*'*10)
    print('Research hotspots since', start, 'to', end, 'are', keywords_glob)
    for i in range(start, end + 1):
        keywords = _getConfHotspots(conf, i, i)
        res[i] = _intersect(keywords, keywords_glob)
        print(str(i) + ':', res[i])
    return res


def _intersect(src: list, filter: list):
    key = [item[0] for item in filter]
    return [i for i in src if i[0] in key]


def getConfHotspots(conf: str,  start: int, end=2023, top_k=5):
    keywordsMap = {}
    print('*'*10, 'Keywords Summary', '*'*10)
    for i in range(start, end + 1):
        keywords = _getConfHotspots(conf, i, i)
        keywordsMap[i] = keywords[:top_k]
        print(i, ":", keywordsMap[i])
    return keywordsMap
     

def _getConfHotspots(conf: str, start: int, end=2023):
    res = searcher.multiFieldSearch(start, end, conf, return_all=True, printing=False)
    
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
    import argparse
    
    parser = argparse.ArgumentParser(description="visdoc: Research Trend Explorer App")
    
    # Define hints for the functions
    parser.add_argument("function", choices=["getConfHotspots", "getPivotAuthors", "getHotspotsEvo"], help="Select a function (e.g., 'getConfHotspots')")
    
    # Define hints for the arguments
    parser.add_argument("--conference", help="Specify the conference name (e.g., 'AAAI')")
    parser.add_argument("--start", type=int, help="Specify the start year (e.g., 2018)")
    parser.add_argument("--end", type=int, help="Specify the end year (e.g., 2023)")
    parser.add_argument("--research_field", help="Specify the research field (e.g., 'LLM')")
    
    args = parser.parse_args()
    
    if not args.end:
        args.end = 2023

    if args.function == "getConfHotspots":
        getConfHotspots(args.conference, args.start)
    elif args.function == "getPivotAuthors":
        getPivotAuthors(args.research_field, args.start, args.end. args.conference)
    elif args.function == "getHotspotsEvo":
        getHotspotsEvo(args.conference, args.start, args.end)


    

    
    
    