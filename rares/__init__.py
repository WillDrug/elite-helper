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
logger.setLevel(logging.INFO)



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

    def determine_next(self, sysst, visited):
        """messages.append(f'Next stop: {route.get("system")}:}{route.get("station")};'
                                f'Commodity: {route.get("commodity")}: Profit: {route.get("profit")}; '
                                f'Distance: {route.get("distance")}; Last update: {route.get("updated")} hours')"""
        system, station = sysst
        # try to find the node
        cur_node = self.root
        for node in self.nodes:
            if node.system == system and node.station == station:
                cur_node = node
        if cur_node.is_terminus:  # find x-y-z closest
            routes = []
            cur_node = self.root
            best_distance = None
            x_node = None
            # pass_x
            bar = generate_bar(UnknownLength, 'Doing X-pass')
            bar.start()
            while not cur_node.link_x_forward.is_terminus:
                bar.update(bar.value + 1)
                new_distance = abs(cur_node.link_x_forward.system.x - system.x)
                if best_distance is None or new_distance < best_distance:
                    best_distance = new_distance
                    x_node = cur_node.link_x_forward
                cur_node = cur_node.link_x_forward
            if x_node is not None:
                routes.append(x_node)
            bar.finish()
            # pass_y
            cur_node = self.root
            best_distance = None
            y_node = None
            # pass_x
            bar = generate_bar(UnknownLength, 'Doing Y-pass')
            bar.start()
            while not cur_node.link_y_forward.is_terminus:
                bar.update(bar.value + 1)
                new_distance = abs(cur_node.link_y_forward.system.y - system.y)
                if best_distance is None or new_distance < best_distance:
                    best_distance = new_distance
                    y_node = cur_node.link_y_forward
                cur_node = cur_node.link_y_forward
            if y_node is not None:
                routes.append(y_node)
            bar.finish()

            # pass_z
            cur_node = self.root
            best_distance = None
            z_node = None
            bar = generate_bar(UnknownLength, 'Doing Z-pass')
            bar.start()
            while not cur_node.link_z_forward.is_terminus:
                bar.update(bar.value + 1)
                new_distance = abs(cur_node.link_z_forward.system.z - system.z)
                if best_distance is None or new_distance < best_distance:
                    best_distance = new_distance
                    z_node = cur_node.link_z_forward
                cur_node = cur_node.link_z_forward
            if z_node is not None:
                routes.append(z_node)

            bar.finish()

            # profits
            prices = StationPriceList(station.sid)
            prices.populate()
            new_routes = []
            for route in routes:
                new_routes.append({'node': route, 'profit': prices - route.prices})
            routes = new_routes
        else:
            routes = [{'node': cur_node.link_x_forward, 'profit': cur_node.prices - cur_node.link_x_forward.prices},
                      {'node': cur_node.link_x_backward, 'profit': cur_node.prices - cur_node.link_x_backward.prices},
                      {'node': cur_node.link_y_forward, 'profit': cur_node.prices - cur_node.link_y_forward.prices},
                      {'node': cur_node.link_y_backward, 'profit': cur_node.prices - cur_node.link_y_backward.prices},
                      {'node': cur_node.link_z_forward, 'profit': cur_node.prices - cur_node.link_z_forward.prices},
                      {'node': cur_node.link_z_backward, 'profit': cur_node.prices - cur_node.link_z_backward.prices}]

        # filter routes by visited
        # routes are always filled with nodes
        to_skip = []
        bar = generate_bar(routes.__len__()*visited.__len__(), 'Filtering visited')
        bar.start()
        for route in routes:
            if route['node'].terminus:
                to_skip.append(route['node'])
                continue
            for visit in visited:
                if system.distance(visit.system) > route['node'].system.distance(visit.system):  # distance closes!
                    to_skip.append(route['node'])
                bar.update(bar.value + 1)
        bar.finish()
        routes = [route for route in routes if route['node'] not in to_skip]
        # todo: fix possible duplicates
        """messages.append(f'Next stop: {route.get("system")}:}{route.get("station")};'
                                        f'Commodity: {route.get("commodity")}: Profit: {route.get("profit")}; '
                                        f'Distance: {route.get("distance")}; Last update: {route.get("updated")} hours')"""
        ret_obj = []
        for node in routes:
            ret_obj.append({'system': node['node'].system.name, 'station': node['node'].station.name,
                            'commodity': node['node'].name,
                            'buy': '<none>' if node['profit'][0] is None else node['profit'][0].name, 'profit': node['profit'][1], 'distance': system.distance(node['node'].system),
                            'updated': (time.time()-node['node'].system.updated_at)/60/60})
        return ret_obj


    def query(self, system, station):
        logger.info(f'Querying {system}:{station}')
        for node in self.nodes:
            if node.system.name == system and node.station.name == station:
                return node
        return None

class RareLoader:
    def __init__(self):
        pass

    def prime(self, ship_size, max_distance_from_star):
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
        systems = system_loader(names=[q['System'] for q in reference])

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

    def init(self, ship_size='None', max_distance_from_star=-1):
        self.ship_size = ship_size
        self.max_distance_from_star = max_distance_from_star

        logger.info('Rare loader initializing')
        logger.info('Trying to unpickle populated data')
        results = []
        for api in ['commodities.json', 'stations.jsonl', 'listings.csv', 'systems.csv']:
            results.append(eddb_prime.recache(api))
        if any(results):
            logger.info('Recache needed')
            self.prime(self.ship_size, self.max_distance_from_star)
        else:
            try:
                self.graph = pickle.loads(
                    open(f'{os.path.dirname(os.path.realpath(__file__))}/graph_dump.pcl', 'rb+').read())
            except FileNotFoundError:
                logger.info('Failed to load up backup, reloading')
                self.prime(ship_size, max_distance_from_star)

        self.route = []
        self.visited = []

    def clear(self):
        messages = []
        for v in self.visited:
            messages.append(f'Sell {v.name} somewhere.')
        self.route = []
        self.visited = []
        return messages

    def check_sell(self):
        ret = list()
        for node in self.visited:
            if self.route[-1][0].distance(node.system) > 150:  # todo: config this up
                ret.append(node.name)
        self.visited = [v for v in self.visited if v.name not in ret]  # clear
        return ret

    def update_current(self, system, station):
        node = self.graph.query(system, station)  # redo names to class objects
        if not node:
            system_o = System(name=system)
            station_o = Station(name=station)
            logger.info(f'Populating system {system}')
            if not system_o.populate():
                raise LookupError(f'Failed to find system :{system}:')
            print(system_o.name, system_o.id)
            logger.info(f'Populating station {station} with ref as {system_o.id}')
            if not station_o.populate(system_id=system_o.id):  # TODO: there are duplicate system names. try consulting simbad_ref field and parse the whole file on a .populate() sweep
                raise LookupError(f'Failed to find station :{station}:')
            do_buy = False
            self.route.append((system_o, station_o))
        else:
            self.visited.append(node)
            self.route.append((node.system, node.station))
            do_buy = True

        sell_this = self.check_sell()

        return do_buy, node, sell_this  # seconds to minutes to hours updated
        # awaiting [{'rare': ,'buy': , 'profit', 'distance': ''}]

    def determine_next(self):
        return self.graph.determine_next(self.route[-1], self.visited)


if __name__ == '__main__':
    rl = RareLoader()
    rl.init('None', -1)
    # rl.update_current('Delphi', 'The Oracle')
    rl.update_current('HR 7221', 'Veron City')
    print(rl.determine_next())
    rl.update_current('Holva', 'Kreutz Orbital')
    print(rl.determine_next())