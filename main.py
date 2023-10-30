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


storeDir = "./index/"
topK = 20
searcher = Searher(store_dir = storeDir, topK = topK)

def getConfHostspots(conf: str, start: int, end=2023):
    confRes = searcher.searchByConf(conf, return_all=True, printing=False)
    timeRes = searcher.searchByYearRange(start, end, return_all=True)
    res = list(set(confRes) & set(timeRes))
    return res


if __name__ == "__main__":
    res = getConfHostspots("AAAI", 2022)
    print(len(res))