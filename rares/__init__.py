import time
import pickle
import os
import sys as system_module_lol
from eddb import eddb_prime
from eddb.station import station_loader, Station
from eddb.system import system_loader, System
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import logging
from eddb.progress_tracker import generate_bar
from progressbar import UnknownLength
from eddb.pricelist import listing_loader, StationPriceList
from eddb.commodity import Commodities
logger = logging.getLogger('RareGraph')
logger.handlers = []
logger.addHandler(logging.StreamHandler(stream=system_module_lol.stdout))
logger.setLevel(logging.DEBUG)



class RareNode:
    def __init__(self, name: str, system: System, station: Station, prices: StationPriceList, terminus=False, echo=False):
        # graph literally has no reason to be two-way. why? no idea
        self.terminus = terminus
        self.name = name
        self.system = system
        self.station = station
        self.prices = prices
        if terminus and not echo:  # new root node automatically creates graph-end terminus as well
            end = RareNode(None, None, None, None, terminus=True, echo=True)
            self.link_x_forward = end
            self.link_x_backward = None
            self.link_y_forward = end
            self.link_y_backward = None
            self.link_z_forward = end
            self.link_z_backward = None
            end.link_x_backward = self
            end.link_y_backward = self
            end.link_z_backward = self
            end.link_x_forward = None
            end.link_y_forward = None
            end.link_z_forward = None

    @property
    def is_terminus(self):
        return self.terminus


    def next_x_gt(self, node):
        if self.link_x_forward.terminus:
            return True
        if self.link_x_forward.system.x >= node.system.x:
            return True
        return False

    def next_y_gt(self, node):
        if self.link_y_forward.terminus:
            return True
        if self.link_y_forward.system.y >= node.system.y:
            return True
        return False

    def next_z_gt(self, node):
        if self.link_z_forward.terminus:
            return True
        if self.link_z_forward.system.y >= node.system.y:
            return True
        return False

    def __str__(self):
        return '<terminus>' if not self.name else self.name

    def __eq__(self, other):
        return self.name == other.name

    def insert_x(self, node):
        swap = self.link_x_forward
        self.link_x_forward = node
        node.link_x_forward = swap
        swap.link_x_backward = node
        node.link_x_backward = self

    def insert_y(self, node):
        swap = self.link_y_forward
        self.link_y_forward = node
        node.link_y_forward = swap
        swap.link_y_backward = node
        node.link_y_backward = self

    def insert_z(self, node):
        swap = self.link_z_forward
        self.link_z_forward = node
        node.link_z_forward = swap
        swap.link_z_backward = node
        node.link_z_backward = self





# TODO: remove system graph from here and do a separate package
class RareGraph:
    def __init__(self, nodes: list = []):

        logger.info('Graph engine initializing')
        logger.info('Sorting nodes')
        # sorting to speed up insertion
        # graph contains lesser X-Y-Z as top nodes; all nodes are expected to have 3 links (XYZ)
        nodes = sorted(nodes, key=lambda t_node: (t_node.system.x, t_node.system.y, t_node.system.z))
        self.index = dict()
        self.nodes = list()
        logger.info('Creating root node')
        self.root = RareNode(None, None, None, None, terminus=True)
        logger.info('Iterating through nodes')
        bar = generate_bar(nodes.__len__(), 'Inserting systems into graph')
        bar.start()
        for node in nodes:  # todo: don't recalculate graph on each insert may be?!
            self.insert(node)
            bar.update(bar.value + 1)
        bar.finish()

    def insert(self, node):
        # three passes to link the node
        logger.info(f'Parsing {node.name}')
        ref_x = self.root
        ref_y = self.root
        ref_z = self.root
        logger.info('Parse_X')
        bar = generate_bar(self.nodes.__len__(), 'Parse_X')
        bar.start()
        while True:
            if ref_x.next_x_gt(node):
                ref_x.insert_x(node)
                break
            else:
                ref_x = ref_x.link_x_forward
            bar.update(bar.value + 1)
        bar.finish()

        bar = generate_bar(self.nodes.__len__(), 'Parse_Y')
        bar.start()
        while True:
            if ref_y.next_y_gt(node):
                ref_y.insert_y(node)
                break
            else:
                ref_y = ref_y.link_y_forward
            bar.update(bar.value + 1)
        bar.finish()

        bar = generate_bar(self.nodes.__len__(), 'Parse_Z')
        bar.start()
        while True:
            if ref_z.next_z_gt(node):
                ref_z.insert_z(node)
                break
            else:
                ref_z = ref_z.link_z_forward
            bar.update(bar.value + 1)
        bar.finish()

        # keep a full list for future ref
        self.nodes.append(node)

        # index this shit up.
        self.index[node.name] = node

    def plot_to(self, x, y, z):
        nodes = []
        ref = self.root
        for i in range(x):
            if ref.link_x_forward.terminus:
                break
            ref = ref.link_x_forward
            nodes.append(ref)
        ref = self.root
        for i in range(y):
            if ref.link_y_forward.terminus:
                break
            ref = ref.link_y_forward
            nodes.append(ref)
        ref = self.root
        for i in range(z):
            if ref.link_z_forward.terminus:
                break
            ref = ref.link_z_forward
            nodes.append(ref)
        self.plot(nodes)

    def plot(self, nodes=None):
        if nodes is None:
            nodes = self.nodes
        ax = plt.gca(projection="3d")
        x = list()
        y = list()
        z = list()
        for node in nodes:
            x.append(node.system.x)
            y.append(node.system.y)
            z.append(node.system.z)

        ax.scatter(x, y, z, c='r', s=100)
        ax.plot(x, y, z, color='r')
        plt.show()

    def query(self, system, station):
        logger.info(f'Querying {system}:{station}')
        for node in self.nodes:
            if node.system.name == system and node.station.name == station:
                return node
        return None

