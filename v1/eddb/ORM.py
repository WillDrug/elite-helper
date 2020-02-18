from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Integer, Float, create_engine, ForeignKey, Boolean
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from . import settings

from math import sqrt

engine = create_engine(settings.get('engine'))
Session = sessionmaker(bind=engine)
connection = engine.connect()
Base = declarative_base()

class Cache(Base):
    __tablename__ = 'cache'

    name = Column(String, primary_key=True)
    loaded = Column(Integer)
    cached = Column(Integer)

    def __repr__(self):
        return f'<API({self.name}, {self.cached})>'


class Commodity(Base):
    __tablename__ = 'commodity'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    category_id = Column(Integer, ForeignKey('category.id'))  # fixme CASCADE this shit
    average_price = Column(Integer)
    is_rare = Column(Boolean)
    max_buy_price = Column(Integer)
    max_sell_price = Column(Integer)
    min_buy_price = Column(Integer)
    min_sell_price = Column(Integer)
    buy_price_lower_average = Column(Integer)
    sell_price_upper_average = Column(Integer)
    is_non_marketable = Column(Boolean)
    ed_id = Column(Integer)

    def __repr__(self):
        if self.max_sell_price is None or self.min_buy_price is None:
            return f'<Commodity(name={self.name}, marketable={not self.is_non_marketable}, sellable={True if self.max_sell_price is not None else False}, buyable={True if self.min_buy_price is not None else False})>'
        else:
            return f'<Commodity(name={self.name}, top_profit={self.max_sell_price-self.min_buy_price})>'

    @classmethod
    def get_marketable(cls):
        s = Session()
        ret = s.query(cls).filter(cls.is_non_marketable == False).filter(cls.max_sell_price.isnot(None)).filter(cls.min_buy_price.isnot(None)).all()
        s.close()
        return ret

class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f'<Category(name={self.name})>'

class Listing(Base):
    __tablename__ = 'listing'
    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey('station.id'))
    commodity_id = Column(Integer, ForeignKey('commodity.id'))
    supply = Column(Integer)
    supply_bracket = Column(Integer)  # what's that
    buy_price = Column(Integer)
    sell_price = Column(Integer)
    demand = Column(Integer)
    demand_bracket = Column(Integer)
    collected_at = Column(Integer)

    def __repr__(self):
        return f'<Listing(id={self.id}, station={self.station_id})>'

    def get_buy_price(self):
        if self.buy_price == 0:
            return None
        else:
            return self.buy_price

    def get_sell_price(self):
        if self.sell_price == 0:
            return None
        else:
            return self.sell_price

class System(Base):
    __tablename__ = 'system'

    id = Column(Integer, primary_key=True)
    edsm_id = Column(Integer)
    name = Column(String)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)
    population = Column(Integer)
    is_populated = Column(Boolean)
    government_id = Column(Integer, ForeignKey('government.id'))
    allegiance_id = Column(Integer, ForeignKey('allegiance.id'))
    security_id = Column(Integer, ForeignKey('security.id'))
    primary_economy_id = Column(Integer, ForeignKey('economy.id'))
    power = Column(String)
    power_state_id = Column(Integer, ForeignKey('powerstate.id'))
    needs_permit = Column(Boolean)
    updated_at = Column(Integer)
    simbad_ref = Column(Integer)
    controlling_minor_faction_id = Column(Integer, ForeignKey('faction.id'))
    reserve_type_id = Column(Integer, ForeignKey('reserve.id'))

    @hybrid_method
    def distance(self, other):
        """ABS(
            SQRT(
                (x1 - x0) ^ 2 +
                (y1 - y0) ^ 2 +
                (z1 - z0) ^ 2
            )
        )"""
        return abs(sqrt(pow(other.x - self.x, 2) + pow(other.y - self.y, 2) + pow(other.z - self.z, 2)))

    def __eq__(self, other):
        return self.id == other.id

    def __sub__(self, other):
        return abs(sqrt(pow(self.x-other.x, 2) + pow(self.y-other.y, 2) + pow(self.z-other.z, 2)))

    def __repr__(self):
        return f'<System(name={self.name})>'

# Additional Systems tables
class Government(Base):
    __tablename__ = 'government'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f'<Government(name={self.name})>'

class Allegiance(Base):
    __tablename__ = 'allegiance'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f'<Allegiance(name={self.name})>'

class Security(Base):
    __tablename__ = 'security'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f'<Security(name={self.name})>'

class Economy(Base):
    __tablename__ = 'economy'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f'<Economy(name={self.name})>'

class Powerstate(Base):
    __tablename__ = 'powerstate'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f'<Powerstate(name={self.name})>'

class Faction(Base):
    __tablename__ = 'faction'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f'<Faction(name={self.name})>'

class Reserve(Base):
    __tablename__ = 'reserve'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f'<Reserve(name={self.name})>'

