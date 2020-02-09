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

# hackjob
cur_sys = System(sys.argv[1])
cur_sys.populate()
cur_sta = Station(sys.argv[2])
cur_sta.populate(system_id=cur_sys.id)
trg_sys = System(sys.argv[3])
trg_sys.populate()
trg_sta = Station(sys.argv[4])
trg_sta.populate(system_id=trg_sys.id)


print(StationPriceList(trg_sta)-StationPriceList(cur_sta))
