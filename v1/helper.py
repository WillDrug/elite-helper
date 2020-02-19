from eddb.loader import EDDBLoader, APIS
from eddb.trading import Trader

el = EDDBLoader()
el.recache_all()

t = Trader()
station = t.source('Ariatia', 'Biowaste')