class Module(Base):
    __tablename__ = 'module'

    id = Column(Integer, primary_key=True)  # fixme: populate
    name = Column(String)

    def __repr__(self):
        return f'<Module(name={self.name})>'

class StationModules(Base):
    __tablename__ = 'stationmodules'

    station_id = Column(Integer, ForeignKey('station.id'), primary_key=True)
    module_id = Column(Integer, ForeignKey('module.id'), primary_key=True)

    def __repr__(self):
        return f'<StationModules(station={self.station_id}, module={self.module_id})>'

class StationEconomies(Base):
    __tablename__ = 'stationeconomies'

    station_id = Column(Integer, ForeignKey('station.id'), primary_key=True)
    economy_id = Column(Integer, ForeignKey('economy.id'), primary_key=True)

    def __repr__(self):
        return f'<StationEconomies(name={self.station_id}, economy={self.economy_id})>'

class State(Base):
    __tablename__ = 'state'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f'<State(name={self.name})>'

class StationState(Base):
    __tablename__ = 'stationstate'

    station_id = Column(Integer, ForeignKey('station.id'), primary_key=True)
    state_id = Column(Integer, ForeignKey('state.id'), primary_key=True)

    def __repr__(self):
        return f'<Government(station={self.station_id}, state_id={self.state_id})>'

class Type(Base):
    __tablename__ = 'type'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f'<Type(name={self.name})>'

class Body(Base):
    __tablename__ = 'body'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f'<Body(name={self.name})>'

class StationCommodities(Base):
    __tablename__ = 'stationcommodities'

    station_id = Column(Integer, ForeignKey('station.id'), primary_key=True)
    commodity_id = Column(Integer, ForeignKey('commodity.id'), primary_key=True)
    usage = Column(Integer, primary_key=True)  # -1 prohibited, 0 import, 1 export

    def __repr__(self):
        return f'<StationCommodities(station_id={self.station_id}, commodity={self.commodity_id}, usage={self.usage})>'

class StationShips(Base):
    __tablename__ = 'stationships'

    station_id = Column(Integer, primary_key=True)
    name = Column(String, primary_key=True)

    def __repr__(self):
        return f'<StationShips(station_id={self.station_id}, name={self.name})>'

class Station(Base):
    __tablename__ = 'station'

    id = Column(Integer, primary_key=True)
    system_id = Column(Integer, ForeignKey('system.id'))
    government_id = Column(Integer, ForeignKey('government.id'))
    settlement_size = Column(String)
    shipyard_updated_at = Column(Integer)
    market_updated_at = Column(Integer)
    updated_at = Column(Integer)
    allegiance_id = Column(Integer, ForeignKey('allegiance.id'))
    has_rearm = Column(Boolean)
    settlement_security_id = Column(Integer, ForeignKey('security.id'))
    max_landing_pad_size = Column(String)
    has_commodities = Column(Boolean)
    has_repair = Column(Boolean)
    name = Column(String)
    selling_ships = Column(String)  # stringified list. fixme: dict
    has_outfitting = Column(Boolean)
    has_blackmarket = Column(Boolean)
    has_refuel = Column(Boolean)
    type_id = Column(Integer, ForeignKey('type.id'))
    has_market = Column(Boolean)
    controlling_minor_faction_id = Column(Integer, ForeignKey('faction.id'))
    is_planetary = Column(Boolean)
    outfitting_updated_at = Column(Integer)
    has_docking = Column(Boolean)
    body_id = Column(Integer, ForeignKey('body.id'))
    has_shipyard = Column(Boolean)
    distance_to_star = Column(Integer)

    def __repr__(self):
        return f'<Station(name={self.name})>'

    def __sub__(self, other):
        if not self.has_market or not other.has_market:
            return None, 0

        s = Session()
        prices = s.query(Listing).filter(Listing.station_id.in_([self.id, other.id])).filter(Listing.commodity_id.in_([q.id for q in Commodity.get_marketable()])).all()
        to_delete = list()
        for p in prices:
            if (p.station_id == self.id and p.get_buy_price() is None) or (p.station_id == other.id and p.get_sell_price() is None):
                to_delete.append(p.commodity_id)
        compare = {}
        for p in prices:
            if p.commodity_id in to_delete:
                continue
            if p.commodity_id not in compare.keys():
                compare[p.commodity_id] = 0
            if p.station_id == self.id:
                compare[p.commodity_id] -= p.get_buy_price()
            if p.station_id == other.id:
                compare[p.commodity_id] += p.get_sell_price()
        price = 0
        commodity = None
        for com in compare:
            if compare[com] > price:
                price = compare[com]
                commodity = com

        if commodity is not None:
            commodity = s.query(Commodity).filter(Commodity.id == commodity).first()
            if commodity is not None:
                commodity = commodity.name

        return commodity, price
Base.metadata.create_all(engine)
