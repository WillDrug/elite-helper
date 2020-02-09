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

eddb_prime.recache_all()
# eddb_prime.index_all()
# exit()
if __name__ == '__main__':

    cur_sys = ''
    cur_sta = ''
    for update in di.update_generator():
        update = update.strip().split(';')
        print(f'Beep! {update}')
        if update[0] == 'mission':
            target_sys = System(name=update[1])
            target_sys.populate()
            target_sta = Station(name=update[2])
            target_sta.populate(target_sys.id)

            if cur_sta is not None:
                list_target = StationPriceList(target_sta)
                list_current = StationPriceList(cur_sta)
                print(list_target-list_current)
            else:
                print('How are you not docked?')

        elif update[0] == 'docked':
            cur_sys = System(name=update[1])
            cur_sys.populate()
            cur_sta = Station(name=update[2])
            cur_sta.populate(cur_sys.id)

        elif update[0] == 'exit':
            di.shutdown()

    pickle.dump(cache, open('cache.pcl', 'wb+'))