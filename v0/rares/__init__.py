import time
import pickle
import os
import sys as system_module_lol
from eddb import eddb_prime
from eddb.station import station_loader, Station
from eddb.system import system_loader, System
try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    import matplotlib
    matplotlib.use('agg')
    from matplotlib import pyplot as plt
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

commodity_controller = Commodities()

class RareNode:
    def __init__(self, system: System, station: Station, prices: StationPriceList, terminus=False, echo=False):
        # graph literally has no reason to be two-way. why? no idea
        self.terminus = terminus
        self.system = system
        self.station = station
        self.prices = prices
        if terminus and not echo:  # new root node automatically creates graph-end terminus as well
            end = RareNode(None, None, None, terminus=True, echo=True)
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
        if not terminus:
            self.commodities = []

    @property
    def is_terminus(self):
        return self.terminus

    def add_commodity(self, name):
        comm = commodity_controller.get_by_name(name)
        if comm is None:
            comm = {'id': None, 'name': name}
        self.commodities.append(comm)

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
        return '<terminus>' if not self.system else f'{self.system.name}:{self.station.name}'

    def __eq__(self, other):
        return self.system == other.system and self.station == other.station

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
        self.root = RareNode(None, None, None, terminus=True)
        logger.info('Iterating through nodes')
        bar = generate_bar(nodes.__len__(), 'Inserting systems into graph')
        bar.start()
        for node in nodes:  # todo: don't recalculate graph on each insert may be?!
            self.insert(node)
            bar.update(bar.value + 1)
        bar.finish()



    def insert(self, node):
        # three passes to link the node
        logger.info(f'Parsing {node.system.name}:{node.station.name}')

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
        self.index[node.__str__()] = node

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

    def closest(self, system):
        distance = system.distance(self.nodes[0].system)
        ref = self.nodes[0]
        for node in self.nodes:
            chk = system.distance(node.system) < distance
            if chk < distance:
                ref = node
                distance = chk
        return ref

    def __generate(self, route, visited=[], sell_distance=150, max_ly=None):
        visited.append(route[-1]["node"])
        res = os.system('cls')
        if res != 0:
            os.system('clear')
        print([r["node"].system.name for r in route])
        # determine list of possible next nodes
        dup_possible_next_jump = [route[-1]["node"].link_x_forward, route[-1]["node"].link_x_backward,
                     route[-1]["node"].link_y_forward, route[-1]["node"].link_y_backward,
                     route[-1]["node"].link_z_forward, route[-1]["node"].link_z_backward]
        # clear terminus
        dup_possible_next_jump = [jump for jump in dup_possible_next_jump if not jump.terminus]
        # removing duplicates
        possible_next_jump = []
        for jump in dup_possible_next_jump:
            if jump not in possible_next_jump:
                possible_next_jump.append(jump)

        # filter visited which should be sold
        filtered_visited = []
        # bar = generate_bar(visited.__len__(), 'Removing sellable visited')
        # bar.start()
        for visit in visited:
            if visit.system.distance(route[-1]["node"].system) < sell_distance:
                filtered_visited.append(visit)
            # bar.update(bar.value + 1)
        # bar.finish()
        # filter by distance
        to_skip = []
        # bar = generate_bar(possible_next_jump.__len__(), 'Filtering visited by closing distance and max jump distance')
        # bar.start()
        for jump in possible_next_jump:
            for visit in visited:
                if visit.system.distance(route[-1]["node"].system) > visit.system.distance(jump.system):
                    to_skip.append(jump)
            if max_ly is not None:
                if route[-1]["node"].system.distance(jump.system) > max_ly:
                    to_skip.append(jump)

            # bar.update(bar.value + 1)
        possible_next_jump = [jump for jump in possible_next_jump if jump not in to_skip]
        # bar.finish()
        # if none are left - return false, we've hit a dead-end

        if possible_next_jump.__len__() == 0:
            print('    ' * route.__len__(), f'Terminated!')
            # return visited nodes
            return False

        # if any have been visited: loop is complete!
        # bar = generate_bar(possible_next_jump.__len__(), 'Checking loop possibility')
        # bar.start()
        for jump in possible_next_jump:
            if jump in [r["node"] for r in route]:
                profits = route[-1]["node"].prices - jump.prices
                route.append({"node": jump, "distance": route[-1]["node"].system.distance(jump.system),
                              "commodity": profits[0], "profit": profits[1], "updated": jump.prices.updated()})
                """({"node": jump["node"], "distance": jump["node"].system.distance(route[-1]["node"].system, ),
                  "commodity": jump["commodity"], "profit": jump["profit"],
                  "updated": jump["node"].prices.updated()})"""
                # todo: fix this profits returning either 0 or None bullshit =\\
                return True
            # bar.update(bar.value + 1)
        # bar.finish()

        # check profits:
        # bar = generate_bar(possible_next_jump.__len__(), 'Populating prices')
        # bar.start()
        jumps_and_profits = []
        for jump in possible_next_jump:
            comm_data = route[-1]["node"].prices - jump.prices
            jumps_and_profits.append({"node": jump, "profit": 0 if comm_data[1] is None else comm_data[1], "commodity": comm_data[0],
                                      "distance": jump.system.distance(route[-1]["node"].system)})
            # bar.update(bar.value + 1)
        jumps_and_profits = sorted(jumps_and_profits, key=lambda x: x["distance"])
        # bar.finish()
        # else take the best profit one and re-run GENERATE (doing this in a loop here
        # print(jumps_and_profits)
        ref_len = route.__len__()
        best_profit = 0
        best_profit_jump = jumps_and_profits[0]
        for jump in jumps_and_profits:
            route.append({"node": jump["node"], "distance": jump["distance"],
                          "commodity": jump["commodity"], "profit": jump["profit"],
                          "updated": jump["node"].prices.updated()})
            loop = self.__generate(route, visited=filtered_visited, sell_distance=sell_distance, max_ly=max_ly)
            # function has altered ROUTE
            if loop:  # if we have looped somewhere down the line, current route is cool
                return loop
            # if we do not loop, correct the route back:
            # know that we can't know how many nodes down the line the latest FALSE for a loop returned
            profit = 0  # check generated route cumulative profit
            for proposed_route_jump in route[ref_len:]:
                profit += proposed_route_jump["profit"]
            if profit > best_profit:
                best_profit_jump = jump
            while route.__len__() > ref_len:
                route.pop()
        # this loop on the first node will guarantee that if there's a loop it will get created.
        # if all failed to loop re-run for the best profit again and return
        # at this point, our route and visited are as we entered the algo

        jump = best_profit_jump
        route.append({"node": jump["node"], "distance": jump["node"].system.distance(route[-1]["node"].system),
                      "commodity": jump["commodity"], "profit": jump["profit"],
                      "updated": jump["node"].prices.updated()})
        # while we use the __generate function, it will not pop our current system or mess with the route.
        return self.__generate(route, filtered_visited, sell_distance=sell_distance, max_ly=max_ly)

    def node_by_commodity(self, cid=None, name=None):
        if not cid and not name:
            return None
        for node in self.nodes:
            if node.terminus:
                continue
            if cid is not None:
                if cid in [q['id'] for q in node.commodities]:
                    return node
            if name is not None:
                if name in [q['name'] for q in node.commodities]:
                    return node

    def generate_from(self, starting_node, current_system=None, first_jump_prices=None, sell_distance=150, max_ly=None):
        """
        format helper:
        [{"node": self.graph.nodes[0], "distance": 50, "commodity": "lulz", "profit": 400, "updated": 18},
         {"node": self.graph.nodes[1], "distance": 56, "commodity": "lulz2", "profit": 1400, "updated": 144}]"""
        route = [{"node": starting_node, "distance": 0, "commodity": None, "profit": None, "updated": starting_node.prices.updated()}]

        looped = self.__generate(route, sell_distance=sell_distance, max_ly=max_ly)  # visited systems are not returned because they shuffle about.

        if first_jump_prices is not None:
            best_deal = first_jump_prices - starting_node.prices
            route.insert(0, {"node": None, "distance": 0, "commodity": best_deal[0], "profit": best_deal[1], "updated": starting_node.prices.updated()})
            route[1]["distance"] = current_system.distance(route[1]["node"].system)

        for jump in route:
            jump['sell'] = []

        for jump in route:  # find where to sell what
            if jump["node"] is None:
                continue
            distance = 0
            ref = None
            for check in route:  #fixme if node does not exist (first-jump-thing)
                chk_dst = jump["node"].system.distance(check["node"].system)
                if chk_dst > distance:
                    distance = chk_dst
                    ref = check
            ref['sell'].append(jump['node'])
        if not looped:  # pretend we do have a loop
            route[0]['distance'] = route[-1]['node'].system.distance(route[0]['node'].system)
        return route

