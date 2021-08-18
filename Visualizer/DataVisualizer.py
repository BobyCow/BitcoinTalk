import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import mplcursors
import random
import math
import json
import csv


class DataViz:
    def __init__(self):
        with open('WORDS/ignore.json', 'r') as file:
            self._ignore = json.load(file)['ignore']

    @staticmethod
    def _message(msg):
        print(f'[{datetime.now()}] {msg}')

    def load_data(self, json_path='raw_analysis_results.json'):
        self._message(f'Loading data from {json_path}...')
        start = datetime.now()
        with open(json_path, 'r', encoding='utf-8', buffering=2000) as file:
            self.boards = json.load(file)
        self._message(f'Data extracted in {datetime.now() - start}\n')

    def show_histogram_for_topic(self, board, topic, main_val='occurrences'):
        print(f'Histogram of: {board} / {topic}')
        nb_to_show = 50
        bar_width = 0.3
        tfidf_scale = 300
        words, frequencies, occurrences = [], [], []
        if main_val == 'occurrences' or main_val != 'tf-idf':
            values = self.boards[board][topic]['words'].keys()
        elif main_val == 'tf-idf':
            values = dict(sorted(self.boards[board][topic]['words'].items(), key=lambda x: x[1]['tf-idf'], reverse=True)).keys()
        for w in values:
            occurrences.append(self.boards[board][topic]['words'][w]['occurrences'])
            frequencies.append(self.boards[board][topic]['words'][w]['tf-idf'] * tfidf_scale)
            words.append(w)
        x_ind = np.arange(len(self.boards[board][topic]['words']))
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_title(f'{board} / {topic}')
        ax.grid(zorder=0)
        ax.set_xlabel('words')
        ax.set_xticklabels(words[:nb_to_show], rotation='vertical')
        ax.set_xticks(x_ind[:nb_to_show] + bar_width / 2)
        b1 = ax.bar(x_ind[:nb_to_show], occurrences[:nb_to_show], bar_width, color='red', zorder=3, edgecolor='black')
        b2 = ax.bar(x_ind[:nb_to_show] + bar_width, frequencies[:nb_to_show], bar_width, color='orange', zorder=3, edgecolor='black')
        if main_val == 'occurrences' or main_val != 'tf-idf':
            ax.legend((b1[0], b2[0]), ('occurrences', f'tf-idf (x{tfidf_scale})'))
        elif main_val == 'tf-idf':
            ax.legend((b2[0], b1[0]), (f'tf-idf (x{tfidf_scale})', 'occurrences'))
        mplcursors.cursor(hover=True)
        fig.tight_layout()
        plt.show()

    def show_histogram_with_words(self, words):
        n_best_words = 50
        for boardname in self.boards.keys():
            for topicname in self.boards[boardname].keys():
                best_occ = list(self.boards[boardname][topicname]['words'].keys())[:n_best_words]
                best_tfidf = [word[0] for word in sorted(self.boards[boardname][topicname]['words'].items(), key=lambda x: x[1]['tf-idf'], reverse=True)][:n_best_words]
                for w in words:
                    if (w in best_occ or w.replace(' ', '') in best_occ) \
                       or w.replace(' ', '') in topicname.replace(' ', '').lower():
                        self.show_histogram_for_topic(boardname, topicname)
                        break
                    if w in best_tfidf or w.replace(' ', '') in best_tfidf:
                        self.show_histogram_for_topic(boardname, topicname, main_val='tf-idf')
                        break

    def show_histogram_from_list(self, word_list=None, title='title', xlegend='xlegend', metric='occurrences'):
        if not word_list:
            return
        bar_width = 0.7
        x_ind = np.arange(len(word_list))
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_title(title)
        ax.grid(zorder=0)
        ax.set_xlabel('words')
        ax.set_xticklabels(xlegend, rotation='vertical')
        ax.set_xticks(x_ind)
        if metric == 'occurrences':
            ax.bar(x_ind, [word[1]['occurrences'] for word in word_list], bar_width, color='red', zorder=3, edgecolor='black')
        else:
            ax.bar(x_ind, [word[1]['tf-idf'] for word in word_list], bar_width, color='orange', zorder=3, edgecolor='black')
        mplcursors.cursor(hover=True)
        fig.tight_layout()
        plt.show()

    def compute_word_list_from_board(self, boardname, word_list=None):
        nb_to_show = 100
        words = {}
        for topicname in [key for key in self.boards[boardname].keys() if key != 'metadata']:
            for k, v in self.boards[boardname][topicname]['words'].items():
                if (word_list != None and k not in word_list) or k in self._ignore:
                    continue
                if k in words:
                    words[k]['occurrences'] += v['occurrences']
                    words[k]['in_docs'] += len(v['in_docs'])
                else:
                    words[k] = {
                        'occurrences': v['occurrences'],
                        'in_docs': len(v['in_docs'])
                    }
        for w in words.keys():
            tf = words[w]['occurrences'] / self.boards[boardname]['metadata']['nb_of_words']
            idf = math.log(self.boards[boardname]['metadata']['nb_of_documents'] / words[w]['in_docs'])
            words[w]['tf-idf'] = tf * idf
        best_occurrences = sorted(words.items(), key=lambda x: x[1]['occurrences'], reverse=True)[:nb_to_show]
        best_tfidf = sorted(words.items(), key=lambda x: x[1]['tf-idf'], reverse=True)[:nb_to_show]
        self.show_histogram_from_list(word_list=best_occurrences, title=f'{boardname} (best occurrences)', xlegend=[word[0] for word in best_occurrences])
        self.show_histogram_from_list(word_list=best_tfidf, title=f'{boardname} (best tf-idf)', xlegend=[word[0] for word in best_tfidf], metric='tf-idf')

    def _get_posts(self, board_to_process):
        posts = []
        list_of_boards = [key for key in self.boards.keys() if key != 'available_boards']
        boardnames = [board_to_process] if board_to_process in list_of_boards else list_of_boards
        for boardname in boardnames:
            for topicname in self.boards[boardname].keys():
                pages = [self.boards[boardname][topicname][str(page_nb)] for page_nb in range(1, self.boards[boardname][topicname]['total_pages'] + 1)]
                for page in pages:
                    for post in page['posts']:
                        posts.append(post)
        posts = sorted(posts, key=lambda x: x['last_edit'])
        return posts

    def show_posts_occurrences(self, board_to_process='all', step='month'):
        posts = self._get_posts(board_to_process)
        date_list = {}
        date_format = '%d/%m/%Y'
        day = timedelta(days=1)
        week = timedelta(days=7)
        month = timedelta(days=30.5)
        year = timedelta(days=365)
        if step == 'day':
            step = day
        if step == 'week':
            step = week
        if step == 'month':
            step = month
        if step == 'year':
            step = year
        timestamp_list = [post['last_edit'] for post in posts]
        d1 = datetime.strptime(datetime.fromtimestamp(timestamp_list[0]).strftime(date_format), date_format)
        d2 = datetime.strptime(datetime.fromtimestamp(timestamp_list[-1]).strftime(date_format), date_format)
        d = d1
        while d < d2:
            date_list[d.strftime(date_format)] = 0
            d += step
        for t in timestamp_list:
            for d in date_list.keys():
                if datetime.strptime(d, date_format).timestamp() <= t < (datetime.strptime(d, date_format) + week).timestamp():
                    date_list[d] += 1
                    break
        x = [*date_list.keys()]
        y = [*date_list.values()]
        plt.xticks(rotation=90)
        plt.plot(x, y)
        plt.show()

    @staticmethod
    def chunks(L, n):
        for i in range(0, len(L), n):
            yield L[i:i+n]

    def show_graph_from_topic_with_words(self, boardname, topicname, word_list):
        date_list = {}
        date_format = '%d/%m/%Y'
        one_week = timedelta(days=1)
        pages = [self.boards[boardname][topicname][str(page_nb)] for page_nb in range(1, self.boards[boardname][topicname]['total_pages'] + 1)]
        posts = sorted([post for page in pages for post in page['posts']], key=lambda x: x['last_edit'])
        timestamp_list = [post['last_edit'] for post in posts]
        d1 = datetime.strptime(datetime.fromtimestamp(timestamp_list[0]).strftime(date_format), date_format)
        d2 = datetime.strptime(datetime.fromtimestamp(timestamp_list[-1]).strftime(date_format), date_format)
        d = d1
        while d < d2:
            date_list[d.strftime(date_format)] = {}
            for word in word_list:
                date_list[d.strftime(date_format)][word] = 0
            d += one_week
        for post in posts:
            for w in word_list:
                if w in post['raw_content']:
                    for date in date_list.keys():
                        if datetime.strptime(date, date_format).timestamp() <= post['last_edit'] < (datetime.strptime(date, date_format) + one_week).timestamp():
                            date_list[date][w] += 1
                            break
        with open('data.csv', 'w') as file:
            writer = csv.writer(file, dialect='excel')
            x = [*date_list.keys()]
            writer.writerow([topicname] + word_list)
            for d in date_list.keys():
                writer.writerow([d] + [v for v in [*date_list[d].values()]])
            for wl in self.chunks(word_list, 3):
                for word in wl:
                    rgb = (random.random(), random.random(), random.random())
                    plt.plot(x, [date_list[wl][word] for wl in date_list.keys()], color=rgb, label=word, zorder=3)
                plt.grid(zorder=0)
                plt.xticks(rotation=45)
                plt.legend()
                plt.show()


if __name__ == '__main__':
    d = DataViz()
    d.load_data(json_path='raw_BitcoinTalk-data.json')
    with open('WORDS/Word_list_analysis.json', 'r') as file:
        d.show_graph_from_topic_with_words('Pools', 'KanoPool 0.9% fee 🐈 since 2014 - Solo 0.5% fee - Worldwide - 2432 blocks', json.load(file)['Word_list_analysis'])