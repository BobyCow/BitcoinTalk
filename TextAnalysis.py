from signal import signal, SIGINT
import matplotlib.pyplot as plt
from datetime import datetime
from spacy.matcher import Matcher
import numpy as np
import mplcursors
import cursor
import spacy
import json
import math
import sys
import os


class Analyzer:
    def __init__(self, model='en_core_web_sm'):
        cursor.hide()
        self._data = None
        self._rules = [
            [{'POS': 'NOUN'}, {'POS': 'VERB'}],
            [{'POS': 'ADJ'}, {'POS': 'NOUN'}],
            [{'POS': 'VERB'}, {'POS': 'ADJ'}, {'POS': 'NOUN'}],
            [{'POS': 'NOUN'}, {'POS': 'VERB'}, {'POS': 'ADV'}],
            [{'POS': 'NOUN'}, {'POS': 'ADP'}, {'POS': 'NOUN'}],
            [{'POS': 'NOUN'}, {'LOWER': '/'}, {'POS': 'NOUN'}]
        ]
        try:
            self._nlp = spacy.load(model)
        except Exception:
            try:
                os.system(f'python -m spacy download {model}')
                self._nlp = spacy.load(model)
            except Exception:
                raise Exception('Spacy error: try to install requirements.txt\nSee https://github.com/BobyCow/BitcoinTalk for more instructions')
        print()

    @staticmethod
    def exit(sig=None, frame=None):
        if sig or frame:
            print('\n\nCtrl+C detected')
        cursor.show()
        exit(0)

    @staticmethod
    def _message(msg):
        print(f'[{datetime.now()}] {msg}')

    @staticmethod
    def _save_json(data, filename, indent=2, mode='w'):
        with open(filename, mode) as file:
            json.dump(data, file, indent=indent)

    def load_data(self, json_path='BitcoinTalk-data.json'):
        self._message(f'Loading data from {json_path}...')
        start = datetime.now()
        with open(json_path, 'r', encoding='utf-8', buffering=2000) as file:
            self._data = json.load(file)
        self._message(f'Data extracted in {datetime.now() - start}\n')

    def _is_token_valid(self, token):
        if not token.is_punct \
            and not token.is_stop \
            and not token.pos_ == 'SPACE' \
            and not token.pos_ == 'X' \
            and (len(token.text) > 1 and token.pos_ != 'SYM'):
            # and token.lemma_ in self._nlp.vocab:
            return True
        return False

    def scan(self):
        if not self._data:
            raise Exception('self._data is None')
        self.boards = {key: {} for key in self._data.keys() if type(self._data[key]) == dict}
        self._message(f'Boards: {self.boards}\n')
        self.topicnames = {}
        self._matcher = Matcher(self._nlp.vocab)
        self._matcher.add('rules', self._rules)
        for boardname in self.boards.keys():
            print(f'------------------ {boardname} ------------------'.center(200))
            self.topicnames[boardname] = [topicname for topicname in self._data[boardname].keys()]
            for topicname in self.topicnames[boardname][:5]: # REMOVE [:5] if you want this function to scan all topics
                pages = self._data[boardname][topicname]['total_pages']
                self._message(f"Processing {boardname} // {topicname} ({pages} page{'' if pages == 1 else 's'})")
                texts = [post['raw_content'].lower() for page in range(1, pages + 1) for post in self._data[boardname][topicname][str(page)]['posts']]
                self.boards[boardname][topicname] = {'words': {}, 'metadata': {'nb_of_words': 0, 'nb_of_documents': len(texts)}}
                for doc, post_id in zip(self._nlp.pipe(texts), range(0, len(texts))):
                    self._process_analysis(boardname, topicname, doc, post_id)
                self._compute_tfidf(boardname, topicname)
            print()
        self._save_json(self.boards, 'results.json')

    def _process_analysis(self, boardname, topicname, doc, post_id):
        lemmatized_doc = self._nlp(' '.join([token.lemma_ for token in doc]).replace(' / ', '/'))
        matches = self._matcher(lemmatized_doc)
        ngrams = [lemmatized_doc[start:end].text for _, start, end in matches]
        for ngram in ngrams:
            if ngram not in self.boards[boardname][topicname]['words']:
                self.boards[boardname][topicname]['words'][ngram] = {'occurrences': 1, 'in_docs': [post_id]}
            else:
                self.boards[boardname][topicname]['words'][ngram]['occurrences'] += 1
                if post_id not in self.boards[boardname][topicname]['words'][ngram]['in_docs']:
                    self.boards[boardname][topicname]['words'][ngram]['in_docs'].append(post_id)
        for token in lemmatized_doc:
            self.boards[boardname][topicname]['metadata']['nb_of_words'] += 1
            if self._is_token_valid(token):
                if token.lemma_ not in self.boards[boardname][topicname]['words']:
                    self.boards[boardname][topicname]['words'][token.lemma_] = {'occurrences': 1, 'in_docs': [post_id]}
                else:
                    self.boards[boardname][topicname]['words'][token.lemma_]['occurrences'] += 1
                    if post_id not in self.boards[boardname][topicname]['words'][token.lemma_]['in_docs']:
                        self.boards[boardname][topicname]['words'][token.lemma_]['in_docs'].append(post_id)

    def _compute_tfidf(self, boardname, topicname):
        for word in self.boards[boardname][topicname]['words'].keys():
            tf = self.boards[boardname][topicname]['words'][word]['occurrences'] / self.boards[boardname][topicname]['metadata']['nb_of_words']
            idf = math.log(self.boards[boardname][topicname]['metadata']['nb_of_documents'] / len(self.boards[boardname][topicname]['words'][word]['in_docs']))
            tf_idf = tf * idf
            self.boards[boardname][topicname]['words'][word]['tf'] = tf
            self.boards[boardname][topicname]['words'][word]['idf'] = idf
            self.boards[boardname][topicname]['words'][word]['tf-idf'] = tf_idf
        self.boards[boardname][topicname]['words'] = dict(sorted(self.boards[boardname][topicname]['words'].items(), key=lambda x: x[1]['occurrences'], reverse=True))

    def show_histogram(self, board, topic):
        print(f'Histogram of: {board} / {topic}')
        nb_to_show = 50
        bar_width = 0.3
        tfidf_scale = 300
        words, tfuencies, occurrences = [], [], []
        for w in self.boards[board][topic]['words'].keys():
            occurrences.append(self.boards[board][topic]['words'][w]['occurrences'])
            tfuencies.append(self.boards[board][topic]['words'][w]['tf-idf'] * tfidf_scale)
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
        b2 = ax.bar(x_ind[:nb_to_show] + bar_width, tfuencies[:nb_to_show], bar_width, color='orange', zorder=3, edgecolor='black')
        ax.legend((b1[0], b2[0]), ('occurrences', f'tf-idf (x{tfidf_scale})'))
        mplcursors.cursor(hover=True)
        fig.tight_layout()
        plt.show()


if __name__ == '__main__':
    # try:
    a = Analyzer()
    signal(SIGINT, a.exit)
    a.load_data()
    a.scan()
    print('\n')
    for boardname in a.boards.keys():
        for topic in a.boards[boardname].keys():
            a.show_histogram(boardname, topic)
    a.exit()
    # except Exception as e:
    #     print(f'\nIn: {e.__traceback__.tb_frame.f_code.co_filename}\nType: {type(e).__name__}', file=sys.stderr)
    #     print(e, file=sys.stderr)
    #     exit(-1)