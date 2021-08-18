from signal import signal, SIGINT
from datetime import datetime
from spacy.matcher import Matcher
import cursor
import spacy
import json
import math
import os


class Analyzer:
    def __init__(self, model='en_core_web_sm'):
        cursor.hide()
        self._data = None
        self._rules = [
            # bi-grams
            [{'LOWER': 'the'}, {'POS': 'NOUN'}],
            [{'POS': 'NOUN'}, {'POS': 'NOUN'}],
            [{'POS': 'NOUN'}, {'POS': 'VERB'}],
            [{'POS': 'ADJ'}, {'POS': 'NOUN'}],
            # tri-grams
            [{'POS': 'VERB'}, {'POS': 'ADJ'}, {'POS': 'NOUN'}],
            [{'POS': 'NOUN'}, {'POS': 'VERB'}, {'POS': 'ADV'}],
            [{'POS': 'NOUN'}, {'POS': 'ADP'}, {'POS': 'NOUN'}],
            [{'POS': 'NOUN'}, {'LOWER': '/'}, {'POS': 'NOUN'}],
            [{'POS': 'PROPN'}, {'LOWER': '/'}, {'POS': 'PROPN'}],
            # tri-grams with regex
            [{'POS': 'NOUN'}, {'TEXT': {'REGEX': 'at|in|to|on|of'}}, {'POS': 'NOUN'}],
            [{'TEXT': {'REGEX': 'at|in|to|on|of'}}, {'LOWER': 'the'}, {'POS': 'NOUN'}],
            # quadri-grams with regex
            [{'TEXT': {'REGEX': 'at|in|to|on|of'}}, {'LOWER': 'the'}, {'POS': 'ADJ'}, {'POS': 'NOUN'}],
            [{'POS': 'NOUN'}, {'TEXT': {'REGEX': 'at|in|to|on|of'}}, {'LOWER': 'the'}, {'POS': 'NOUN'}]
        ]
        with open('WORDS/ignore.json', 'r') as file:
            self._ignore = json.load(file)['ignore']
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
            print('\n\nCtrl+C detected\n')
        print('Setting cursor visible...')
        cursor.show()
        print('Exiting with code 0')
        exit(0)

    @staticmethod
    def _message(msg):
        print(f'[{datetime.now()}] {msg}')

    @staticmethod
    def _save_json(data, filename, indent=2, mode='w'):
        with open(filename, mode) as file:
            json.dump(data, file, indent=indent)

    @staticmethod
    def _is_num(token):
        try:
            int(token)
            float(token)
            return True
        except:
            return False

    def load_data(self, json_path='raw_BitcoinTalk-data.json'):
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
           and not self._is_num(token.lemma_) \
           and (len(token.text) > 1 and token.pos_ != 'SYM') \
           and (token.text not in self._ignore and token.lemma_ not in self._ignore):
           # and token.lemma_ in self._nlp.vocab: # If you only want words that are in the english NLP vocabulary
            return True
        return False

    def full_scan(self):
        if not self._data:
            raise Exception('self._data is None')
        self.boards = {key: {} for key in self._data.keys() if type(self._data[key]) == dict}
        self._message(f'Boards: {self.boards}\n')
        self.topicnames = {}
        self._matcher = Matcher(self._nlp.vocab)
        self._matcher.add('rules', self._rules)
        for boardname in self.boards.keys():
            print(f'------------------ {boardname} ------------------'.center(200))
            self.boards[boardname]['metadata'] = {'nb_of_words': 0, 'nb_of_documents': 0}
            self.topicnames[boardname] = [topicname for topicname in self._data[boardname].keys()]
            for topicname in self.topicnames[boardname][:400]: # add [:100] if you want this function to full_scan only the first 100 topics
                pages = self._data[boardname][topicname]['total_pages']
                self._message(f"|{boardname}|{topicname.center(100)} ({pages} page{'' if pages == 1 else 's'})")
                texts = [post['raw_content'].lower() for page in range(1, pages + 1) for post in self._data[boardname][topicname][str(page)]['posts']]
                self.boards[boardname][topicname] = {'words': {}, 'metadata': {'nb_of_words': 0, 'nb_of_documents': len(texts)}}
                self.boards[boardname]['metadata']['nb_of_documents'] += len(texts)
                for doc, post_id in zip(self._nlp.pipe(texts), range(0, len(texts))):
                    self._process_analysis(boardname, topicname, doc, post_id)
                self._compute_tfidf(boardname, topicname)
            print()
        self._save_json(self.boards, 'analysis_results.json')
        self._save_json(self.boards, 'raw_analysis_results.json', indent=None)

    def _process_analysis(self, boardname, topicname, doc, post_id):
        lemmatized_doc = self._nlp(' '.join([token.lemma_ for token in doc]).replace(' / ', '/'))
        matches = self._matcher(lemmatized_doc)
        ngrams = [lemmatized_doc[start:end].text for _, start, end in matches]
        nb_of_words = len(lemmatized_doc.text.split(' '))
        self.boards[boardname]['metadata']['nb_of_words'] += nb_of_words
        self.boards[boardname][topicname]['metadata']['nb_of_words'] = nb_of_words
        for ngram in ngrams:
            if ngram not in self.boards[boardname][topicname]['words']:
                self.boards[boardname][topicname]['words'][ngram] = {'occurrences': 1, 'in_docs': [post_id]}
            else:
                self.boards[boardname][topicname]['words'][ngram]['occurrences'] += 1
                if post_id not in self.boards[boardname][topicname]['words'][ngram]['in_docs']:
                    self.boards[boardname][topicname]['words'][ngram]['in_docs'].append(post_id)
        for token in lemmatized_doc:
            self.boards[boardname]['metadata']['nb_of_words'] += 1
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

    def temporal_scan(self, timestamp1, timestamp2, list_of_words=None, board_to_process='all'):
        posts_to_scan = []
        list_of_boards = [key for key in self._data.keys() if key != 'available_boards']
        boardnames = [board_to_process] if board_to_process in list_of_boards else list_of_boards
        for boardname in boardnames:
            for topicname in self._data[boardname].keys():
                pages = [self._data[boardname][topicname][str(page_nb)] for page_nb in range(1, self._data[boardname][topicname]['total_pages'] + 1)]
                for page in pages:
                    for post in page['posts']:
                        if timestamp1 <= post['last_edit'] <= timestamp2:
                            posts_to_scan.append({
                                'board': boardname,
                                'topic': topicname,
                                'post': post
                            })


if __name__ == '__main__':
    a = Analyzer()
    signal(SIGINT, a.exit)
    a.load_data()
    a.temporal_scan(1315539975.0, 1367165741.0)
    a.exit()