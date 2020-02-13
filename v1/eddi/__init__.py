import os
from time import sleep
from threading import Thread

class EDDI:
    def __init__(self, loc=f'{os.getenv("APPDATA")}\EDDI\speechresponder.out'):
        f = open(loc, 'w', encoding='utf-8')  # clear file
        f.close()
        self.f = open(loc, 'r', encoding='utf-8')
        self.run = True

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
                sleep(0.1)
                continue
            yield line
        raise StopIteration

    def shutdown(self):
        self.run = False
        sleep(1)
        self.f.close()

    def update(self, s):
        pass

    def event_listener(self):
        for event in self.update_generator():
            event = event.split(';')
            if event[0] == 'docked':
                self.current_system = event[1]
                self.current_station = event[2]
            if event[0] == 'mission':
                self.target_system = event[1]
                self.target_station = event[2]

    def startup(self):
        self.t = Thread(target=self.event_listener)
        self.t.daemon = True
        self.t.run()

    def shutdown(self):
        self.run = False
        sleep(1)
        self.t.join()
        self.f.close()