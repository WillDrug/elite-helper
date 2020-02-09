import os
from time import sleep

class EDDI:
    def __init__(self, loc=f'{os.getenv("APPDATA")}\EDDI\speechresponder.out'):
        f = open(f'{os.getenv("APPDATA")}\EDDI\speechresponder.out', 'w', encoding='utf-8')
        f.close()
        self.f = open(f'{os.getenv("APPDATA")}\EDDI\speechresponder.out', 'r', encoding='utf-8')
        self.run = True

    def update_generator(self):
        self.run = True
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