class RareLoader:
    def __init__(self):
        pass

    def process_cargo(self, cargo):
        logger.info(f'Checking :{cargo}:')
        for node in self.graph.nodes:
            if node.name == cargo:
                logger.info(f'Appended a node for {cargo}')
                self.visited.append(node)

    def prime(self, ship_size, max_distance_from_star, filter_permit=True):
        logger.info('Opening file for RareLoader')
        f = open(f'{os.path.dirname(os.path.realpath(__file__))}/reference.tsv', 'r', encoding='utf-8')
        header = f.readline().split(';')
        reference = list()
        logger.info('Reading reference')
        for line in f.readlines():
            entry = dict()
            logger.debug(f'Processing {entry}')
            for e, k in zip(line.split(';'), header):
                logger.debug(f'{k} is {e}')
                entry[k.strip()] = e.strip()
            reference.append(entry)

        f.close()

        # load up systems to get id's
        # todo: may be do sort-merge here? although not really necessary on a small list
        logger.info('Loading systems')
        systems = system_loader(names=[q['System'] for q in reference], filter_needs_permit=filter_permit)

        # load up station infos
        station_filter = list()
        # pair up each reference with a system id
        logger.info('Creating station filter')
        for ref in reference:
            for sys in systems:
                if ref['System'] == sys.name:
                    station_filter.append((ref['Port'], sys.id))
                    break
        logger.info('Loading stations')
        stations = station_loader(refs=station_filter, landing_pad=ship_size, distance_to_star=max_distance_from_star)
        prices_list = listing_loader([q.sid for q in stations])
        nodes = []

        logger.info('Creating graph nodes')
        for ref in reference:
            system = None
            for sys in systems:
                if ref['System'] == sys.name:
                    system = sys
                    break
            if system is None:
                logger.warning(f'System {ref["System"]} not found, skipping')
                continue
                # raise NameError(f'System >:{ref["System"]}:< not found')
            station = None
            for st in stations:
                if ref['Port'] == st.name:
                    station = st
                    break
            if station is None:
                logger.warning(f'Station {ref["Port"]} not found')
                # raise NameError(f'Station {ref["Port"]} not found')
                continue
            prices = None
            for listing in prices_list:
                if listing.station == station.sid:
                    prices = listing
            if prices is None:
                logger.warning(f'Skipping {ref["Name"]} because {station.name} has no listings')
                continue
            logger.debug(f'Created node for {ref["Commodity"]}')
            nodes.append(RareNode(ref['Commodity'], system, station, prices))
        logger.info('Creating graph')
        self.graph = RareGraph(nodes=nodes)

        # create graph of Systems with stations attached
        # initialize current state if requested
        logger.info('Dumping backup data')
        pickle.dump(self.graph, open(f'{os.path.dirname(os.path.realpath(__file__))}/graph_dump.pcl', 'wb'))

    def init(self, ship_size='None', max_distance_from_star=-1, filter_needs_permit=False):
        self.ship_size = ship_size
        self.max_distance_from_star = max_distance_from_star

        logger.info('Rare loader initializing')
        logger.info('Trying to unpickle populated data')
        results = []
        for api in ['commodities.json', 'stations.jsonl', 'listings.csv', 'systems.csv']:
            results.append(eddb_prime.recache(api))
        if any(results):
            logger.info('Recache needed')
            self.prime(self.ship_size, self.max_distance_from_star, filter_needs_permit)
        else:
            try:
                self.graph = pickle.loads(
                    open(f'{os.path.dirname(os.path.realpath(__file__))}/graph_dump.pcl', 'rb+').read())
            except FileNotFoundError:
                logger.info('Failed to load up backup, reloading')
                self.prime(ship_size, max_distance_from_star, filter_needs_permit)

    def alternative_determine_next(self, cur_system, cur_station, limit=10):   # expecting current
        # cur_system = self.route[-1][0]
        ref_dict = {}
        node_dict = {}
        prices = None
        for node in self.graph.nodes:
            if node.terminus:
                continue
            if node.system == cur_system:
                prices = node.prices
            ref_dict[node.name] = cur_system.distance(node.system)
            node_dict[node.name] = node
        if prices is None:
            prices = StationPriceList(cur_station.sid)
            prices.populate()
        nodelist = sorted(ref_dict, key=lambda k: ref_dict[k])
        nodelist = [node_dict[q] for q in nodelist]
        to_skip = []
        for node in nodelist:
            for visit in self.visited:
                if cur_system.distance(visit.system) > node.system.distance(visit.system):  # distance closes!
                    to_skip.append(node)
        logger.debug(f'Filtering systems from {nodelist.__len__()}')
        nodelist = [node for node in nodelist if node not in to_skip]
        logger.debug(f'Resulting list is {nodelist.__len__()}')
        ret_obj = []
        for node in nodelist[:limit]:
            profit = prices - node.prices
            ret_obj.append({'system': node.system.name, 'station': node.station.name,
                            'commodity': node.name,
                            'buy': '<none>' if profit[0] is None else profit[0].name,
                            'profit': profit[1], 'distance': ref_dict[node.name],
                            'updated': (time.time() - node.system.updated_at) / 60 / 60})
        return ret_obj

    def query(self, system, station):
        return self.graph.query(system, station)

    def generate(self, system, station, node = None):
        pass

if __name__ == '__main__':
    chona = System(name='Chona')
    chona.populate()
    rl = RareLoader()
    rl.init('L', 50000, True)
    distance = 50000
    ref = None
    for node in rl.graph.nodes:
        if chona.distance(node.system) < distance:
            distance = chona.distance(node.system)
            ref = node.system
    print(ref.name, distance)
