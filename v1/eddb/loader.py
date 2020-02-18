import requests
from time import time
from . import dir_path, settings
from .logger import EliteLogger
from .ORM import *
from sqlalchemy.sql import exists
from progressbar import ProgressBar, UnknownLength
from .progress_tracker import generate_bar
import os, json
from enum import Enum
import pandas
import io
from sqlalchemy.exc import SQLAlchemyError


class APIS(Enum):
    COMMODITIES = 'commodities.json'
    SYSTEMS = 'systems.csv'
    STATIONS = 'stations.jsonl'
    LISTINGS = 'listings.csv'
    SYSTEMS_DELTA = 'systems_recently.csv'

    @classmethod
    def get_iterator(cls):
        return [q.value for q in cls]
    
    
class EDDBLoader:
    override = False

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
        if cached is None or cached.loaded >= int(time())+settings.get('cache_time', 86400):
            if cached is None:
                cached = Cache(name=api)
            res = self.load_api(api)
            if not res:
                return False
            else:
                self.l.debug(f'Loading succeeded for {api}: {res}')
                cached.loaded = int(time())
            if cached.loaded >= int(time())+settings.get('cache_time', 86400):
                res = self.update_db_for_api(api)
            else:
                self.l.info(f'{api} already loaded, skipping')
            if not res:
                return False
            else:
                self.l.debug(f'Updating DB succeeded for {api}: {res}')
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
        if api not in switch.keys():
            self.l.error(f'Key Error at updating DB for {api}')
            return False
        return switch[api]()

    def __blind_update(self, orm_obj, attr_dict):
        for key, value in attr_dict.items():
            setattr(orm_obj, key, value)
        return orm_obj

    def update_db_commodities(self):
        # todo move to read_json?
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
        return True

    def __upsert(self, d, oc, session=None):
        commit = False
        if session is None:
            session = Session()
            commit = True
        if session.query(exists().where(oc.id == d.get('id'))).scalar():
            orig = session.query(oc).filter(oc.id == d.get('id')).first()
            self.__blind_update(orig, d)
        else:
            session.add(oc(**d))
        if commit:
            session.commit()
            session.close()

    def __update_db_stations(self, stations):
        ext = [
            (['government_id', 'government'], Government),
            (['allegiance_id', 'allegiance'], Allegiance),
            (['settlement_security_id', 'settlement_security'], Security),
            (['type_id', 'type'], Type)
        ]
        drop = ['settlement_size_id', 'economies', 'states', 'prohibited_commodities', 'import_commodities',
                'export_commodities', 'selling_modules', 'selling_ships']

        commrate = settings.get('commit_rate', -1)
        if commrate < 0:
            commrate = None

        self.l.info('Running special cases')
        self.l.info('Extracting dictionary table updates')
        bar = generate_bar(stations.__len__(), 'Updating dictionaries')
        bar.start()
        for e in ext:
            self.__extract_df(stations, *e)
            bar.update(bar.value + 1)

        bar = generate_bar(stations.__len__(), 'Updating state info')
        bar.start()
        s = Session()
        for station in stations[['id', 'states']].to_dict(orient='records'):
            for state in station['states']:
                self.__upsert(state, State, s)
                s.add(StationState(station_id=station.get('id'), state_id=state.get('id')))
            if commrate is not None:
                if bar.value % commrate == 0:
                    s.commit()
            bar.update(bar.value + 1)
        bar.finish()
        s.commit()

        bar = generate_bar(stations.__len__(), 'Updating economy info')
        for station in stations[['id', 'economies']].to_dict(orient='records'):
            for economy in station['economies']:
                # checking id present in dict
                economy_id = s.query(Economy).filter(Economy.name == economy).first()
                if economy_id is None:
                    self.l.error(
                        f'Failed to fetch economy {economy} id. Respect the weird order of operations here, dammit')
                    continue  # skip alltogether
                else:
                    economy_id = economy_id.id
                s.add(StationEconomies(station_id=station.get('id'), economy_id=economy_id))
            if commrate is not None:
                if bar.value % commrate == 0:
                    s.commit()
            bar.update(bar.value + 1)
        bar.finish()
        s.commit()

        bar = generate_bar(stations.__len__(), 'Updating module info')  # FIXME OOM here, very taxing operation for some reason.; current commit rate ~8.1 GB taken; full commit - 16GB+; check double the commit rate
        for station in stations[['id', 'selling_modules']].to_dict(orient='records'):
            bar.update(bar.value + 1)
            for module in station['selling_modules']:
                s.add(StationModules(station_id=station.get('id'), module_id=module))
            if commrate is not None:
                if bar.value % commrate == 0:
                    s.commit()
        bar.finish()

        bar = generate_bar(stations.__len__(), 'Updating ship sale info')
        for station in stations[['id', 'selling_ships']].to_dict(orient='records'):
            bar.update(bar.value + 1)
            for ship in station['selling_ships']:
                s.add(StationShips(station_id=station.get('id'), name=ship))
            if commrate is not None:
                if bar.value % commrate == 0:
                    s.commit()

        bar = generate_bar(stations.__len__(), 'Updating commodity info')
        for station in stations[['id', 'prohibited_commodities', 'import_commodities', 'export_commodities']].to_dict(
                orient='records'):
            for key, usage in {'prohibited_commodities': -1, 'import_commodities': 0,
                               'export_commodities': 1}.items():  # todo move this outside into ORM or something
                for commodity in station[key]:
                    commodity_id = s.query(Commodity).filter(Commodity.name == commodity).first()
                    if commodity_id is None:
                        self.l.error(f'Failed to fetch commodity {commodity_id}, repsect the order of operations!!')
                        continue
                    else:
                        commodity_id = commodity_id.id

                    s.add(StationCommodities(station_id=station.get('id'), commodity_id=commodity_id, usage=usage))
            if commrate is not None:
                if bar.value % commrate == 0:
                    s.commit()
            bar.update(bar.value + 1)
        bar.finish()
        s.commit()
        s.close()

        self.l.info('Dropping columns')
        stations.drop(columns=drop, inplace=True)
        self.l.info('Recreating stations table')
        stations.to_sql(Station.__tablename__, engine, if_exists='append', index=False)
        return True

    def update_db_stations(self):
        self.l.info('Dropping Station, statioin2state, station2module, station2economy, station2commodity, stationships mapping')
        s = Session()
        s.query(Station).delete()
        s.query(StationState).delete()
        s.query(StationEconomies).delete()
        s.query(StationModules).delete()
        s.query(StationCommodities).delete()
        s.query(StationShips).delete()
        s.commit()
        s.close()
        self.l.info('Loading stations')
        chunksize = settings.get('chunksize', -1)
        if chunksize > 0:
            self.l.info(f'Reading file by {chunksize} chunks')
            for stations in self.read_json(APIS.STATIONS.value, lines=True, chunksize=chunksize):
                if not self.__update_db_stations(stations):
                    return False
            return True
        else:
            self.l.info('Gulping file')
            return self.__update_db_stations(self.read_json(APIS.STATIONS.value, lines=True))


    def __extract_df(self, df: pandas.DataFrame, group: list, orm_cls):
        """ much hardcode. very sad.
        :param df: original dataframe
        :param group: expecting a tuple\list of [id, name] of the extraction parameter
        :param orm_cls: ORM class to insert the extracted group into
        :return:
        """
        self.l.debug('Entering cleanup phase. Extracting group')
        grp = df.groupby(group).size().reset_index().drop(columns=[0]).rename(columns={group[0]: 'id', group[1]: 'name'})
        self.l.debug('Running session')
        s = Session()
        self.l.debug('Looping over records')
        for row in grp.to_dict(orient='records'):
            if s.query(exists().where(orm_cls.id == row.get('id'))).scalar():
                orig = s.query(orm_cls).filter(orm_cls.id == row.get('id')).first()
                self.__blind_update(orig, row)
            else:
                s.add(orm_cls(**row))
        self.l.debug('Committing changes')
        s.commit()
        # grp.to_sql(orm_cls.__tablename__, engine, if_exists='replace', index=False)
        self.l.debug('Dropping original frame columns')
        df.drop(columns=group[1], inplace=True)

    @property
    def __systems_extraction_data(self):
        return [  # first is an identifier, always
            (['government_id', 'government'], Government),
            (['allegiance_id', 'allegiance'], Allegiance),
            (['security_id', 'security'], Security),
            (['primary_economy_id', 'primary_economy'], Economy),
            (['power_state_id', 'power_state'], Powerstate),
            (['controlling_minor_faction_id', 'controlling_minor_faction'], Faction),
            (['reserve_type_id', 'reserve_type'], Reserve)
        ]

    def __update_db_systems(self, systems: pandas.DataFrame):
        # name containing quotes took care by pandas
        # strip away government, allegiance, security, economy, powerstate, faction, reserve

        self.l.info('Updating dict tables')
        bar = generate_bar(self.__systems_extraction_data.__len__(), 'Dict tables updates')
        bar.start()
        for e in self.__systems_extraction_data:
            self.__extract_df(systems, *e)
            bar.update(bar.value+1)
        bar.finish()

        # load into sql
        self.l.info('Loading systems into DB')
        systems.to_sql(System.__tablename__, engine, if_exists='append', index=False)
        return True

    def __update_db_systems_delta(self):
        self.l.info('Loading systems delta')
        systems = self.read_csv(f'systems_recently.csv')
        s = Session()
        for ext in self.__systems_extraction_data:
            self.__extract_df(systems, *ext)
        bar = generate_bar(systems.__len__(), 'Updating sytstems data')
        bar.start()
        for sys in systems.to_dict(orient='records'):
            self.__upsert(sys, System, s)
            bar.update(bar.value+1)
        bar.finish()
        s.commit()
        s.close()
        return True

    def update_db_systems(self):
        self.l.info('Checking systems special case')
        s = Session()
        chk = s.query(Cache).filter(Cache.name == APIS.SYSTEMS.value).first()
        s.close()
        if chk is not None and not self.override:
            self.l.info('Updating systems instead of loading')
            return self.__update_db_systems_delta()
        self.l.info('Doing full systems update. Dropping systems table')
        s = Session()
        s.query(System).delete()
        s.commit()
        s.close()

        self.l.info('Reading API file in chunks')
        # systems = pandas.read_csv(f'{dir_path}/data/{APIS.SYSTEMS.value}')
        chunk = settings.get('chunksize', -1)
        if chunk < 0:
            self.l.warning('Empty chunk size, gulping full file')
            return self.__update_db_systems(self.read_csv(APIS.SYSTEMS.value))

        self.l.debug(f'Chunk size set to {chunk}')

        system_reader = self.read_csv(APIS.SYSTEMS.value, chunksize=chunk)
        bar = generate_bar(self.__line_count(APIS.SYSTEMS.value), 'Loading API')
        bar.start()
        for system in system_reader:
            if not self.__update_db_systems(system):
                return False
            bar.update(bar.value+system.__len__())
        bar.finish()
        return True

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
        if api == APIS.SYSTEMS.value and not self.override:  # override makes everything clean
            self.l.info('Checking systems special case')
            s = Session()
            chk = s.query(Cache).filter(Cache.name == APIS.SYSTEMS.value).first()
            s.close()
            if chk is not None:
                self.l.warning('Changing systems to recently changed for loading')
                api = 'systems_recently.csv'
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
            self.l.error(f'Failed to delete {api}: File Not Found')
            return False
        return True

    def __line_count(self, api):
        return sum(1 for row in open(f'{dir_path}/data/{api}', 'r'))

    def __check_api(self, api):
        if api not in APIS.get_iterator():
            raise ModuleNotFoundError

    def read_json(self, api, lines=False, chunksize=None):
        if chunksize == -1:
            chunksize = None
        self.__check_api(api)
        return pandas.read_json(f'{dir_path}/data/{api}', lines=lines, chunksize=chunksize, orient='records')

    def read_csv(self, api, chunksize=None):
        self.__check_api(api)
        return pandas.read_csv(f'{dir_path}/data/{api}', chunksize=chunksize)

    def read_object(self, api):
        self.__check_api(api)
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