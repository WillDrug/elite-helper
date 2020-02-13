from .ORM import *
from .logger import EliteLogger
from . import settings

class Trader:
    def __init__(self, ship_size=None, max_distance=None, requires_permit=False):
        self.l = EliteLogger('Trader')
        self.ship_size = ship_size
        self.max_distance = max_distance
        self.requires_permit = requires_permit

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

    def carry_on(self, starting_point, target_point) -> (Commodity, int):
        """
        Suggest a commodity to take with you on a journey
        :param starting_point: System object or name
        :param target_point:  System object or name
        :return: Commodity object and profit
        """
