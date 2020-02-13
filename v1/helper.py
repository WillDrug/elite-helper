from eddb.loader import EDDBLoader, APIS, Trader
el = EDDBLoader()
el.recache_all()

from eddi import EDDI()
eddi.startup()

t = Trader()

# run input loop here.