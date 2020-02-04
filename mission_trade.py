import pickle

import logging, sys

l = logging.getLogger('Helper')
l.handlers = []
l.addHandler(logging.StreamHandler(stream=sys.stdout))
l.setLevel(logging.DEBUG)

from eddi import EDDI
di = EDDI()

from eddb import eddb_prime
from eddb.station import Station
from eddb.system import System
from eddb.pricelist import StationPriceList

eddb_prime.recache_all(index=True)
eddb_prime.force_index()

try:
    cache = pickle.load(open('cache.pcl', 'rb+'))
except FileNotFoundError:
    cache = {}

if __name__ == '__main__':

    cur_sys = ''
    cur_sta = ''
    for update in di.update_generator():
        update = update.strip().split(';')
        if update[0] == 'mission':
            if update[1] not in cache.keys():
                target_sys = System(name=update[1])
                target_sys.populate()
                cache[update[1]] = {}
                cache[update[1]]['sys'] = target_sys
            if update[2] not in cache.keys():
                target_sta = Station(name=update[2])
                target_sta.populate(target_sys.id)
                cache[update[1]][update[2]] = target_sta

            target_sys = cache[update[1]]
            target_sta = cache[update[1]][update[2]]

            list_target = StationPriceList(target_sta)
            list_current = StationPriceList(cur_sta)

            print(list_target-list_current)

        elif update[0] == 'docked':
            if update[1] not in cache.keys():
                cur_sys = System(name=update[1])
                cur_sys.populate()
                cache[update[1]] = {}
                cache[update[1]]['sys'] = cur_sys
            if update[2] not in cache[update[1]].keys():
                cur_sta = Station(name=update[2])
                cur_sta.populate(cur_sys.id)
                cache[update[1]][update[2]] = cur_sta

            cur_sys = cache[update[1]]['sys']
            cur_sta = cache[update[1]][update[2]]
        elif update[0] == 'exit':
            di.shutdown()

    # pickle.dump(cache, open('cache.pcl', 'wb+'))