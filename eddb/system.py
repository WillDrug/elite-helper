from . import eddb
from math import sqrt

this_api = 'systems.csv'

def system_loader(ids: list = [], names: list = []):
    eddb.recache(this_api)
    gen = eddb.read_iter(this_api)
    header = gen.__next__()
    header = header.split(',')

    ret = list()

    for system in gen:
        # todo: think about switching this to rares implementation, with zipped(header, line) cycle, creating dict instead of .index() call
        system = system.split(',')
        name = system[header.index('name')]
        sid = system[header.index('id')]
        if ids.__len__() > 0 and sid not in ids:
            continue
        if names.__len__() > 0 and name not in names:
            continue

        sys = System(sid, name)
        sys._populate(sid, name, system[header.index('x')], system[header.index('y')], system[header.index('z')],
                      system[header.index('allegiance')], system[header.index('needs_permit')])

    return ret

class System:
    def __init__(self, sid=None, name=None):
        if not sid and not name:
            raise IndexError('Specify at least one ID')
        self.id = sid
        self.name = name

    def _populate(self, sid, name, x, y, z, allegiance, needs_permit):
        self.id = int(sid)
        self.name = name.replace('"', '')
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        if allegiance == 'None':
            self.allegiance = None
        else:
            self.allegiance = allegiance
        self.needs_permit = True if needs_permit > 0 else False

    def populate(self):
        pass  # TODO: update info from eddb and shit


    def distance(self, other):
        return abs(sqrt(pow(self.x-other.x,2)+pow(self.y-other.y,2)+pow(self.z-other.z,2)))
