from eddb.trading import Trader
from edif import EliteInterface
from eddi import EDDI

t = Trader()

ed = EDDI()
ed.startup()

ei = EliteInterface({
    'carry_on': {
        'starting_point_system': None,
        'starting_point_station': None,
        'target_point_system': None,
        'target_point_station': None,
        'function': t.carry_on
    },
    'sell': {
        'function': t.sell,
        'starting_point': '',
        'commodity': '',
        'distance_limit': None,
        'choices': 1,
        'price_limit_index': None
    }
}, current_state=ed)

ei.run()
ed.shutdown()