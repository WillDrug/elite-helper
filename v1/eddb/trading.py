from .ORM import *
from .logger import EliteLogger
from . import settings

class TooManyResults(Exception):
    pass


class Trader:
    def __init__(self, ship_size=None, max_distance=None, requires_permit=False):
        self.l = EliteLogger('Trader', level=settings.get('log_level'))
        self.ship_size = ship_size
        self.max_distance = max_distance
        self.requires_permit = requires_permit

    def __clean(self, orm, instance, attr):
        if not isinstance(instance, orm):
            return self.__pop_single(orm, attr, instance)
        else:
            return instance

    def __pop_single(self, orm, attr, val):
        return self.__pop(orm, [(orm, attr, val, 0)])

    def __pop(self, orm_cls, query):  # is this really necessary?
        s = Session()
        sub = s.query(orm_cls)
        for orm, attr, val, compare in query:
            if compare == 0:
                compare = getattr(orm, attr).__eq__
            elif compare == -1:
                compare = getattr(orm, attr).__lte__
            elif compare == -2:
                compare = getattr(orm, attr).__lt__
            elif compare == 1:
                compare = getattr(orm, attr).__gte__
            elif compare == 2:
                compare = getattr(orm, attr).__gt__
            sub = sub.filter(compare(val))

        ret = sub.all()
        if ret.__len__() > 1:
            raise TooManyResults(f'Got too many of {orm_cls} for a query. SPECIFY.')
        if ret.__len__() == 0:
            return None
        return ret[0]

    def __populate_commodity(self, commodity_name):
        return self.__pop_single(Commodity, 'name', commodity_name)

    def __populate_system(self, system_name):
        return self.__pop_single(System, 'name', system_name)


    def __populate_station(self, station_name, system=None):
        if system is not None:
            return self.__pop(Station, [(Station, 'system_id', system.id, 0), (Station, 'name', station_name, 0)])
        else:
            return self.__pop_single(Station, 'name', station_name)

    def __find_trading_target(self, commodity: Commodity, starting_point: System, buy: bool) -> System:
        """
        Inner function for source and sell
        :param commodity: Commodity object
        :param starting_point: System object
        :param buy: True if source, False if sell
        :return: System object
        """
        pass

    def source(self, starting_point, commodity, price_limit_index=1.0, distance_limit=None) -> (Station, int):
        """
        returns a system object with the best distance to price ratio to buy
        :param commodity: a Commodity object or name
        :param starting_point: a System object or name
        :return: Station object to buy at and price
        """
        starting_point = self.__clean(System, starting_point, 'name')
        commodity = self.__clean(Commodity, commodity, 'name')
        if starting_point is None or commodity is None:
            return None, None

        price = commodity.average_price*price_limit_index
        s = Session()
        applicable = s.query(Listing).filter(Listing.commodity_id == commodity.id).filter(Listing.buy_price < price).all()
        sub = s.query(Station).join(System).filter(Station.id.in_([q.id for q in applicable]))
        if distance_limit is not None:
            sub = sub.filter(System.distance(starting_point) < distance_limit)

        sub = sub.order_by(System.distance(starting_point))
        return sub.first()



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