from signal import signal, SIGINT
import matplotlib.pyplot as plt
import numpy as np
import cursor
import spacy
import json
import sys
import os


class Analyzer:
    def __init__(self, model='en_core_web_sm'):
        cursor.hide()
        try:
            self._npl = spacy.load(model)
        except Exception:
            try:
                os.system(f'python -m spacy download {model}')
                self._npl = spacy.load(model)
            except Exception:
                raise Exception('Spacy error: try to install requirements.txt\nSee https://github.com/BobyCow/BitcoinTalk for more instructions')
        print()

    @staticmethod
    def _is_token_valid(token):
        if not token.is_punct and not token.is_stop and not token.pos_ == 'SPACE':
            return True
        return False

    def scan(self, json_path='BitcoinTalk-data.json'):
        print(f'Loading data from {json_path}...')
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        self.boards = [{key: []} for key in data.keys() if type(data[key]) == dict]
        self._words = {}
        print(f'Boards: {self.boards}')
        self.topicnames = {}
        for b in self.boards:
            boardname = next(iter(b))
            print(f'------------------ {boardname} ------------------'.center(200))
            self._words[boardname] = {}
            self.topicnames[boardname] = [topicname for topicname in data[boardname].keys()]
            for topicname in self.topicnames[boardname][:20]:
                print(f'Processing {boardname} // {topicname}...')
                self._words[boardname][topicname] = {}
                pages = data[boardname][topicname]['total_pages']
                for page in range(1, pages + 1):
                    page_info = f'{page}/{pages}'
                    print(page_info, end='', flush=True)
                    for post in data[boardname][topicname][str(page)]['posts']:
                        text = post['raw_content'].lower()
                        doc = self._npl(text)
                        for token in doc:
                            if self._is_token_valid(token):
                                if token.lemma_ not in self._words[boardname][topicname]:
                                    self._words[boardname][topicname][token.lemma_] = 1
                                else:
                                    self._words[boardname][topicname][token.lemma_] += 1
                        print('\b' * len(page_info), end='', flush=True)
                self._words[boardname][topicname] = sorted(self._words[boardname][topicname].items(), key=lambda x: x[1], reverse=True)
        with open('results.json', 'w') as file:
            json.dump(self._words, file, indent=2)

    def show_histogram(self, board, topic):
        nb_to_show = 25
        word = []
        frequency = []
        for i in range(len(self._words[board][topic])):
            word.append(self._words[board][topic][i][0])
            frequency.append(self._words[board][topic][i][1])
        indices = np.arange(len(self._words[board][topic]))
        plt.title(f'{board} / {topic}')
        plt.grid(zorder=0)
        plt.xlabel('words')
        plt.ylabel('occurrences')
        plt.bar(indices[:nb_to_show], frequency[:nb_to_show], color='orange', zorder=3)
        plt.xticks(indices[:nb_to_show], word[:nb_to_show], rotation='vertical')
        plt.tight_layout()
        plt.show()

    def exit(self, sig=None, frame=None):
        if sig:
            print('\n\nCtrl+C detected')
        cursor.show()
        exit(0)


if __name__ == '__main__':
    try:
        a = Analyzer()
        signal(SIGINT, a.exit)
        a.scan()
        print('\n\n')
        for board in a.boards:
            boardname = next(iter(board))
            for topic in a.topicnames[boardname][:5]:
                print(f'Histogram of: {boardname} / {topic}')
                a.show_histogram(boardname, topic)
        a.exit()
    except Exception as e:
        print(f'\nIn: {e.__traceback__.tb_frame.f_code.co_filename}\nType: {type(e).__name__}', file=sys.stderr)
        print(e, file=sys.stderr)
        exit(-1)