from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta
from signal import signal, SIGINT
from time import sleep
import calendar
import cursor
import json
import os


class BitcoinTalkScraper:
    def __init__(self):
        self._boards = []
        self._data = {}
        self._save_file = 'BitcoinTalk-data.json'
        cursor.hide()

    @staticmethod
    def _display_infos(board):
        print('#--------------------------------------- BOARD ---------------------------------------#')
        print(f"Title:\t\t{board['title']}")
        print(f"Moderator:\t{board['moderator']['name']} ({board['moderator']['profile']})")
        print(f"Description:\t{board['description']}")
        print(f"URL:\t\t{board['link']}")
        print(f"Lastpost:\t{datetime.fromtimestamp(board['lastpost']['timestamp'])}")
        print(f"Available:\t{board['available']}{'' if board['available'] else ' (IT WILL NOT BE TREATED)'}")
        print('#-------------------------------------------------------------------------------------#\n')

    def _get_timestamp(self, date_str):
        if 'on ' in date_str:
            date_str = date_str.replace('on ', '')
        if 'Today at' in date_str:
            today = datetime.today()
            date_str = date_str.replace('Today at', f'{calendar.month_name[today.month]} {str(today.day).zfill(2)}, {today.year},')
        datetime_obj = datetime.strptime(date_str, '%B %d, %Y, %I:%M:%S %p')
        timestamp = datetime.timestamp(datetime_obj)
        return timestamp

    def _get_TDL(self, td):
        link = td.find('a').get('href')
        title, *description, _ = [text.strip() for text in td.text.split('\n') if len(text) > 0]
        description = description[0] if description else None
        return title, description, link

    def _get_moderator(self, td):
        anchor = td.find('a', attrs={'title': 'Board Moderator'})
        return {
            'name': anchor.text,
            'profile': anchor.get('href')
        }

    def _get_PT(self, td):
        posts, topics = [text.strip() for text in td.text.split('\n') if len(text) > 0]
        return int(posts[:posts.index(' ')]), int(topics[:topics.index(' ')])

    def _get_lastpost(self, td):
        anchors = td.find_all('a')
        date = [text.strip() for text in td.text.split('\n') if len(text) > 0][-1]
        return {
            'by': {
                'name': anchors[0].text,
                'profile': anchors[0].get('href')
            },
            'link': anchors[1].get('href'),
            'timestamp': self._get_timestamp(date)
        }

    def _get_author(self, text, anchor=None):
        if anchor:
            name, rank, status, activity, merit, *sentence = [info.strip() for info in text.split('\n') if len(info) > 0]
            return {
                'name': name,
                'profile': anchor.get('href'),
                'status': status,
                'rank': rank,
                'activity': activity,
                'merit': merit,
                'sentence': sentence[0] if len(sentence) > 0 else None
            }
        else:
            name, profile = [info.strip() for info in text.split('\n') if len(info) > 0]
            return {
                'name': name,
                'profile': profile,
                'status': 'Offline',
                'rank': None,
                'activity': None,
                'merit': None,
                'sentence': None
            }

    def _extract_board_infos(self, tds):
        title, description, link = self._get_TDL(tds[1])
        moderator = self._get_moderator(tds[1])
        posts, topics = self._get_PT(tds[2])
        lastpost = self._get_lastpost(tds[3])
        return title, description, link, moderator, posts, topics, lastpost

    def _get_childboards(self, path='tmp'):
        self._path = path
        with open(f'{path}/Mining.html', 'r') as file:
            html = file.read()
        ## Parse html ##
        soup = bs(html, 'html.parser')
        ## Getting array of child boards ##
        table = soup.find('body').find_all('div')[1].find_all('div')[2].find_all('tr')[1:]
        ## Iterating over every board ##
        for board in table:
            available = True
            infos = board.find_all('td')
            if len(infos) != 4:
                continue
            title, description, link, moderator, posts, topics, lastpost = self._extract_board_infos(infos)
            ## Board is missing ##
            if not os.path.exists(f'{path}/{title}/'):
                available = False
            ## Appending a board object containing all informations ##
            self._boards.append({
                'title': title,
                'link': link,
                'description': description,
                'moderator': moderator,
                'posts': posts,
                'topics': topics,
                'lastpost': lastpost,
                'available': available
            })
        return self._boards[:]

    def save_data(self, signum=None, frame=None):
        if signum:
            print('\n\nCtrl+C detected, saving data ...')
        with open(self._save_file, 'w', encoding='utf-8') as file:
            json.dump(self._data, file, indent=2)
        print(f'\nData saved in `{self._save_file}`')
        print('Exiting with code 0 ...')
        cursor.show()
        exit(0)

    def extract_data(self):
        signal(SIGINT, self.save_data)
        self._get_childboards()
        self._data['available_boards'] = len([board for board in self._boards if board['available']])
        for board in self._boards:
            self._display_infos(board)
            self._data[board['title']] = {}
            if not board['available']:
                print(f"Skipping `{board['title']}` board\n")
                self._data[board['title']] = {'error': 'not_available'}
                continue
            board_path = f"{self._path}/{board['title']}"
            with open(f"{board_path}/{board['title']}.html", 'r', encoding='utf-8') as file:
                soup = bs(file.read(), 'html.parser')
            page_tags = soup.find('td', attrs={'class': 'middletext', 'id': 'toppages'}).findAll('a', attrs={'class': 'navPages'})
            self._data[board['title']]['total_pages'] = int(page_tags[-2].text) if len(page_tags) > 1 else 1
            self._skim_topics(board=board, path=board_path)
            print()
        print('DONE')
        return self._data

    def _skim_topics(self, board, path):
        self._data[board['title']] = {}
        topic_hashes = [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]
        ## Scrape topic infos in this loop ##
        for th in topic_hashes:
            ## List of all topic's html pages ##
            topic_pages = [name for name in os.listdir(f'{path}/{th}/') if name.endswith('.html')]
            infos = self._get_topic_infos(path=f'{path}/{th}/1.html')
            self._data[board['title']][infos['title']] = {
                'started_by': infos['started_by'],
                'started_at': infos['started_at'],
                'total_pages': len(topic_pages)
            }
            topic_pages = sorted(topic_pages, key=lambda x: int(x[:x.index('.')]))
            ## Scrape topic posts in this loop ##
            for tp in topic_pages:
                filename = f'{path}/{th}/{tp}'
                print(f'\n{datetime.now()}')
                print(f"└── {self._path}")
                print(f"    └── {board['title']}")
                print(f'        └── {th}')
                print(f"            └── {tp} ({int(tp[:tp.index('.')])}/{len(topic_pages)})")
                with open(filename, 'r', encoding='utf-8') as file:
                    soup = bs(file.read(), 'html.parser')
                self._data[board['title']][infos['title']][tp.replace('.html', '')] = {'posts': []}
                self._extract_posts(soup, board, infos, tp)

    def _get_topic_infos(self, path):
        with open(path, 'r', encoding='utf-8') as file:
            soup = bs(file.read(), 'html.parser')
        title = soup.title.text
        form = soup.find('form', attrs={'id': 'quickModForm'})
        posts = [post.find('td') for post in form.find('table').find_all('tr') if len(post.find('td')) == 5]
        try:
            date = form.find('span', attrs={'class': 'edited'}).text
        except Exception:
            date = form.find_all('td', attrs={'valign': 'middle'})[1].find_all('div')[1].text
        try:
            started_by = {'name': posts[0].find('a').text, 'profile': posts[0].find('a').get('href')}
        except Exception:
            started_by = {'name': posts[0].find('b').text, 'profile': 'noprofile'}
        return {
            'title': title,
            'started_by': started_by,
            'started_at': self._get_timestamp(date)
        }

    @staticmethod
    def spinner():
        cursors = [u'\u25DF', u'\u25DE', u'\u25DD', u'\u25DC']
        while True:
            for cur in cursors:
                yield cur

    def _extract_posts(self, soup, board, infos, tp):
        delay = 0.005
        scraped_posts = 0
        start = datetime.now()
        one_second = timedelta(seconds=1)
        form = soup.find('form', attrs={'id': 'quickModForm'})
        posts = form.find('table').find_all('tr')
        for post, cur in zip(posts, self.spinner()):
            # Might be an add or something we don't care about
            if not post.find('div', attrs={'class': 'post'}) or len(post) != 5 or len(post.parent.attrs) != 4:
                continue
            print(u'\u2588', end='', flush=True)
            try:
                date = post.find('table').find('span', attrs={'class': 'edited'}).text
            except Exception:
                date = post.find('table').find_all('td', attrs={'valign': 'middle'})[1].find_all('div')[1].text
            try:
                author = self._get_author(post.find('td', attrs={'class': 'poster_info'}).text, post.find('img', attrs={'title': 'View Profile'}).parent)
            except Exception:
                author = self._get_author(post.find('td', attrs={'class': 'poster_info'}).text)
            content = post.find('div', attrs={'class': 'post'})
            self._data[board['title']][infos['title']][tp.replace('.html', '')]['posts'].append({
                'author': author,
                'html_content': str(content),
                'raw_content': content.get_text(separator='\n'),
                'last_edit': self._get_timestamp(date),
            })
            scraped_posts += 1
            elapsed = datetime.now() - start
            padding = ' ' * (25 - scraped_posts)
            info_str = f"{padding}{cur}  Scraped {scraped_posts} post{'s' if scraped_posts > 1 else ''} in {elapsed} second{'s' if elapsed > one_second else ''} ({delay} second{'s' if delay > 1 else ''} of delay)"
            print(info_str, end='', flush=True)
            sleep(delay)
            print('\b' * len(info_str), end='', flush=True)
        cur = u'\u25B8'
        info_str = f"{padding}{cur}  Scraped {scraped_posts} post{'s' if scraped_posts > 1 else ''} in {elapsed} second{'s' if elapsed > one_second else ''} ({delay} second{'s' if delay > 1 else ''} of delay)"
        print(info_str)
        print()


if __name__ == '__main__':
    bts = BitcoinTalkScraper()
    bts.extract_data()
    bts.save_data()