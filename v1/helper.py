from eddb.loader import EDDBLoader, APIS
from eddb.trading import Trader
from eddb.ORM import System, Session


s = Session()
system = s.query(System).filter(System.name == 'Ariatia').first()

close_by = s.query(System).filter(System.distance(system, 20, 0)).all()

print(close_by)