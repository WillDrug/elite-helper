import os
from time import sleep
from threading import Thread
from eddb.logger import EliteLogger   # todo move logging into a separate package alltogether
from eddb.ORM import Session, Listing, Station

class EDDI:
    def __init__(self, loc=f'{os.getenv("APPDATA")}\EDDI\speechresponder.out'):
        f = open(loc, 'w', encoding='utf-8')  # clear file
        f.close()
        self.f = open(loc, 'r', encoding='utf-8')
        self.run = True
        self.l = EliteLogger('EDDI Connector')

        self.current_system = None
        self.current_station = None
        self.target_system = None
        self.target_station = None

    def update_generator(self):
        # self.run = True
        self.f.seek(0, 2)
        while self.run:
            line = self.f.readline()
            if not line:
                sleep(0.5)
                continue
            yield line
        raise StopIteration

    def update(self, s):
        pass

    def event_listener(self):
        for event in self.update_generator():
            self.l.debug(f'EDDI reports got event {event}')
            event = event.strip().split(';')
            if event[0] == 'docked':
                self.current_system = event[1]
                self.current_station = event[2]
            if event[0] == 'undocked':
                self.current_station = None
            if event[0] == 'jump':
                self.current_system = event[1]
            if event[0] == 'mission':
                self.target_system = event[1]
                self.target_station = event[2]
            if event[0] == 'listings':
                if self.current_station is None:
                    self.l.warning('No current system')
                    continue
                print(self.current_station)
                s = Session()
                station = s.query(Station).filter(Station.name == self.current_station).first()
                self.l.debug(event)
                self.l.info('Updating listings')
                event.pop(0)
                event.pop()  # crutch
                while True:
                    try:
                        eddb_id = int(event.pop(0))

                        buyprice = event.pop(0)
                        if buyprice == '':
                            buyprice = 0
                        else:
                            buyprice = int(buyprice)

                        sellprice = event.pop(0)
                        if sellprice == '':
                            sellprice = 0
                        else:
                            sellprice = int(sellprice)

                        supply = event.pop(0)
                        if supply == '':
                            supply = 0
                        else:
                            supply = int(supply)

                        demand = event.pop(0)
                        if demand == '':
                            demand = 0
                        else:
                            demand = int(demand)

                        name = event.pop(0)

                    except IndexError:
                        break
                    self.l.debug(f'Updating {station.name} listing for {name}')
                    listing = s.query(Listing).filter(Listing.station_id == station.id).filter(Listing.commodity_id == eddb_id).first()
                    if listing is None:
                        self.l.error(f'Error! {name} was not listed for {station.name} before. Refusing to create')
                        continue
                    listing.buy_price = buyprice
                    listing.sell_price = sellprice
                    listing.supply = supply
                    listing.demand = demand
                self.l.info(f'Updated {station.name} listings')
                s.commit()
                s.close()

    def startup(self):
        self.l.info('EDDI Thread starting up')
        self.t = Thread(target=self.event_listener, daemon=True)
        self.t.start()
        self.l.debug('Daemon thread running')

    def shutdown(self):
        self.l.info('Received shutdown command')
        if not self.run:
            self.l.warning('Thread not running')
            return
        self.run = False
        sleep(1)
        self.t.join()
        self.f.close()