import progressbar as pb
# todo: cache this
import sys
from time import time
import pickle
import requests
import logging
import os

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

    def load_data(self, api):
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
            return True
        else:
            return False

    def recache_all(self):
        for api in self.api_names:
            self.recache(api)

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

    def read_iter(self, api):
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