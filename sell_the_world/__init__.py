from eddb import eddb_prime
from eddb.system import System, system_loader
from eddb.station import Station, station_loader
from eddb.pricelist import StationPriceList, listing_loader
from eddb.commodity import Commodities

commodity_controller = Commodities



class StationNode:
    def __init__(self):
        pass

class StationGraph:
    def __init__(self, nodes: list = []):
        for node in nodes:
            self.insert(node)

    def insert(self, node):
        pass

class ProfitFinder:
    def __init__(self, max_ly=150, ship_size='L', max_distance_from_star=50000):
        self.max_ly = max_ly
        self.max_distance_from_star = max_distance_from_star
        self.ship_size = ship_size

        self.graph = StationGraph()