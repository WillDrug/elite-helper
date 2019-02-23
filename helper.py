import sys
from rares import RareLoader, RareGraph
from bot import EliteBot
from config import telegram_token
import logging

l = logging.getLogger('Helper')
l.handlers = []
l.addHandler(logging.StreamHandler(stream=sys.stdout))
l.setLevel(logging.DEBUG)

rares = RareLoader()

bot = EliteBot(telegram_token, rares)
bot.run()
rares.init(bot.cget('ship_size'), bot.cget('max_distance_from_star'))
from eddi import EDDI
di = EDDI()



for update in di.update_generator():
    update = update.split(';')
    # switch event
    if update[0] == 'docked':
        system = update[1]
        station = update[2]
        if bot.trading:  # todo: switch to State() class, use both with bot and helper.py; push references into helpers
            messages = []
            do_buy, node, sell_this = rares.update_current(system, station)
            if do_buy:  # todo: find a way to fix this =\
                bot.bot.sendMessage(391834810, f'You have docked. Buy {node.name}!')
            if sell_this.__len__() > 0:  # TODO: either do catching or remove exceptions alltogether
                bot.bot.sendMessage(391834810, f'Eligible rares for selling: {", ".join(sell_this)}')
            # 2)
            # find closest rare not in list
            # check highest price difference
            # if distance more than cap or price higher than cap: return list
            # else continue with the next station
            possible_routes = rares.determine_next()
            for route in possible_routes:
                messages.append(f'Next stop: {route.get("system")}:{route.get("station")};'
                                f'Commodity: {route.get("commodity")}: Profit: {route.get("profit")}; '
                                f'Distance: {route.get("distance")}; Last update: {route.get("updated")} hours')
            bot.bot.sendMessage(391834810, '\n'.join(messages))
        else:
            messages = rares.clear()
            if messages.__len__() > 0:
                bot.bot.sendMessage(391834810, '\n'.join(messages))
    else:
        pass

di.shutdown()