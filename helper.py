
from eddb.station import station_loader
stations = station_loader(ids=[5611])
print(stations)
exit()


from bot import EliteBot
from config import telegram_token
bot = EliteBot(telegram_token)
#bot.run()
from eddi import EDDI
di = EDDI()


for update in di.update_generator():
    update = update.split(';')
    # switch event
    if update[0] == 'docked':
        system = update[1]
        station = update[2]
        if bot.trading:
            messages = []
            # 1)
            # check current rares distances
            #

            # 2)
            # find closest rare not in list
            # check highest price difference
            # if distance more than cap or price higher than cap: return list
            # else continue with the next station
            pass
    else:
        pass

di.shutdown()