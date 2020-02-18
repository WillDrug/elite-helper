from eddb.loader import EDDBLoader, APIS
from eddb.trading import Trader

el = EDDBLoader()
el.recache_all()

t = Trader()
print(t.source('Ariatia', 'Biowaste'))