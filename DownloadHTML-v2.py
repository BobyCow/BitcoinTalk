from bs4 import BeautifulSoup as bs
from signal import signal, SIGINT
from utils import make_request
from datetime import datetime
from time import sleep
import hashlib
import cursor
import json
import sys
import os


class BTC_Downloader:
    def __init__(self, base_uri=None, base_path='BitcoinTalk-Forum/'):
        if not base_uri:
            raise Exception("Missing keyword argument 'base_uri'")
        self._base_path = base_path
        # Check if 'BitcoinTalk-Forum' directory exists and create it if it doesn't
        if not os.path.exists(self._base_path):
            os.mkdir(self._base_path)
        self._base_uri = base_uri
        # In case the user stops the program (Ctrl+C) while it's running, we need to set a default value (None) for:
        #   - self._dl_start (if the program stops before the download starts)
        #   - self._check_end (if the program stops before the checking is over)
        self._dl_start = None
        self._check_end = None
        self._failures = 0
        cursor.hide()

    def are_pages_missing(self):
        # Start timers
        self._start = datetime.now()
        self._check_start = datetime.now()
        # Download the first page in case we need to get global informations about the forum
        base_page = self._download_base_page()
        # To avoid encoding problems we first need to decode the content in latin1, then encoding and decoding it in utf-8
        content = base_page.content.decode('latin1').encode('utf-8').decode('utf-8')
        # Write the content into a file
        with open(f'{self._base_path}/Mining.html', 'w', encoding='utf-8') as file:
            file.write(content)
        # Start analyzing https://bitcointalk.org/index.php?board=14.0 (Mining)
        print('------------------------ FETCHING ONLINE DATA ------------------------'.center(200))
        online_boards = self._get_online_board_list(base_page.content)
        # Saving results into a json file
        with open('file_online.json', 'w', encoding='utf-8') as file:
            json.dump(online_boards, file, indent=2)
        print()
        # If the user asks for a full update, we don't need to check what's already downloaded
        if len(sys.argv) >= 2 and ('--update' in sys.argv or '-u' in sys.argv):
            print('------------------------ UPDATING ALL DATA ------------------------'.center(200))
            self._download_list = online_boards
            self._check_end = datetime.now()
            return True
        # Else, we need to retrieve data about all topics that were already downloaded, in order to compare the list with online topics
        else:
            print('------------------------ FETCHING LOCAL DATA ------------------------'.center(200))
            local_boards = self._get_local_board_list()
            with open('file_local.json', 'w', encoding='utf-8') as file:
                json.dump(local_boards, file, indent=2)
            # Compare online_boards with local_boards to create a download_list
            return self._check_missing_pages(online_boards, local_boards)

    def _check_missing_pages(self, online_boards, local_boards):
        self._download_list = {}
        # We first need to iterate over the online list which contains all topics present on the forum
        for boardname, boardinfos in online_boards.items():
            # We check if current board is present in the local list
            if boardname in local_boards.keys():
                # If it is present, we'll have to check topics one by one
                for topic in boardinfos['topics']:
                    # We create a "topic_to_compare" in order to get rid of the "boardpage" field (inside the online list but not the local one)
                    topic_to_cmp = {
                        'first_page_link': topic['first_page_link'],
                        'title': topic['title'],
                        'pages': topic['pages']
                    }
                    # If the topic is not present into the local list, then we need to append it into the download list
                    if topic_to_cmp not in local_boards[boardname]['topics']:
                        # Create a board object the first time
                        if boardname not in self._download_list.keys():
                            self._download_list[boardname] = {
                                'first_page': boardinfos['first_page'],
                                'pages': boardinfos['pages'],
                                'links': boardinfos['links'],
                                'topics': []
                            }
                        # Then we just need to append topics to the board
                        self._download_list[boardname]['topics'].append(topic)
            # If the board is not present, just copy it into the download list
            else:
                self._download_list[boardname] = boardinfos
        # Save the download list into a json file
        with open('download_list.json', 'w', encoding='utf-8') as file:
            json.dump(self._download_list, file, indent=2)
        # Stop the checking timer
        self._check_end = datetime.now()
        # Return False if there is nothing to download, otherwise return True
        return False if len(self._download_list) == 0 else True

    def _retrieve_html(self, uri, retry=1, max_retries=5):
        # Make a request to get the first page of the board
        response = make_request(uri)
        ## To avoid encoding problems we first need to decode the content in latin1, then encoding and decoding it in utf-8
        content = response.content.decode('latin1').encode('utf-8').decode('utf-8')
        if response.status_code != 200 or content.count('cf-error') >= 1:
            if retry != max_retries:
                return self._retrieve_html(uri, retry=retry+1)
            else:
                print(f'Failed to download {uri} after {retry} attempts')
                self._failures += 1
        return content

    def start_downloading(self):
        # Setting a delay between requests, to avoid 429 (too many requests) and 503 (service unavailable) error codes
        delay = 0.5
        # Start download timer
        self._dl_start = datetime.now()
        # Iterate over the download list
        for boardname, boardinfos in self._download_list.items():
            boardpages = boardinfos['pages']
            boardpath = f'{self._base_path}/{boardname}'
            # Create a directory for the current board if it doesn't exist
            if not os.path.exists(f'{boardpath}'):
                os.mkdir(f'{boardpath}')
                print(f'\nCreated `{boardname}` directory')
            content = self._retrieve_html(boardinfos['links'][0])
            # Save the result into a file stored into the board directory
            with open(f'{boardpath}/{boardname}.html', 'w', encoding='utf-8') as file:
                file.write(content)
            # Iterate over all topics of the board
            for topic in boardinfos['topics']:
                # Get global infos about the topic (nb of pages, base uri, id)
                topic_pages = topic['pages']
                base_uri = topic['first_page_link'][:topic['first_page_link'].index('=') + 1]
                topic_id = topic['first_page_link'][topic['first_page_link'].index('=') + 1:]
                # Create a directory for the topic (if it doesn't exist), based on its title (encoded with sha1)
                topic_dir = hashlib.sha1(str.encode(topic['title'])).hexdigest()
                topic_path = f'{boardpath}/{topic_dir}'
                if not os.path.exists(topic_path):
                    os.mkdir(topic_path)
                    print(f"\nCreated `{topic_dir}` directory for `{topic['title']}`")
                for page_nb in range(0, topic['pages']):
                    print(f'\n{datetime.now()}')
                    print(f"└── {boardname} ({topic['boardpage']}/{boardpages})")
                    print(f"    └── {topic['title']} ({page_nb + 1}/{topic_pages})")
                    # Build the topic uri with its ID/base uri (the id is a decimal number, and the numbers after the comma are a multiple of 20 in ascending order)
                    page_id = str(int(float(topic_id))) + f'.{page_nb * 20}'
                    uri = f'{base_uri}{page_id}'
                    # Retrieve html of the topic page
                    content = self._retrieve_html(uri)
                    # Write the content into a file
                    with open(f'{topic_path}/{page_nb + 1}.html', 'w', encoding='utf-8') as file:
                        file.write(content)
                    print(f"Successfully downloaded `{topic['title']}` ({page_nb + 1}/{topic_pages})!")
                    # Wait before doing another request
                    sleep(delay)
        self.display_logs()

    # SIGINT handler
    def display_logs(self, sig=None, frame=None):
        # Stop timers
        self._dl_end = datetime.now()
        self._end = datetime.now()
        if sig:
            print('\nCtrl+C detected!')
            # Check if the program was stopped during the checking phase
            if not self._check_end:
                self._check_end = datetime.now()
        print('\n#----------------------- Infos -----------------------#')
        print(f'\tChecking duration:\t{self._check_end - self._check_start}')
        print(f"\tDownload duration:\t{self._dl_end - self._dl_start if self._dl_start else 'Undefined'}")
        print(f'\tTotal duration:\t\t{self._end - self._start}')
        print(f'\tFailures:\t\t{self._failures}')
        print('#-----------------------------------------------------#')
        cursor.show()
        exit(0)

    def _download_base_page(self):
        print('Downloading `Mining` page...')
        response = make_request(self._base_uri)
        print()
        return response

    @staticmethod
    def _progress_bar(topic_nb, max_topics, reset=False):
        if max_topics == 0:
            return
        toolbar_width = 50
        square = u'\u2588'
        percentage = round(100 * topic_nb / max_topics, 2)
        rounded = round(percentage)
        # Ugly way to print a 100% progress bar a the end of the process
        if reset:
            sys.stdout.write('\n\n\033[F')
            sys.stdout.write('\033[K')
            print(f"|{square * toolbar_width}| {rounded}%\n")
            return
        # Display progress bar
        p_str = f' {percentage}%'
        sys.stdout.write('|%s| %s' % (' ' * toolbar_width, p_str))
        sys.stdout.flush()
        sys.stdout.write('\b' * (toolbar_width + (len(p_str) + 1) + 1))
        sys.stdout.write(square * int(rounded / 2))
        sys.stdout.flush()
        # Return to the previous line
        sys.stdout.write('\033[F')
        # Erase the line
        sys.stdout.write('\033[K')

    def _get_local_board_list(self):
        boards = {}
        max_topics = 0
        # If there is no board, return an empty dictionary
        if not os.path.exists(self._base_path):
            return boards
        # Else, get names of the boards
        boardnames = [name for name in os.listdir(self._base_path) if os.path.isdir(os.path.join(self._base_path, name))]
        # Get nb of topics in local files
        for boardname in boardnames:
            max_topics += len([dir for dir in os.listdir(os.path.join(self._base_path, boardname))])
        # Iterate over all boards
        for name in boardnames:
            # Append boarname to base path
            board_path = os.path.join(self._base_path, name)
            # Get all topic directories inside the board directory
            topic_hashes = [hash for hash in os.listdir(board_path) if os.path.isdir(f'{board_path}/{hash}')]
            # Read the first page of the board to get its content
            with open(f'{board_path}/{name}.html', 'r', encoding='latin1') as file:
                firstpage = file.read()
                # Creating a bs4 soup
                soup = bs(firstpage, 'html.parser')
            # Retrieving data about the board (base_uri, id, nb of pages, and links of all its pages)
            board_base_uri = soup.find('link', attrs={'rel': 'index'}).get('href')
            board_uri = board_base_uri[:board_base_uri.index('=') + 1]
            board_id = board_base_uri[board_base_uri.index('=') + 1:]
            pages = int(soup.find('td', attrs={'id': 'toppages'}).findAll('a', attrs={'class': 'navPages'})[-2].text)
            # Build board uris with its ID/base uri (the id is a decimal number, and the numbers after the comma are a multiple of 40 in ascending order)
            boardlinks = [f"{board_uri}{str(int(float(board_id))) + f'.{nb * 40}'}" for nb in range(pages)]
            boards[name] = {
                'first_page': firstpage,
                'pages': pages,
                'links': boardlinks,
                'topics': []
            }
            # Iterate over all topics of the current board
            for topic, topic_nb in zip(topic_hashes, range(0, max_topics)):
                # Getting its path
                topicpath = os.path.join(board_path, topic)
                # Getting paths of its pages
                pagepaths = [os.path.join(topicpath, page) for page in os.listdir(topicpath) if not os.path.isdir(os.path.join(topicpath, page))]
                if len(pagepaths) == 0:
                    print(topicpath, 'is empty')
                    continue
                # Read the first page
                with open(pagepaths[0], 'r', encoding='utf-8') as file:
                    # Creating a bs4 soup
                    soup = bs(file.read(), 'html.parser')
                    # nb of pages
                    pages = len(pagepaths)
                    # Title of the topic without special characters / newlines / trailing spaces
                    title = soup.title.text.strip().replace(u'\x85', u' ').replace('\n', '')
                    # Display infos of the topic + progress bar
                    print(f"| {pagepaths[0]} | {title.center(115)} | {pages} {'pages' if pages > 1 else 'page'}")
                    self._progress_bar(topic_nb, max_topics)
                    # Get the link of the topic's page
                    prev_link = soup.find('link', attrs={'rel': 'prev'}).get('href')
                    boards[name]['topics'].append({
                        'first_page_link': prev_link[:prev_link.index(';')],
                        'title': title,
                        'pages': pages
                    })
        # Reset the progress bar
        self._progress_bar(max_topics, max_topics, reset=True)
        return boards

    def _get_online_board_list(self, html):
        boards = {}
        delay = 0.00001
        soup = bs(html, 'html.parser')
        ## Retrieving boards' data from table
        results = [tr for tr in soup.find('table', attrs={'border': '0', 'width': '100%', 'cellspacing': '1', 'cellpadding': '5', 'class': 'bordercolor'}).findAll('tr') if len(tr) == 9]
        ## Constructing a dict {'board_name': 'board_link'}
        for tr in results:
            ## Getting board's name and uri in order to retrieve its data
            boardname = tr.findAll('a')[1].text.strip()
            board_base_uri = tr.findAll('a')[1].get('href')
            ## Making request
            print(f'{datetime.now()}\tDownloading `{boardname}`...')
            response = make_request(board_base_uri)
            print()
            ## Creating soup
            soup = bs(response.content, 'html.parser')
            ## Getting the number of pages to know how many requests we'll have to do
            page_anchors = soup.find('td', attrs={'class': 'middletext'}).findAll('a', attrs={'class': 'navPages'})
            pages_nb = int(page_anchors[-2].text) if len(page_anchors) > 1 else 1
            ## Constructing pages uris based on the board_page's base_uri and id
            board_uri = board_base_uri[:board_base_uri.index('=') + 1]
            board_id = board_base_uri[board_base_uri.index('=') + 1:]
            boardlinks = [f"{board_uri}{str(int(float(board_id))) + f'.{nb * 40}'}" for nb in range(pages_nb)]
            ## To avoid encoding problems we first need to decode the content in latin1, then encoding and decoding it in utf-8
            content = response.content.decode('latin1').encode('utf-8').decode('utf-8')
            ## Storing results inside boards
            boards[boardname] = {
                'first_page': content,
                'pages': pages_nb,
                'links': boardlinks,
                'topics': []
            }
            print(f"{pages_nb} pages to download:")
            for boardlink, page in zip(boards[boardname]['links'], range(1, pages_nb + 1)):
                response = make_request(boardlink)
                soup = bs(response.content, 'html.parser')
                table = soup.find('table', attrs={'border': '0', 'width': '100%', 'cellspacing': '1', 'cellpadding': '4', 'class': 'bordercolor'})
                topics_nb = 0
                for name, pages, link in self._get_topic_list_from_table(table):
                    boards[boardname]['topics'].append({
                        'first_page_link': link,
                        'title': name,
                        'pages': pages,
                        'boardpage': page
                    })
                    topics_nb += 1
                    print(u'\u2588', end='', flush=True)
                    sleep(delay)
                print(f"\n{datetime.now()}\tRetrieved data of {topics_nb} topic{'s' if topics_nb > 1 else ''} on page {page}/{pages_nb} of {boardname}!\n")
        return boards

    def _get_topic_list_from_table(self, table):
        ## Retrieving all topics' title from a table. Skipping the first element corresponding to the header of the table
        results = [tr.findAll('td')[2] for tr in table.findAll('tr')[1:]]
        for res in results:
            ## Getting rid of \xa0 special character (\xa0 is actually non-breaking space in Latin1 (ISO 8859-1)),
            ## and splitting line to get topic's name and nb of pages into different variables
            name, *pages = res.text.strip().replace(u'\xa0', u' ').split('\n')
            ## Retrieving link of the current topic
            link = res.find('a').get('href')
            ## Converting "« 1 2 3 4 5  All »" to a list of integers like [1, 2, 3, 4, 5]
            if pages:
                pages = [int(word) for word in ''.join(pages).split() if word.isdigit()]
            else:
                pages = [1]
            ## Returning elements one by one for processing
            yield name.strip(), max(pages), link


if __name__ == '__main__':
    try:
        base_uri = 'https://bitcointalk.org/index.php?board=14.0'
        bts = BTC_Downloader(base_uri)
        # Detect Ctrl+C
        signal(SIGINT, bts.display_logs)
        if bts.are_pages_missing():
            bts.start_downloading()
    except Exception as e:
        print(e, file=sys.stderr)