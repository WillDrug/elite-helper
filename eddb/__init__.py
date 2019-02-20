# todo: cache this
from time import time
import pickle
import requests
import logging

class EDDB:
    api_names = ['commodities.json', 'stations.jsonl', 'listings.csv']

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

    def __init__(self):
        self.logger = logging.getLogger('EDDB_Base')
        self.logger.setLevel(logging.INFO)
        try:
            self.config = pickle.load(open('eddb/data/config.pcl', 'rb+'), encoding='utf-8')
        except FileNotFoundError:
            self.config = {}
            self.cset('timeout', 36800)
            self.config['cached'] = {}
            for api in self.api_names:
                self.ccset(api, 0)
            self.prime()
            self.save_config()

    def load_data(self, api):
        response = requests.get(f'https://eddb.io/archive/v6/{api}', stream=True)

        # Throw an error for bad status codes
        self.logger.debug(f'{api} status code is {response.status_code}')
        if response.status_code != 200:
            return False

        with open(f'eddb/data/{api}', 'w+', encoding='utf-8') as handle:  # todo, fix paths
            for block in response.iter_content(1024):
                handle.write(block.decode('utf-8'))
        self.ccset(api, time())
        return True

    def prime(self):
        self.logger.info('Priming files')
        for api in self.api_names:
            self.logger.debug(f'Priming {api}')
            self.load_data(api)
        self.save_config()

    def recache(self, api):
        if time() - self.ccget(api) > float(self.cget('timeout')):
            self.logger.info(f'Recaching {api}')
            self.load_data(api)
            self.save_config()

    def recache_all(self):
        for api in self.api_names:
            self.recache(api)


    def save_config(self):
        pickle.dump(self.config, open('eddb/data/config.pcl', 'wb+'))  # todo; fix paths

    def read(self, api):
        if api not in self.api_names:
            raise ModuleNotFoundError
        f = open(f'eddb/data/{api}', 'r', encoding='utf-8')
        return f.read()

    def read_iter(self, api):
        if api not in self.api_names:
            raise ModuleNotFoundError
        f = open(f'eddb/data/{api}', 'r', encoding='utf-8')
        return FileReader(f)

class FileReader:
    def __init__(self, f):
        self.f = f

    def __iter__(self):
        return self

    def __next__(self):
        l = self.f.readline()
        if not l:
            self.f.close()
            raise StopIteration
        return l

eddb = EDDB()