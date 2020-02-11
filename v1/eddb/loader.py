import requests
from time import time
from . import dir_path, settings
from .logger import EliteLogger
from .ORM import Cache, Session, Commodity, Category, Listing, engine
from progressbar import ProgressBar, UnknownLength
from .progress_tracker import generate_bar
import os, json
from enum import Enum
import pandas
from functools import wraps



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

    def update_db_commodities(self): # no need to improve, small file
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


    def update_db_listings(self):
        self.l.info('Reading API with pandas magic')
        df = self.read_csv(APIS.LISTINGS.value)
        self.l.info('Dropping and reinserting Listings')
        df.to_sql(Listing.__tablename__, engine, if_exists='replace', index=False)
        self.l.info('Listings done.')

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

    def __check_api(self, api):
        if api not in APIS.get_iterator():
            raise ModuleNotFoundError

    def read_csv(self, api):
        self.__check_api()
        return pandas.read_csv(f'{dir_path}/data/{api}')

    def read_object(self, api):
        self.__check_api()
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