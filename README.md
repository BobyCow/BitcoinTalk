# **BitcoinTalk Scraper**

## **Requirements:**

### Install requirements

| LIB | DOC | IMPORT |
|-----|-----|--------|
| bs4 | [BeautifulSoup][bs4] | `from bs4 import BeautifulSoup as bs` |
| cursor | [Cursor][cur] | `import cursor` |
| spacy | [Spacy][spc] | `import spacy` |
| matplotlib | [Matplotlib][mtplt] | `import matplotlib.pyplot as plt` |
| mplcursors | [Mplcursors][mplc] | `import mplcursors` |

```sh
python -m pip install -r requirements.txt
```

## **Features:**

****
### _DownloadHTML-v2_
>Check if pages of the [BitcoinTalk][btcf] forum are missing and download them if necessary:  
>RUN: `python DownloadHTML-v2.py`

>Download all pages of the [BitcoinTalk][btcf] forum:  
>RUN: `python DownloadHTML-v2.py [ -u | --update ]`  

**It will create a directory containing all html pages of the [forum][btcf], with the following architecture:**  
```
├── BitcoinTalk-Forum
│   ├── Hardware (childboard name)
│   │   ├── 0a6b038fb2ee35ae4941dd86fcad7c1858cef8df (hashed topic title using sha1 encoding)
│   │   │   ├── 1.html (html page of the topic)
│   │   │   ├── 2.html
│   │   │   └── 3.html
│   │   ├── 7dc40b9c0c457b9986b4a710705b67d0b035f9e8
│   │   │   └── 1.html
│   │   ├── 85ea1f75700b12789b153d1ea1e952738b84efb1
│   │   │   ├── 1.html
│   │   │   ├── 2.html
│   │   │   ├── 3.html
│   │   │   ├── 4.html
│   │   │   ├── 5.html
│   │   │   ├── [...]
│   │   ├── 93fc59b432ec70f3b7d72bedac883df6ce1af86a
│   │   ├── [...]
│   ├── Mining Software (miners) [...]
│   ├── Mining speculation [...]
│   ├── Mining support [...]
│   └── Pools [...]
```

****
### _Scraper_
>Iterate over downloaded files and retrieve all informations:  
>RUN: `python Scraper.py`  

**The scraper will create a file named `BitcoinTalk-data.json`.  
It is a large file containing all informations about all scraped topics.**

****
### _TextAnalysis_
>Iterate over all topics, create B-O-W (_bags-of-words_) and compute TF-IDF (_term frequency-inverse document frequency_) on each word (excluding stop-words & punctuation).  

>Before running this program, please make sure you already ran **DownloadHTML-v2.py** and **Scraper.py** in order to create a `BitcoinTalk-data.json` file:  
>RUN: `python TextAnalysis.py`

**It will analyse data inside `BitcoinTalk-data.json`, and will create a `analysis_results.json` file containing (as its name says) the results of the analysis:
For each word, of each post, of each topic:**
- **number of occurrences**
- **term frequency**
- **inverse document frequency**
- **term frequency * inverse document frequency (tf-idf)**
- **metadata relative to the topic**
    - **total number of words**
    - **number of documents (posts)**  

**If you need words to be ignored while analyzing all topics, you can add them inside `./WORDS/ignore.json`:**  
```json
{
    "ignore": [
        "pool",
        "pools",
        "hi",
        "ve",
        "hey",
        "test"
    ]
}
```

****
Documentation about [TF-IDF][tfidf]  
*Thomas Péan*

[bs4]: <https://www.crummy.com/software/BeautifulSoup/bs4/doc/>
[cur]: <https://github.com/GijsTimmers/cursor>
[spc]: <https://spacy.io/>
[mplc]: <https://mplcursors.readthedocs.io/en/stable/index.html>
[mtplt]: <https://matplotlib.org/>
[btcf]: <https://bitcointalk.org/index.php?board=14.0>
[tfidf]: <https://en.wikipedia.org/wiki/Tf%E2%80%93idf>
