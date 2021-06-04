# **BitcoinTalk Scraper**

## **Requirements:**

### Install requirements

| LIB | DOC | IMPORT |
|-----|-----|--------|
| bs4 | [BeautifulSoup][bs4] | `from bs4 import BeautifulSoup as bs` |
| cursor | [Cursor][cur] | `import cursor` |
| spacy | [Spacy][spc] | `import spacy` |

```sh
python -m pip install -r requirements.txt
```

## **Features:**

### _DownloadHTML-v2_
>Check if pages of the [BitcoinTalk][btcf] forum are missing and download them if necessary:
>`python DownloadHTML-v2.py`

>Download all pages of the [BitcoinTalk][btcf] forum:
>`python DownloadHTML-v2.py [ -u | --update ]`

### _Scraper_
>Iterate over downloaded files and retrieve all informations:
>`python Scraper.py`

### _TextAnalysis_
>Iterate over all topics, create B-O-W (_bags-of-words_) and computes TF-IDF (_term frequency-inverse document frequency_) on each word (excluding stop-words & punctuation):
>`python Scraper.py`

[bs4]: <https://www.crummy.com/software/BeautifulSoup/bs4/doc/>
[cur]: <https://github.com/GijsTimmers/cursor>
[spc]: <https://spacy.io/>
[btcf]: <https://bitcointalk.org/index.php?board=14.0>