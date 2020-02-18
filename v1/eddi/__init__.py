import os
from time import sleep
from threading import Thread
from eddb.logger import EliteLogger   # todo move logging into a separate package alltogether

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
            event = event.split(';')
            if event[0] == 'docked':
                self.current_system = event[1]
                self.current_station = event[2]
            if event[0] == 'mission':
                self.target_system = event[1]
                self.target_station = event[2]

    def startup(self):
        self.l.info('EDDI Thread starting up')
        self.t = Thread(target=self.event_listener, daemon=True)
        self.t.start()
        self.l.debug('Daemon thread running')

    def shutdown(self):
        self.l.info('Received shutdown command')
        self.run = False
        sleep(1)
        self.t.join()
        self.f.close()