class RareLoader:
    def __init__(self, sell_distance=150):
        self.sell_distance = sell_distance

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
            dup = False
            for node in nodes:
                if node.system.id == system.id and node.station.sid == station.sid:
                    node.add_commodity(ref["Commodity"])
                    dup = True
                    break
            if dup:
                continue
            prices = None
            for listing in prices_list:
                if listing.station == station.sid:
                    prices = listing
            if prices is None:
                logger.warning(f'Skipping {ref["Commodity"]} because {station.name} has no listings')
                continue
            logger.debug(f'Created node for {ref["Commodity"]}')

            nodes.append(RareNode(system, station, prices))
            nodes[-1].add_commodity(ref['Commodity'])
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

    def alternative_determine_next(self, cur_system, cur_station, limit=10, visited=[]):   # expecting current
        # cur_system = self.route[-1][0]
        ref_dict = {}
        node_dict = {}
        prices = None
        for node in self.graph.nodes:
            if node.terminus:
                continue
            if node.system == cur_system:
                prices = node.prices
                continue
            ref_dict[node.__str__()] = cur_system.distance(node.system)
            node_dict[node.__str__()] = node
        if prices is None:
            prices = StationPriceList(cur_station.sid)
            prices.populate()
        nodelist = sorted(ref_dict, key=lambda k: ref_dict[k])
        nodelist = [node_dict[q] for q in nodelist]
        to_skip = []
        for node in nodelist:
            for visit in visited:
                if cur_system.distance(visit.system) > node.system.distance(visit.system):  # distance closes!
                    to_skip.append(node)
        logger.debug(f'Filtering systems from {nodelist.__len__()}')
        nodelist = [node for node in nodelist if node not in to_skip]
        logger.debug(f'Resulting list is {nodelist.__len__()}')
        ret_obj = []
        for node in nodelist[:limit]:
            profit = prices - node.prices
            ret_obj.append({'system': node.system.name, 'station': node.station.name,
                            'commodity': [q['name'] for q in node.commodities],
                            'buy': '<none>' if profit[0] is None else profit[0].name,
                            'profit': profit[1], 'distance': ref_dict[node.__str__()],
                            'updated': (time.time() - node.system.updated_at) / 60 / 60})
        return ret_obj

    def query(self, system, station):
        return self.graph.query(system, station)

    def generate(self, system, station, node=None, max_ly=None):  # TODO: add limiters for something. max distance would be ok, but it's always "next over" so dunno. return trips are a failure though.
        if node is None:
            node = self.graph.closest(system)
            prices = StationPriceList(station)
            prices.populate()
        else:
            prices = None
        route = self.graph.generate_from(node, current_system=system, first_jump_prices=prices, sell_distance=self.sell_distance, max_ly=max_ly)
        return route

    def check_sell(self, current_system, visited):
        dst = current_system.distance(visited.system)
        if dst >= self.sell_distance:
            return dst
        else:
            return None

    def query_by_commodity(self, cid=None, name=None):
        return self.graph.node_by_commodity(cid=cid, name=name)

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
