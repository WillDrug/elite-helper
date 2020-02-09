from eddb import eddb_prime
from math import sqrt
from eddb.progress_tracker import generate_bar, track_job
import json

import os
this_api = 'systems.csv'


def system_loader(ids: list = [], names: list = [], filter_needs_permit = False):

    eddb_prime.recache(this_api)
    gen = eddb_prime.read_iter(this_api)
    header = gen.__next__()
    header = header.split(',')

    ret = list()

    bar = generate_bar(gen.size, 'Filtering systems')
    bar.value = 0
    bar.start()

    for system in gen:
        bar.update(bar.value + system.encode('utf-8').__len__())
        # todo: think about switching this to rares implementation, with zipped(header, line) cycle, creating dict instead of .index() call
        system = system.split(',')
        name = system[header.index('name')].replace('"', '')
        sid = system[header.index('id')]

        if ids.__len__() > 0 and sid not in ids:
            continue

        if names.__len__() > 0 and name not in names:
            continue

        if filter_needs_permit and int(system[header.index('needs_permit')]) > 0:
            continue

        sys = System(sid, name)
        sys._populate(system[header.index('id')], system[header.index('name')], float(system[header.index('x')]), float(system[header.index('y')]), float(system[header.index('z')]),
                      system[header.index('allegiance')], int(system[header.index('needs_permit')]), int(system[header.index('updated_at')]))
        ret.append(sys)
    bar.finish()
    return ret

class System:

    def __init__(self, name):
        if not name:
            raise IndexError('Specify name')
        self.name = name
        self.id = None

    def __eq__(self, other):
        return self.id == other.id

    def _populate(self, sid, name, x, y, z, allegiance, needs_permit, updated_at):
        self.id = int(sid)
        self.name = name.replace('"', '')
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        if allegiance == 'None':
            self.allegiance = None
        else:
            self.allegiance = allegiance
        self.needs_permit = True if int(needs_permit) > 0 else False
        self.updated_at = int(updated_at)

    def populate(self):
        ix1 = self.name[0] if self.name[0] != '*' else 'ast'
        if self.name.__len__() > 1:
            ix2 = self.name[1] if self.name[1] != '*' else 'ast'
        else:
            ix2 = ''
        gen_ob = eddb_prime.read_object(this_api, index=f'{ix1}{ix2}')
        gen = gen_ob.readlines()
        gen_ob.close()
        bar = generate_bar(gen.__len__(), 'Filtering systems')
        bar.value = 0
        bar.start()

        for system in gen:
            bar.update(bar.value + 1)
            system = json.loads(system)


            if self.name is not None and system.get('name') != self.name:
                continue
            if self.id is not None and system.get('id') != self.id:
                continue

            self._populate(system.get('id'), system.get('name'), float(system.get('x')), float(system.get('y')),
                          float(system.get('z')),
                          system.get('allegiance'), int(system.get('needs_permit')), int(system.get('updated_at')))
            bar.finish()
            return True
        bar.finish()
        return False

    def distance(self, other):
        return abs(sqrt(pow(self.x-other.x, 2) + pow(self.y-other.y, 2) + pow(self.z-other.z, 2)))
