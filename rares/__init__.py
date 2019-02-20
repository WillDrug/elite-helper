import csv
from eddb.station import station_loader, Station
from eddb.system import system_loader, System


class RareNode:
    def __init__(self, name: str, accomodation: int, system: System, station: Station):
        self.name = name
        self.accomodation = accomodation
        self.system = system
        self.station = station

    def __str__(self):
        return self.name

    def link_x(self, other):
        pass

    def link_y(self, other):
        pass

    def link_z(self, other):
        pass

    def __eq__(self, other):
        return self.name == other.name

    def sub_x(self, other):
        return self.system.x - other.system.x

    def sub_y(self, other):
        return self.system.y - other.system.y

    def sub_z(self, other):
        return self.system.z - other.system.z


# TODO: remove system graph from here and do a separate package
class RareGraph:
    def __init__(self, nodes: list = []):
        nodes = sorted(nodes, key=lambda node: (node.system.x, node.system.y, node.system.z))  # sorting to speed up insertion
        self.index = dict()
        self.nodes = list()
        for node in nodes:  # todo: don't recalculate graph on each insert may be?!
            self.insert(node)

    def insert(self, node: RareNode):
        if node.name in self.index.keys():
            return
        if self.nodes.__len__() == 0:
            self.nodes.append(node)
        # there's at least another one present.
        closest_x = self.nodes[0]
        closest_y = self.nodes[0]
        closest_z = self.nodes[0]

        for ref_node in self.nodes:  # here x, y and z links can be duplicates... todo : fix?! O_o
            # 1) find closest node on X and insert
            if node.sub_x(ref_node) < node.sub_x(closest_x):
                closest_x = ref_node
            # 2) find closest node on Y and insert
            if node.sub_y(ref_node) < node.sub_y(closest_y):
                closest_y = ref_node
            # 3) find closest node on Z and insert
            if node.sub_z(ref_node) < node.sub_z(closest_z):
                closest_z = ref_node
        # 4) relink nodes to each other
        # 4.1) save closest connect new node to closest
        # 5) insert into list and dict
        self.index[node.name] = node
        self.nodes.append(node)



class RareLoader:
    def __init__(self, ship_size='None', max_distance_from_star=-1):
        f = open('rares/reference.tsv', 'r', encoding='utf-8')  # todo, fix to os.base
        header = f.readline().split(';')
        reference = list()
        for line in f.readlines():
            entry = dict()
            for e, k in zip(line.split(','), self.header):
                entry[k] = e
            reference.append(entry)

        f.close()

        # load up systems to get id's
        # todo: may be do sort-merge here? although not really necessary on a small list
        systems = system_loader(names=[q['system'] for q in reference])

        # load up station infos
        station_filter = list()
        # pair up each reference with a system id
        for ref in reference:
            for sys in systems:
                if ref['system'] == sys.name:
                    station_filter.append((ref['Port'], sys.id))
                    break
        stations = station_loader(refs=station_filter, landing_pad=ship_size, distance_to_star=max_distance_from_star)

        nodes = []

        for ref in reference:
            system = None
            for sys in systems:
                if ref['System'] == sys.name:
                    system = sys
                    break
            if system is None:
                raise NameError('System not found')
            station = None
            for st in stations:
                if ref['Port'] == st.name:
                    station = st
                    break
            if station is None:
                raise NameError('Station not found')

            nodes.append(RareNode(ref['Commodity'], ref['Allocation'], system, station))

        self.graph = RareGraph(nodes=nodes)

        # create graph of Systems with stations attached
        # initialize current state if requested