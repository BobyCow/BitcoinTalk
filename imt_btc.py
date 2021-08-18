from optparse import OptionParser

def all_process(opt, value):
    from DownloadHTML.DownloadHTML import start_process
    from TextAnalysis.TextAnalysis import Analyzer
    from Scraper.Scraper import BitcoinTalkScraper
    # Download html
    start_process()
    # Scraping
    bts = BitcoinTalkScraper()
    bts.extract_data()
    bts.save_data()
    # Text mining
    a = Analyzer()
    a.load_data()
    a.full_scan()
    exit(0)

def download(value):
    from DownloadHTML.DownloadHTML import start_process
    if value == ['update']:
        print('update')
        start_process('update')
    else:
        print('standard')
        start_process('standard')

def scraper(value):
    from Scraper.Scraper import BitcoinTalkScraper
    bts = BitcoinTalkScraper()
    bts.extract_data()
    bts.save_data()

def analysis(value):
    from TextAnalysis.TextAnalysis import Analyzer
    a = Analyzer()
    a.load_data()
    a.full_scan()

def data_viz(value):
    from Visualizer.DataVisualizer import DataViz
    # d = DataViz()
    # d.load_data(json_path='raw_BitcoinTalk-data.json')

def switcher(opts, parser):
    switch = {
        'all': all_process,
        'download_mode': download,
        'scrape': scraper,
        'full-analysis': analysis,
        'temporal-analysis': analysis,
        'visualization': data_viz
    }
    if opts.all and (opts.download or opts.scrape or opts.text_analysis):
        parser.error('Options --all and [-d|-s|-t] are mutually exclusive')
        exit(-1)
    for opt, value in opts.__dict__.items():
        if value:
            switch.get(opt, lambda x: print(f"'{opt} {x}' is not a valid option"))(value)


def parse_arguments():
    parser = OptionParser()
    parser.add_option("--download standard", action="store_const",
                    dest="dowload_mode", const="standard")
    parser.add_option("--download update", action="store_const",
                    dest="dowload_mode", const="update")
    parser.set_defaults(dowload_mode="standard")
    # parser.add_option('-a', '--all', help='run all process: download html, scraping, and text analysis', action='store_true')
    # parser.add_option('--download', help='download html pages of BitcoinTalk (https://bitcointalk.org/index.php?board=14.0)\ndownload_modes: standard | update', action='append', dest='update', default=[])
    # parser.add_option('-s', '--scrape', help='scrape downloaded html pages of BitcoinTalk. Do not use this option if you didn\'t download html pages before', action='store_true')
    # parser.add_option('--full-analysis', help='perform full analysis on textual data, extracted via scraping')
    # parser.add_option('-t', '--temporal-analysis', nargs=3, help='perform temporal analysis on textual data, extracted via scraping')
    # parser.add_option('-v', '--visualization', help='data visualization', action='store_true')
    opts, _ = parser.parse_args()
    print(f'Options: {opts}')
    switcher(opts, parser)

if __name__ == '__main__':
    parse_arguments()