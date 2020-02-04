import progressbar as pb
# todo: cache this
import sys
from time import time
import pickle
import requests
import logging
import os
from eddb.progress_tracker import generate_bar

class EDDB:
    api_names = ['commodities.json', 'stations.jsonl', 'listings.csv', 'systems.csv']

    def cset(self, k, v):
        self.config[k] = v

    def cget(self, k):
        return self.config.get(k, None)

    def ccget(self, k):
        if 'cached' not in self.config.keys():
            self.config['cached'] = {}
        return self.config['cached'].get(k, 0)

    def ccset(self, k, v):
        if 'cached' not in self.config.keys():
            self.config['cached'] = {}
        self.config['cached'][k] = v

    def is_indexed(self, api):
        if 'indexed' in self.config.keys():
            return api in self.config['indexed']
        else:
            return False

    def indexed(self, api):
        if 'indexed' not in self.config.keys():
            self.config['indexed'] = []
        self.config['indexed'].append(api)

    def __init__(self):
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.logger = logging.getLogger('EDDB_Base')
        self.logger.handlers = []
        self.logger.addHandler(logging.StreamHandler(stream=sys.stdout))
        self.logger.setLevel(logging.INFO)
        try:
            self.config = pickle.load(open(f'{self.dir_path}/data/config.pcl', 'rb+'), encoding='utf-8')
        except FileNotFoundError:
            self.config = {}
            self.cset('timeout', 36800)
            self.config['cached'] = {}
            for api in self.api_names:
                self.ccset(api, 0)
            self.prime()
            self.save_config()

    def load_data(self, api, index=False):
        response = requests.get(f'https://eddb.io/archive/v6/{api}', stream=True)

        # Throw an error for bad status codes
        self.logger.debug(f'{api} status code is {response.status_code}')
        if response.status_code != 200:
            return False
        bar = pb.ProgressBar(max_value=pb.UnknownLength)
        bar.start()
        with open(f'{self.dir_path}/data/{api}', 'w+', encoding='utf-8') as handle:  # todo, fix paths
            for block in response.iter_content(1024):
                handle.write(block.decode('utf-8'))
                bar.update(bar.value + 1)
        bar.finish()
        self.ccset(api, time())
        if index:
            return self.index_api(api)
        return True

    def index_api(self, api):
        self.logger.info(f'Indexing {api}')
        gen = self.read_iter(api)
        header = gen.__next__()
        header = header.split(',')
        bar = generate_bar(gen.size, f'Indexing {api}')
        bar.value = 0

        ref_idx = ''
        f = None

        bar.start()
        for l in gen:
            if ref_idx != l[0]:
                if f is not None:
                    f.close()
                ref_idx = l[0]
                f = open(f'{self.dir_path}/data/{api}_{l[0]}', 'w')
                f.write(','.join(header))
            f.write(l)
            bar.update(bar.value + l.encode('utf-8').__len__())

        bar.finish()
        self.indexed(api)

    def force_index(self):
        for a in self.api_names:
            if not self.is_indexed(a):
                self.index_api(a)
        return


    def prime(self):
        self.logger.info('Priming files')
        for api in self.api_names:
            self.logger.debug(f'Priming {api}')
            self.load_data(api)
        self.save_config()

    def recache(self, api, index=False):
        if time() - self.ccget(api) > float(self.cget('timeout')):
            self.logger.info(f'Recaching {api}')
            self.load_data(api, index=index)
            self.save_config()
            return True
        else:
            return False

    def recache_all(self, index=False):
        for api in self.api_names:
            self.recache(api, index=index)

    def clean(self, api):
        os.remove(f'{self.dir_path}/data/{api}')

    def save_config(self):
        pickle.dump(self.config, open(f'{self.dir_path}/data/config.pcl', 'wb+'))  # todo; fix paths

    def read_object(self, api):
        if api not in self.api_names:
            raise ModuleNotFoundError
        f = open(f'{self.dir_path}/data/{api}', 'r', encoding='utf-8')
        return f

    def read(self, api):
        return self.read_object(api).read()

    def read_iter(self, api, index=None):
        if index is not None and self.is_indexed(api):
            return FileReader(self.read_object(api), os.path.getsize(f'{self.dir_path}/data/{api}_{index[0]}'))
        else:
            return FileReader(self.read_object(api), os.path.getsize(f'{self.dir_path}/data/{api}'))

class FileReader:
    def __init__(self, f, size):
        self.f = f
        self.size = size

    def __iter__(self):
        return self

    def __next__(self):
        l = self.f.readline()
        if not l:
            self.f.close()
            raise StopIteration
        return l

eddb_prime = EDDB()
