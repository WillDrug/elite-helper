from eddb.loader import EDDBLoader, APIS
from eddb.trading import Trader
el = EDDBLoader()
# el.recache_all()
el.update_all()
exit()

from eddi import EDDI
eddi = EDDI()
eddi.startup()

t = Trader()

print(t.carry_on('Ariatia', 'Gooch Ring', 'Harm', 'Gentil Hub'))
exit()

# run input loop here.
# todo move to interface
while True:
    command = input('> ')
    if command == 'sell':
        system = input('system>')
        station = input('station>')
        t.carry_on(eddi.current_system, eddi.current_station, system, station)
    if command == 'exit':
        break

eddi.shutdown()