import sys
from . import eddb_prime
import json
from eddb.progress_tracker import generate_bar
this_api = 'stations.jsonl'


import logging
l = logging.getLogger('Station.py')
l.handlers = []
l.addHandler(logging.StreamHandler(stream=sys.stdout))
l.setLevel(logging.INFO)


class LandingPad:
    def __init__(self, size):
        self.size = size
        if self.size == 'None':
            self.size_num = 0
        elif self.size == 'M':
            self.size_num = 1
        elif self.size == 'L':
            self.size_num = 2
        elif size is None:
            self.size_num = -1
        elif size == '':  # unknown, presuming small only
            self.size_num = 0
        else:
            raise ValueError(size)

    def __gt__(self, other):
        return self.size_num > other.size_num

    def __eq__(self, other):
        return self.size_num == other.size_num

    def __lt__(self, other):
        return self.size_num < other.size_num


def station_loader(refs: list = [], landing_pad: str = 'None', distance_to_star: int = -1):
    # TODO: parallelize file usage with OFFSET and multiproc reading.
    l.info(f'Loding stations')
    eddb_prime.recache(this_api)
    pad_filter = LandingPad(landing_pad)
    ret_list = []
    reader = eddb_prime.read_iter(this_api)
    bar = generate_bar(reader.size, 'Filtering stations')
    bar.value = 0
    bar.start()
    for station in reader:
        bar.update(bar.value + station.encode('utf-8').__len__())
        station = json.loads(station)

        if refs.__len__() > 0:
            filtered = True
            for st, sy in refs:
                if st == station.get("name", "") and (sy == station.get("system_id", 0) or sy is None):
                    filtered = False

            if filtered:
                continue

        if pad_filter > LandingPad(station.get('max_landing_pad_size', 'None')):
            continue

        if station.get('distance_to_star', 0) is not None and 0 < distance_to_star < station.get('distance_to_star', 0):
            continue


        # all filters passed, appending station

        ap_station = Station(sid=station.get("id"), name=station.get("name"))
        ap_station._populate(station.get("id"), station.get("name"), station.get('system_id', 0), station.get('updated_at', 0),
                             station.get('max_landing_pad_size', 'None'), station.get('distance_to_star', -1),
                             station.get('allegiance', 'Penis'), station.get('type', 'Shnitzel'))

        ret_list.append(ap_station)

    bar.finish()

    return ret_list



class Station:
    def __init__(self, name=None, sid=None):
        if not name and not sid:
            raise IndexError('Specify station init')
        self.name = name
        self.sid = sid

    def _populate(self, id, name, system_id, updated_at, max_landing_pad_size, distance_to_star, allegiance, s_type):
        self.sid = id
        self.name = name
        self.system_id = system_id
        self.updated_at = updated_at
        self.landing_pad = max_landing_pad_size
        self.distance = distance_to_star
        self.allegiance = allegiance
        self.type = s_type

    def populate(self, system_id=None):
        reader = eddb_prime.read_iter(this_api, index=self.name)
        bar = generate_bar(reader.size, 'Filtering stations')
        bar.value = 0
        bar.start()
        for station in reader:
            bar.update(bar.value + station.encode('utf-8').__len__())
            station = json.loads(station)

            if self.name is not None and self.name != station.get('name'):
                continue
            if self.sid is not None and self.sid != station.get('id'):
                continue
            if system_id is not None and system_id != station.get('system_id'):
                continue

            # all filters passed, appending station

            self._populate(station.get('id'), station.get('name'), station.get('system_id', 0), station.get('updated_at', 0),
                                 station.get('max_landing_pad_size', 'None'), station.get('distance_to_star', -1),
                                 station.get('allegiance', 'Penis'), station.get('type', 'Shnitzel'))
            bar.finish()
            return True

        bar.finish()
        return False
