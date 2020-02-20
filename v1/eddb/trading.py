from .ORM import *
from .logger import EliteLogger
from . import settings

# todo: annotate and specify types

class TooManyResults(Exception):
    pass

class Trader:
    def __init__(self, ship_size=None, requires_permit=False, distance_from_star=-1):
        self.l = EliteLogger('Trader', level=settings.get('log_level'))
        self.ship_size = ship_size
        self.requires_permit = requires_permit
        self.distance_from_star = distance_from_star

    def generate_response(self, source_station=None, target_station=None, commodity=None, source_system=None, target_system=None):
        """
        Helper function to return a common object for all trade functions
        :param source_station: Station object
        :param target_station: Station object or None
        :param commodity: Commodity object or None
        :param source_system: System object or None
        :param target_system: System object or None
        :return:
        """
        self.l.debug('Generating response')

        if source_system is None and source_station is not None:
            source_system = self.__pop_single(System, 'id', source_station.system_id)
        if target_system is None and target_station is not None:
            target_system = self.__pop_single(System, 'id', target_station.system_id)

        profit = None

        if commodity is None and target_station is not None and source_station is not None:
            commodity = target_station - source_station
            commodity, profit = commodity


        return {
            'source': {
                'system': source_system,
                'station': source_station
            },
            'target': {
                'system': target_system,
                'station': target_station
            },
            'trade': {
                'type': 'source' if target_station is None else 'sell' if source_station is None else 'trade',
                'commodity': commodity,
                'distance': None if source_system is None or target_system is None else target_system-source_system,
                'buy': None if commodity is None or source_station is None else self.__get_listing(source_station, commodity).buy_price,  # todo: pre-load if possible
                'sell': None if commodity is None or target_station is None else self.__get_listing(target_station, commodity).sell_price,
                'profit': profit if profit is not None else self.__get_profit(source_station, target_station, commodity) if source_station is not None and target_station is not None and commodity is not None else None
            }
        }

    def __apply_common_filters(self, query):
        return self.__apply_station_filter(self.__apply_system_filter(query))

    def __apply_system_filter(self, query):
        if not self.requires_permit:
            query = query.filter(System.needs_permit == False)
        return query

    def __apply_station_filter(self, query):
        if self.distance_from_star > -1:
            query = query.filter(Station.distance_to_star < self.distance_from_star)

        if self.ship_size is not None:
            query = query.filter(Station.max_landing_pad_size == self.ship_size)

        return query


    def __get_profit(self, source_station, target_station, commodity):
        """
        Function presumes that all checks are passed for a commodity: source station has supply, target_station has demand.
        Presumes buy_price is not 0, sell price is not 0
        :param source_station: Station object
        :param target_station: Station object
        :param commodity: Commodity object
        :return: int
        """
        self.l.debug(f'Calculating profit from {source_station} to {target_station} for {commodity}')
        buy_price = self.__get_listing(source_station, commodity).buy_price
        sell_price = self.__get_listing(target_station, commodity).sell_price
        return sell_price-buy_price

    def __get_listing(self, station, commodity):
        self.l.debug(f'Getting {commodity} listing for {station}')
        s = Session()
        listing = s.query(Listing).filter(Listing.station_id == station.id).filter(Listing.commodity_id == commodity.id).first()
        s.close()
        return listing

    def __check(self, orm, instance):
        return isinstance(instance, orm)

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
        return commodity_name if self.__check(Commodity, commodity_name) else self.__pop_single(Commodity, 'name', commodity_name)

    def __populate_system(self, system_name):
        return system_name if self.__check(System, system_name) else self.__pop_single(System, 'name', system_name)

    def __populate_station(self, station_name, system=None):
        if self.__check(Station, station_name):
            return station_name
        if system is not None:
            return self.__pop(Station, [(Station, 'system_id', system.id, 0), (Station, 'name', station_name, 0)])
        else:
            return self.__pop_single(Station, 'name', station_name)

    def __find_trading_target(self, commodity: Commodity, starting_point: System, buy: bool,
                              distance_limit=None, choices=1, price_limit_index=None):
        """
        Inner function for source and sell
        :param commodity: Commodity object
        :param starting_point: System object
        :param buy: True if source, False if sell
        :return: List of Trader.generate_response()
        """
        self.l.info(f'Looking up a trading target to {"buy" if buy else "sell"} {commodity} starting at {starting_point}')
        s = Session()

        sub = s.query(Station).join(System).join(Listing).filter(Listing.commodity_id == commodity.id)
        sub = self.__apply_common_filters(sub)
        if price_limit_index is not None:
            if buy:
                price_point = commodity.min_buy_price + (commodity.min_buy_price * (1-float(price_limit_index)))
                self.l.debug(f'Limiting price to {price_point}')
                sub = sub.filter(Listing.buyable == True).filter(Listing.buy_price < price_point)
            else:
                price_point = commodity.max_sell_price * float(price_limit_index)
                self.l.debug(f'Limiting price to {price_point}')
                sub = sub.filter(Listing.sellable == True).filter(Listing.sell_price > price_point)

        if distance_limit is not None:
            sub = sub.filter(System.distance(starting_point) < distance_limit)

        if buy:
            sub = sub.order_by(System.distance(starting_point).asc(), Listing.buy_price.asc())
        else:
            sub = sub.order_by(System.distance(starting_point).asc(), Listing.sell_price.desc())

        return sub.limit(choices).all()

    def source(self, starting_point, commodity, price_limit_index=1.0, distance_limit=None, choices=1) -> (Station, int):
        """
        returns a system object with the best distance to price ratio to buy
        :param commodity: a Commodity object or name
        :param starting_point: a System object or name
        :return: Station object to buy at and price
        """
        self.l.info(f'Looking to source {commodity} from {starting_point}')

        commodity = self.__populate_commodity(commodity)
        starting_point = self.__populate_system(starting_point)
        if commodity is None or starting_point is None:
            return self.generate_response()
        possible = self.__find_trading_target(commodity, starting_point, True, price_limit_index=price_limit_index,
                                              distance_limit=distance_limit, choices=choices)

        return [self.generate_response(source_station=q, commodity=commodity, target_system=starting_point) for q in possible]



    def sell(self, starting_point, commodity, distance_limit=None, choices=1, price_limit_index=None):
        """
        returns a system object with the best distance to price ratio to sell
        :param commodity: a Commodity object or name
        :param starting_point: a System object or name
        :return: Station object to sell at and price
        """
        self.l.info(f'Looking to sell {commodity} from {starting_point}')

        commodity = self.__populate_commodity(commodity)
        starting_point = self.__populate_system(starting_point)
        possible = self.__find_trading_target(commodity, starting_point, False, distance_limit=distance_limit,
                                              price_limit_index=price_limit_index, choices=choices)
        return [self.generate_response(target_station=q, source_system=starting_point, commodity=commodity) for q in possible]


    def carry_on(self, starting_point_system, starting_point_station, target_point_system, target_point_station=None):
        """
        Suggest a commodity to take with you on a journey
        :param starting_point: System object or name
        :param target_point:  System object or name
        :return: Commodity object and profit
        """
        self.l.info(f'Calculating carry-on from {starting_point_system} to {target_point_system}')
        # todo: move systems to additional parameters and raise TooManyResults if needed
        starting_point_system = self.__populate_system(starting_point_system)
        starting_point_station = self.__populate_station(starting_point_station, system=starting_point_system)
        target_point_system = self.__populate_system(target_point_system)
        if target_point_station is None:
            self.l.info('Target point has no station, finding best')
            s = Session()
            stations = self.__apply_station_filter(s.query(Station).filter(Station.system_id == target_point_system.id)).all()
            s.close()
            if stations.__len__() == 0:
                self.l.warning('No stations in that system')
                return self.generate_response()
            best_station = None
            best_profit = 0
            for station in stations:
                _, profit = station-starting_point_station
                if profit > best_profit:
                    best_profit = profit
                    best_station = station
            target_point_station = best_station
        else:
            target_point_station = self.__populate_station(target_point_station, system=target_point_system)


        return self.generate_response(source_system=starting_point_system, source_station=starting_point_station,
                                      target_system=target_point_system, target_station=target_point_station)