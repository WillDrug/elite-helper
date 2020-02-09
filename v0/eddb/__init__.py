import progressbar as pb
# todo: cache this
import sys, os, json
from glob import glob
from time import time
import pickle
import requests
import logging
from eddb.progress_tracker import generate_bar

class Cleaner:
    @classmethod
    def clean_system(cls, row, first=False):
        if first:
            cls.header = row
            return None, None
        header = cls.header.split(',')
        row = row.split(',')
        struct = {}
        for a, b in zip(header, row):
            struct[a.strip()] = b.strip()
        if struct['name'][0] == '"':
            struct['name'] = struct['name'][1:-1]
        ix1 = struct['name'][0] if struct['name'][0] != '*' else 'ast'
        if struct['name'].__len__() > 1:
            ix2 = struct['name'][1] if struct['name'][1] != '*' else 'ast'
        else:
            ix2 = ''
        idx = f'{ix1}{ix2}'

        return json.dumps(struct), idx


    @classmethod
    def clean_station(cls, row, first=False):
        if first:
            cls.header = None
        dt = json.loads(row.strip())
        idx = dt['name'][0] if dt['name'][0] != '?' else '__q'
        return row.strip(), idx

class EDDB:
    api_names = ['commodities.json', 'stations.jsonl', 'listings.csv', 'systems.csv']

    api_clean = {
        'stations.jsonl': Cleaner.clean_station,
        'systems.csv': Cleaner.clean_system
    }

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
        self.logger.info(f'Loading {api}')
        bar = pb.ProgressBar(max_value=pb.UnknownLength)
        bar.start()
        with open(f'{self.dir_path}/data/{api}', 'w+', encoding='utf-8') as handle:  # todo, fix paths
            for block in response.iter_content(1024):
                handle.write(block.decode('utf-8'))
                bar.update(bar.value + 1)
        bar.finish()
        # keeping original APIs for not yet changed system_loader methods
        # if self.index_api(api):
        #     os.remove(f'{self.dir_path}/data/{api}')
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

    def index_all(self):
        for api in self.api_names:
            self.index_api(api)

    def index_api(self, api):
        idx_files = {}
        def getfile(idx):
            if idx not in idx_files.keys():
                idx_files[idx] = open(f'{self.dir_path}/data/{api}_{idx}', 'a')
            return idx_files[idx]

        files = glob(f'{self.dir_path}/data/{api}_*')
        for f in files:
            os.remove(f)
        if api not in self.api_clean.keys():
            return False

        f = self.api_clean[api]
        reader = self.read_iter(api)
        trow, tidx = f(reader.__next__(), first=True)  # fixme this is horrible, this checks for a header OR inserts first row
        if trow is not None:
            getfile(tidx).write(trow.strip())
            getfile(tidx).write('\n')

        bar = generate_bar(reader.size, f'Indexing {api}')
        bar.value = 0
        bar.start()

        cln = self.api_clean[api]

        for r in reader:
            crow, idx = cln(r)
            getfile(idx).write(crow)
            getfile(idx).write('\n')
            bar.update(bar.value + r.encode('utf-8').__len__())
        bar.finish()
        self.logger.info('Closing files')
        for k in idx_files:
            idx_files[k].close()
        return True



    def save_config(self):
        pickle.dump(self.config, open(f'{self.dir_path}/data/config.pcl', 'wb+'))  # todo; fix paths

    def read_object(self, api, index=None):
        if api not in self.api_names:
            raise ModuleNotFoundError
        if index is not None:
            f = open(f'{self.dir_path}/data/{api}_{index}', 'r', encoding='utf-8')
        else:
            f = open(f'{self.dir_path}/data/{api}', 'r', encoding='utf-8')
        return f

    def read(self, api):
        return self.read_object(api).read()

    def read_iter(self, api, index=None):
        if index is not None:
            filename = f'{self.dir_path}/data/{api}_{index}'
            return FileReader(open(filename, 'r', encoding='utf-8'), os.path.getsize(filename))
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

    def close(self):
        self.f.close()

eddb_prime = EDDB()
