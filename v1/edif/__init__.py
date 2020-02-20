from eddb.logger import EliteLogger
from pprint import pprint


class InterfaceDeadEnd(Exception):
    pass

class EliteInterfaceMenu:
    def __init__(self, data):
        self.menu = data
        self.current = None

    def set_action(self, action):
        self.current = self.menu.get(action)
        if self.current is None:
            raise InterfaceDeadEnd('Failed to fetch function')
        return [q for q in self.current.keys() if q != 'function']

    def add_item(self, item, value):
        self.current[item] = value

    def execute(self):
        return self.current['function'](**{q: self.current[q] for q in self.current if q != 'function'})

class EliteInterface:
    def __init__(self, menu, current_state=None):
        self.keep_alive = True
        menu['exit'] = {'function': self.exit}
        self.menu = EliteInterfaceMenu(menu)
        self.l = EliteLogger('Interface')
        self.cs = current_state

    def set_menu(self, data):
        self.menu = EliteInterfaceMenu(data)

    def prompt(self, msg):
        ret = input(f'{msg}> ')
        if ret == '' or ret == -1:
            return None
        if ret == 'True':
            return True
        if ret == 'False':
            return False
        if ret[0] == '%':
            try:
                return getattr(self.cs, ret[1:])
            except AttributeError:
                self.l.warning(f'Attribute {ret} not found')
        return ret

    def run(self):
        while self.keep_alive:
            try:
                parms = self.menu.set_action(self.prompt('CMD'))
                if parms.__len__() == 0:
                    self.menu.execute()
                else:
                    for parm in parms:
                        self.menu.add_item(parm, self.prompt(f'Input {parm}'))
                    response = self.menu.execute()
                    pprint(response)
            except InterfaceDeadEnd:
                self.l.error(f'No command found')

    def exit(self):
        self.keep_alive = False