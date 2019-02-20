from . import eddb
import json
this_api = 'stations.jsonl'

class LandingPad:
    def __init__(self, size):
        self.size = size
        if self.size == 'None':
            self.size_num = 0
        elif self.size == 'M':
            self.size_num = 1
        elif self.size == 'L':
            self.size_num = 2
        else:
            raise ValueError

    def __gt__(self, other):
        return self.size_num > other.size_num

    def __eq__(self, other):
        return self.size_num == other.size_num

    def __lt__(self, other):
        return self.size_num < other.size_num


def station_loader(ids: list = [], names: list = [], landing_pad: str = 'None', distance_to_star: int = -1):
    eddb.recache(this_api)
    pad_filter = LandingPad(landing_pad)
    ret_list = []
    for station in eddb.read_iter(this_api):
        station = json.loads(station)
        if ids.__len__() > 0 and station.get("id", 0) not in ids:
            continue
        if names.__len__() > 0 and station.get("name", "") not in names:
            continue
        if pad_filter > LandingPad(station.get('max_landing_pad_size', 'None')):
            continue
        if distance_to_star > 0 and station.get('distance_to_star', 0) > distance_to_star:
            continue

        # all filters passed, appending station
        ap_station = Station(sid=station.get("id"), name=station.get("name"))
        ap_station._populate(station.get('system_id', 0), station.get('updated_at', 0),
                             station.get('max_landing_pad_size', 'None'), station.get('distance_to_star', -1),
                             station.get('allegiance', 'Penis'), station.get('type', 'Shnitzel'))
        ret_list.append(ap_station)

    return ret_list



class Station:
    def __init__(self, name=None, sid=None):
        if not name and not sid:
            raise IndexError('Specify station init')
        self.name = name
        self.sid = sid

    def _populate(self, system_id, updated_at, max_landing_pad_size, distance_to_star, allegiance, s_type):
        self.system_id = system_id
        self.updated_at = updated_at
        self.landing_pad = max_landing_pad_size
        self.distance = distance_to_star
        self.allegiance = allegiance
        self.type = s_type

    def populate(self):
        # TODO: implement one-time load from eddb and shit
        pass


