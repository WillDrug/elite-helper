from eddb.trading import Trader
from eddb.ORM import *
from eddi import EDDI
from pprint import pprint

from eddb.loader import EDDBLoader

 # todo speech synthesis
 # todo check next-possible-jump when finding best
 # todo create a proper interface ffs
el = EDDBLoader()
el.recache_all()

ed = EDDI()
ed.startup()

choices = 1

while True:
    a = input('> ')

    if a == 'exit':
        break

    elif a == 'distance':
        dst = int(input('distance> '))
        t = Trader(distance_from_star=dst)

    elif a == 'update':
        api = input('API> ')
        el.recache(api)

    elif a == 'carry':
        if ed.current_system is None:
            current_system = input('current_system> ')
        else:
            current_system = ed.current_system
        if ed.current_station is None:
            current_station = input('current_station> ')
        else:
            current_station = ed.current_station

        target_sys = input('target_sys> ')
        target_sta = input('target_sta> ')
        if target_sta == '':
            target_sta = None
        pprint(t.carry_on(current_system, current_station, target_sys, target_point_station=target_sta))

    elif a == 'sell':
        if ed.current_system is None:
            current_system = input('current_system> ')
        else:
            current_system = ed.current_system

        commodity = input('commodity> ')
        try:
            distance = int(input('dst> '))
        except ValueError:
            distance = None
        try:
            pli = float(input('pli> '))
        except ValueError:
            pli = None
        pprint(t.sell(current_system, commodity, distance_limit=distance, price_limit_index=pli, starting_station=ed.current_station, choices=choices))


    elif a == 'source':
        if ed.current_system is None:
            current_system = input('current_system> ')
        else:
            current_system = ed.current_system

        commodity = input('commodity> ')
        try:
            distance = int(input('dst> '))
        except ValueError:
            distance = None
        try:
            pli = float(input('pli> '))
        except ValueError:
            pli = None

        pprint(t.source(current_system, commodity, price_limit_index=pli, distance_limit=distance, choices=choices))
    elif a == 'best':
        if ed.current_system is None:
            current_system = input('current_system> ')
        else:
            current_system = ed.current_system
        if ed.current_station is None:
            current_station = input('current_station> ')
        else:
            current_station = ed.current_station
        try:
            distance = int(input('dst> '))
        except ValueError:
            distance = None
        try:
            pli = float(input('pli> '))
        except ValueError:
            pli = None
        pprint(t.find_best(current_system, current_station, distance_limit=distance, price_index_limit=pli, choices=choices))

    elif a == 'rare_limit':
        t.switch_rare()
        print(f'Rare limit is {t.rare_limit}')

    elif a == 'lock':
        target_system = input('target system> ')
        if target_system == '':
            target_system = None
        t.set_lock_system(target_system)

    elif a == 'next_rare':
        if ed.current_system is None:
            current_system = input('current system> ')
        else:
            current_system = ed.current_system

        t.next_rare(current_system)
        pprint(t.closest_rare(current_system))

    elif a == 'choice':
        try:
            choices = int(input('choice num> '))
        except ValueError:
            choices = 1

    elif a == 'limit_planets':
        t.limit_planetary = not t.limit_planetary
        pprint(f'Limiting planetary: {t.limit_planetary}')
    elif a == 'get_types':
        pprint(Type.get_types())
    elif a == 'limit_types':
        l = input('types> ')
        l = l.strip().split(',')
        l = [q.strip() for q in l]
        if all([Type.check_type(q) for q in l]):
            t.limit_types = l
        else:
            print('Failed')

    elif a == 'limit_sell_count':
        t.limit_sell_count = not t.limit_sell_count
        pprint(f'Limiting magic; {t.limit_sell_count}')