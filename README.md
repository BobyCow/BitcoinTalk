# **BitcoinTalk Scraper**

## **Requirements:**

### Install requirements

| LIB | DOC | IMPORT |
|-----|-----|--------|
| bs4 | [BeautifulSoup][bs4] | `from bs4 import BeautifulSoup as bs` |
| cursor | [Cursor][cur] | `import cursor` |
| spacy | [Spacy][spc] | `import spacy` |
| mplcursors | [Mplcursors][mplc] | `import mplcursors` |

```sh
python -m pip install -r requirements.txt
```

## **Features:**

### _DownloadHTML-v2_
>Check if pages of the [BitcoinTalk][btcf] forum are missing and download them if necessary:  
>RUN: `python DownloadHTML-v2.py`

>Download all pages of the [BitcoinTalk][btcf] forum:  
>RUN: `python DownloadHTML-v2.py [ -u | --update ]`

### _Scraper_
>Iterate over downloaded files and retrieve all informations:  
>RUN: `python Scraper.py`

### _TextAnalysis_
>Iterate over all topics, create B-O-W (_bags-of-words_) and compute TF-IDF (_term frequency-inverse document frequency_) on each word (excluding stop-words & punctuation).  
>Before running this program, please make sure you already ran **DownloadHTML-v2.py** and **Scraper.py** in order to create a _BitcoinTalk-data.json_ file:  
>RUN: `python TextAnalysis.py`  

Documentation about [TF-IDF][tfidf]

[bs4]: <https://www.crummy.com/software/BeautifulSoup/bs4/doc/>
[cur]: <https://github.com/GijsTimmers/cursor>
[spc]: <https://spacy.io/>
[mplc]: <https://mplcursors.readthedocs.io/en/stable/index.html>
[btcf]: <https://bitcointalk.org/index.php?board=14.0>
[tfidf]: <https://en.wikipedia.org/wiki/Tf%E2%80%93idf>