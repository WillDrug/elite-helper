import requests
from time import time, sleep
from . import dir_path, settings
from .logger import EliteLogger
from .ORM import Cache, Session, Commodity, Category, Listing
from progressbar import ProgressBar, UnknownLength
from .progress_tracker import generate_bar
import os, json, sys
from enum import Enum
from multiprocessing import Queue, Process
from queue import Empty

class APIS(Enum):
    COMMODITIES = 'commodities.json'
    STATIONS = 'stations.jsonl'
    LISTINGS = 'listings.csv'
    SYSTEMS = 'systems.csv'

    @classmethod
    def get_iterator(cls):
        return [q.value for q in cls]
    
    
class EDDBLoader:
    def __init__(self):
        self.l = EliteLogger('EDDBLoader', level=settings.get('log_level'))

    def recache_all(self):
        for api in APIS.get_iterator():
            if self.recache(api):
                self.l.info(f'Loaded {api}')
            else:
                self.l.error(f'Failed to load {api}')

    def recache(self, api):
        """
        Checks cache time for api and loads it if necessary
        :param api: EDDB API present in APIS.get_iterator()
        :return: True\False
        """
        self.l.info(f'Checking cache state of {api}')
        session = Session()
        cached = session.query(Cache).filter(Cache.name == api).first()
        if cached is None or cached.cached >= int(time())+settings.get('cache_time', 86400):
            res = self.load_api(api)
            self.l.debug(f'Loading succeeded for {api}: {res}')
            if not res:
                return False
            res = self.update_db_for_api(api)
            self.l.debug(f'Updating DB succeeded for {api}: {res}')
            if not res:
                return False
            # if all passed, update cache time
            if cached is None:
                cached = Cache(name=api, cached=int(time()))
                session.add(cached)
            else:
                cached.cached = int(time())
            session.commit()
        else:
            self.l.info(f'Cache passed for {api}')
            return True



    def update_db_for_api(self, api):
        self.l.info(f'Updating {api} database entries')
        self.l.debug('Routing reader iterator into specific function')  # fixme: decide where those methods should be already
        switch = {
            APIS.COMMODITIES.value: self.update_db_commodities,
            APIS.SYSTEMS.value: self.update_db_systems,
            APIS.STATIONS.value: self.update_db_stations,
            APIS.LISTINGS.value: self.update_db_listings
        }
        try:
            return switch[api]()
        except KeyError:
            return False

    def __blind_update(self, orm_obj, attr_dict):
        for key, value in attr_dict.items():
            setattr(orm_obj, key, value)
        return orm_obj

    def update_db_commodities(self):
        reader = self.read_object(APIS.COMMODITIES.value)
        commodities = reader.read()
        reader.close()
        try:
            commodities = json.loads(commodities)
        except json.JSONDecodeError:
            self.l.error('Failed to load commodities file. JSON error')
            return False

        bar = generate_bar(commodities.__len__(), 'Updating commodity tables')
        bar.start()
        session = Session()
        for cm in commodities:
            cat = cm.get('category')
            if cat is not None:
                c = session.query(Category).filter(Category.id == cat.get('id')).first()
                if c is None:
                    c = Category(**cat)
                    session.add(c)
                else:
                    c = self.__blind_update(c, cat)
                del cm['category']
            c = session.query(Commodity).filter(Commodity.id == cm.get('id')).first()
            if c is None:
                c = Commodity(**cm)
                session.add(c)
            else:
                c = self.__blind_update(c, cm)
            bar.update(bar.value + 1)
        bar.finish()
        session.commit()  # fixme except ORM error
        return True

    def __update_db_listings(self, proc_num, queue):
        self.l.info(f'Worker {proc_num} starting')
        commrate = settings.get('commit_rate', 500)
        session = Session()
        bulk = []
        bar = generate_bar(UnknownLength, f'Worker {proc_num} progress', redirect_stdout=True)
        bar.start()
        while True:
            try:
                sleep(0.1)
                ddata = queue.get(proc_num, 1)
                if bulk.__len__() >= commrate or ddata == 'STOP':
                    self.l.debug(f'Commiting bulk of size {bulk.__len__()}')
                    session.bulk_save_objects(bulk)
                    bulk = []
                    session.commit()

                if ddata == 'STOP':
                    self.l.info(f'Worker {proc_num} SIGTERM')
                    session.close()
                    queue.put('STOP')
                    break

                l = session.query(Listing).filter(Listing.id == ddata.get('id')).first()
                if l is None:
                    l = Listing(**ddata)
                    bulk.append(l)
                else:
                    self.__blind_update(l, ddata)
                # move up before update
                bar.update(bar.value + 1)

            except Empty:
                pass
        bar.finish()
        self.l.info(f'Worker {proc_num} finished')

    def update_db_listings(self):
        queue = Queue()
        consumers = [
            Process(target=self.__update_db_listings, args=(i, queue,))
            for i in range(settings.get('procnum', 8))
        ]
        self.l.info(f"Starting {settings.get('procnum', 8)} subprocesses")
        for consumer in consumers:
            consumer.start()
        reader = self.read_iter(APIS.LISTINGS.value)
        header = reader.__next__()
        header = header.strip().split(',')
        bar = generate_bar(reader.size, 'Loading listing update jobs')
        for line in reader:
            sz = line.encode('utf-8').__len__()
            line = line.strip().split(',')
            queue.put({a: int(b) for a, b in zip(header, line)})
            bar.update(bar.value + sz)
        queue.put('STOP')
        bar.finish()
        self.l.info("Waiting for workers to finish")
        for consumer in consumers:
            consumer.join()
        queue.close()

    def update_db_systems(self):
        reader = self.read_iter(APIS.SYSTEMS.value)

    def update_db_stations(self):
        reader = self.read_iter(APIS.STATIONS.value)

    def update_all(self):
        for api in APIS.get_iterator():
            if self.update_db_for_api(api):
                self.l.info(f'Updated {api}')
            else:
                self.l.error(f'Failed to update {api}')

    def load_all(self):
        for api in APIS.get_iterator():
            if self.load_api(api):
                self.l.info(f'Loaded {api}')
            else:
                self.l.error(f'Failed to load {api}')

    def load_api(self, api):
        """
        This method just loads the file into the filesystem, nothing else
        :param api: eddb API present in APIS.get_iterator() list
        :return: True\False success
        """
        self.l.info(f'Loading {api}')
        response = requests.get(f'https://eddb.io/archive/v6/{api}', stream=True)

        self.l.debug(f'{api} status code is {response.status_code}')
        if response.status_code != 200:
            return False
        self.l.info(f'Loading {api}')
        bar = ProgressBar(max_value=UnknownLength)
        bar.start()
        with open(f'{dir_path}/data/{api}', 'w+', encoding='utf-8') as handle:  # todo, fix paths
            for block in response.iter_content(1024):
                handle.write(block.decode('utf-8'))
                bar.update(bar.value + 1)
        bar.finish()
        return True

    def remove_api(self, api):
        """
        This one just deleted API from the filesystem
        :param api: EDDB API present in APIS.get_iterator()
        :return: True\False
        """
        try:
            os.remove(f'{dir_path}/{api}')
        except FileNotFoundError:
            return False
        return True

    def read_object(self, api):
        if api not in APIS.get_iterator():
            raise ModuleNotFoundError
        return open(f'{dir_path}/data/{api}', 'r', encoding='utf-8')

    def read_iter(self, api):
        return FileReader(self.read_object(api), os.path.getsize(f'{dir_path}/data/{api}'))

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