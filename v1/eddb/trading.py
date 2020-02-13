from .ORM import *
from .logger import EliteLogger
from . import settings

class TooManyStations(Exception):
    pass

class Trader:
    def __init__(self, ship_size=None, max_distance=None, requires_permit=False):
        self.l = EliteLogger('Trader')
        self.ship_size = ship_size
        self.max_distance = max_distance
        self.requires_permit = requires_permit


    def __populate_system(self, system_name):
        s = Session()

        sub = s.query(System).filter(System.name == system_name)
        system = sub.first()
        s.close()
        return system


    def __populate_station(self, station_name, system=None):
        s = Session()

        sub = s.query(Station).filter(Station.name == station_name)
        if system is not None:
            sub = sub.filter(Station.system_id == system.id)

        stations = sub.all()
        s.close()

        if stations.__len__() > 1:
            raise TooManyStations('Specify the system, jerk')
        if stations.__len__() == 0:
            return None

        return stations[0]

    def __find_trading_target(self, commodity: Commodity, starting_point: System, buy: bool) -> System:
        """
        Inner function for source and sell
        :param commodity: Commodity object
        :param starting_point: System object
        :param buy: True if source, False if sell
        :return: System object
        """
        pass

    def source(self, commodity, starting_point) -> (Station, int):
        """
        returns a system object with the best distance to price ratio to buy
        :param commodity: a Commodity object or name
        :param starting_point: a System object or name
        :return: Station object to buy at and price
        """
        pass

    def sell(self, commodity, starting_point) -> (Station, int):
        """
        returns a system object with the best distance to price ratio to sell
        :param commodity: a Commodity object or name
        :param starting_point: a System object or name
        :return: Station object to sell at and price
        """


    def carry_on(self, starting_point_system, starting_point_station, target_point_system, target_point_station) -> (Commodity, int):
        """
        Suggest a commodity to take with you on a journey
        :param starting_point: System object or name
        :param target_point:  System object or name
        :return: Commodity object and profit
        """
        if not isinstance(starting_point_system, System):  # todo: move those str checks to a function
            starting_point_system = self.__populate_system(starting_point_system)
        if not isinstance(starting_point_station, Station):
            starting_point_station = self.__populate_station(starting_point_station, system=starting_point_system)
        if not isinstance(target_point_system, System):
            target_point_system = self.__populate_system(target_point_system)
        if not isinstance(target_point_station, Station):
            target_point_station = self.__populate_station(target_point_station, system=target_point_system)

        return target_point_station-starting_point_station