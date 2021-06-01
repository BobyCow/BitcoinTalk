from bs4 import BeautifulSoup as bs
from datetime import datetime
from utils import make_request
from time import sleep
import sys
import os


class BTScraper:
    def __init__(self, uri):
        self._base_uri = uri

    def download_mining_forum(self, dirname='BitcoinTalk-Forum'):
        ## Getting path of current directory and appending dirname ##
        self._base_path = f"{__file__[0:__file__.rfind('/')]}/{dirname}/"
        self._current_path = self._base_path
        self._start = datetime.now()
        ## Creating directory if it doesn't exist ##
        if not os.path.exists(self._base_path):
            os.mkdir(self._base_path)
        ## Start downloading pages ##
        self._download_mining_page()

    def _save_html_page(self, path, content):
        with open(f'{path}.html', 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Successfully saved '{path[path.rfind('/') + 1:]}.html' into '{path[:path.rfind('/')]}' !")
        print('@~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~@\n')

    def _retrieve_html(self, uri):
        print('@~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~@')
        now = datetime.now()
        print(f'\t\t\t{now}\t(elapsed: {now - self._start})')
        html = make_request(uri, prefix='\t\t').text
        soup = bs(html, 'html.parser')
        return html, soup

    def _download_mining_page(self, retry=0, max_retry=3):
        try:
            print(
                '+--------------------------------------------------------------------------------------------------------+\n'
                '|                                        DOWNLOADING MINING PAGE                                         |\n'
                '+--------------------------------------------------------------------------------------------------------+\n'
            )
            ## Making request to retrieve html, and saving it ##
            html, soup = self._retrieve_html(self._base_uri)
            ## Getting the title of the page to name the html file ##
            title = soup.find('title').text
            self._save_html_page(path=f'{self._base_path}{title}', content=html)
            self._download_childboards(soup)
        except Exception as e:
            print(f'Error: {e}', file=sys.stderr)
            ## Retry if an error occured (up to 3 times) ##
            if retry < max_retry:
                print(f'\nRetrying for the {retry + 1} time...\n')
                self._download_mining_page(retry + 1)
            exit(1)

    def _download_childboards(self, soup):
        ## Retrieving the table of childboards ##
        table = soup.find('body').find_all('div')[1].find_all('div')[2].find_all('tr')[1:]
        ## Create childboards directory if it doesn't exist ##
        self._current_path = f'{self._base_path}Childboards/'
        if not os.path.exists(self._current_path):
            os.mkdir(self._current_path)
        ## Iterating over each board to download all of their pages ##
        for board in table:
            ## Getting a row of the table, containing informations about a board ##
            infos = board.find_all('td')
            ## If there are childboards inside current childboard, skip them ##
            if len(infos) == 1:
                continue
            print(
                '+--------------------------------------------------------------------------------------------------------+\n'
                '|                                         DOWNLOADING CHILDBOARD                                         |\n'
                '+--------------------------------------------------------------------------------------------------------+\n'
            )
            uri = infos[1].find('a').get('href')
            html, soup = self._retrieve_html(uri)
            soup = bs(html, 'html.parser')
            ## Getting the title of the page to name the board's directory ##
            title = soup.find('title').text
            forum_path = f'{self._current_path}{title}/'
            ## Creating a directory for current board if it doesn't exist ##
            if not os.path.exists(forum_path):
                os.mkdir(forum_path)
                print(f'Directory \'{title}\' created !')
            ## Getting the number of pages to know how many requests we'll have to do ##
            page_anchors = soup.find('td', attrs={'class': 'middletext'}).find_all('a', attrs={'class': 'navPages'})
            pages_nb = int(page_anchors[-2].text) if len(page_anchors) > 1 else 1
            print('@~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~@\n')
            self._download_forum(path=forum_path, base_uri=uri[:uri.index('=') + 1], pages_nb=pages_nb, forum_id=uri[uri.index('=') + 1:])

    def _download_forum(self, path, base_uri, pages_nb, forum_id):
        print(
            '+--------------------------------------------------------------------------------------------------------+\n'
            '|                                         DOWNLOADING FORUM PAGES                                        |\n'
            '+--------------------------------------------------------------------------------------------------------+\n'
        )
        for page_nb in range(0, pages_nb):
            page_id = str(int(float(forum_id))) + f'.{page_nb * 40}'
            uri = f'{base_uri}{page_id}'
            self._download_forum_page(path=path, uri=uri, page_nb=page_nb + 1)

    def _download_forum_page(self, path, uri, page_nb):
        page_name = f'Page_{str(page_nb).zfill(3)}'
        print(f'DOWNLOADING FORUM {page_name}:'.rjust(62, ' '))
        page_directory = f'{path}{page_name}/'
        html, soup = self._retrieve_html(uri)
        ## Creating a directory for current page if it doesn't exist ##
        if not os.path.exists(page_directory):
            os.mkdir(page_directory)
            print(f'Directory \'{page_directory}\' created !')
        self._save_html_page(path=page_directory + page_name, content=html)
        self._download_topics(path=page_directory, soup=soup)

    def _download_topics(self, path, soup):
        divs = soup.find('div', attrs={'id': 'bodyarea'}).find_all('div', attrs={'class': 'tborder'})
        ## If there are 3 divs, it means that the forum contains at least one childboard that we want to avoid/skip ##
        table = divs[0].find_all('tr')[1:] if len(divs) == 2 else divs[1].find_all('tr')[1:]
        ## Creating a directory for topics if it doesn't exist ##
        topics_directory = f'{path}Topics/'
        if not os.path.exists(topics_directory):
            os.mkdir(topics_directory)
        ## Iterating over every row in the board to save topics ##
        for row, i in zip(table, range(0, len(table))):
            print(
                '+--------------------------------------------------------------------------------------------------------+\n'
                '|                                           DOWNLOADING TOPIC                                            |\n'
                '+--------------------------------------------------------------------------------------------------------+\n'
            )
            ## Creating a directory for current topic if it doesn't exist ##
            topic_directory = f'{topics_directory}Topic_{str(i).zfill(3)}/'
            if not os.path.exists(topic_directory):
                os.mkdir(topic_directory)
            uri = row.find_all('td')[2].find('a').get('href')
            _, topic_soup = self._retrieve_html(uri)
            page_anchors = topic_soup.find('td', attrs={'class': 'middletext'}).find_all('a', attrs={'class': 'navPages'})
            pages_nb = int(page_anchors[-2].text) if len(page_anchors) > 1 else 1
            print('@~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~@\n')
            self._download_topic_pages(path=topic_directory, base_uri=uri[:uri.index('=') + 1], pages_nb=pages_nb, topic_id=uri[uri.index('=') + 1:])

    def _download_topic_pages(self, path, base_uri, pages_nb, topic_id):
        for page_nb in range(0, pages_nb):
            page_name = f'Page_{str(page_nb).zfill(3)}'
            page_id = str(int(float(topic_id))) + f'.{page_nb * 20}'
            topic_page_path = f'{path}{page_name}'
            if os.path.exists(f'{topic_page_path}.html'):
                print(f'Page {page_name} already exists, skipping')
                continue
            print(f'DOWNLOADING TOPIC {page_name}:'.rjust(62, ' '))
            uri = f'{base_uri}{page_id}'
            html, _ = self._retrieve_html(uri=uri)
            self._save_html_page(path=topic_page_path, content=html)
            sleep(0.5)
        sleep(0.5)


if __name__ == '__main__':
    base_uri = 'https://bitcointalk.org/index.php?board=14.0'
    bts = BTScraper(base_uri)
    bts.download_mining_forum()