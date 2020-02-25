from eddb.trading import Trader
from eddi import EDDI
from pprint import pprint
t = Trader(ship_size='L', distance_from_star=800)

from eddb.loader import EDDBLoader

 # todo sell choice, rare limiter nomral, speech synthesis, check next-possible-jump when finding best
 # todo create web
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