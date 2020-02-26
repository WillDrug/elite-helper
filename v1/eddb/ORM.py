from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, aliased
from sqlalchemy import Column, String, Integer, Float, create_engine, ForeignKey, Boolean
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy import func, select

from . import settings
from math import sqrt
from statistics import mean

from sqlalchemy.event import listens_for
from sqlalchemy.pool import Pool

@listens_for(Pool, "connect")
def on_connect_add_func(dbapi_con, connection_record):
    dbapi_con.create_function('SQRT', 1, sqrt)
    dbapi_con.create_function('POW', 2, pow)



class LandingPad:
    def __init__(self, size):
        self.size = size
        if self.size == 'None':
            self.size_num = 0
        elif self.size == 'M':
            self.size_num = 1
        elif self.size == 'L':
            self.size_num = 2
        elif size is None:
            self.size_num = -1
        elif size == '':  # unknown, presuming small only
            self.size_num = 0
        else:
            raise ValueError(size)

    def __gt__(self, other):
        return self.size_num >= other.size_num

    def __eq__(self, other):
        return self.size_num == other.size_num

    def __lt__(self, other):
        return self.size_num <= other.size_num

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __repr__(self):
        return f'{self.size}({self.size_num})'

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

    @classmethod
    def get_marketable_dict(cls):
        ret = cls.get_marketable()
        return {q.id: q for q in ret}

    @classmethod
    def get_rares(cls):
        s = Session()
        ret = s.query(cls).filter(cls.is_rare == True).all()
        s.close()
        return ret

class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f'<Category(name={self.name})>'

class Listing(Base):
    cached = False

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

    @hybrid_property
    def buyable(self):
        return self.buy_price > 0

    @buyable.expression
    def buyable(self):
        return self.buy_price > 0

    @hybrid_property
    def sellable(self):
        return self.sell_price > 0

    @sellable.expression
    def sellable(self):
        return self.sell_price > 0

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

    @classmethod
    def average_sell_count(cls):
        if cls.cached:
            return cls.asc
        s = Session()
        cls.asc = s.query(func.avg(s.query(func.count(cls.station_id)).group_by(cls.station_id))).scalar()
        s.close()
        cls.cached = True
        return cls.asc

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
        return abs(sqrt(pow(other.x-self.x, 2) + pow(other.y-self.y, 2) + pow(other.z-self.z, 2)))

    @distance.expression
    def distance(cls, other):
        return func.abs(func.sqrt(func.pow(other.x-cls.x,2)+func.pow(other.y-cls.y,2)+func.pow(other.z-cls.z,2)))

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

    @classmethod
    def get_types(cls):
        s = Session()
        types = s.query(cls).all()
        s.close()
        return types

    @classmethod
    def check_type(cls, t):
        s = Session()
        t2 = s.query(cls).filter(cls.name == t).first()
        s.close()
        if t2 is not None:
            return True
        else:
            return False

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
    listings = relationship(Listing, lazy='dynamic')


    @hybrid_method
    def pad_accessible(self, size):
        return LandingPad(self.max_landing_pad_size) <= LandingPad(size)

    @pad_accessible.expression
    def pad_accessible(cls, size):
        return size == 'None' or size is None or (cls.max_landing_pad_size == 'M' and size in ['M', 'L']) or (cls.max_landing_pad_size == 'L' and size == 'L')

    def __repr__(self):
        return f'<Station(name={self.name})>'

    def __sub__(self, other):
        if not self.has_market or not other.has_market:
            return None, 0

        s = Session()
        listing_buy = s.query(Listing).filter(Listing.station_id == other.id).filter(Listing.commodity_id.in_([q.id for q in Commodity.get_marketable()])).filter(Listing.buyable).all()
        listing_sell = s.query(Listing).filter(Listing.station_id == self.id).filter(Listing.commodity_id.in_([q.commodity_id for q in listing_buy])).filter(Listing.sellable).all()
        listing_buy = [q for q in listing_buy if q.commodity_id in [z.commodity_id for z in listing_sell]]

        listing_sell.sort(key=lambda x: x.commodity_id)
        listing_buy.sort(key=lambda x: x.commodity_id)

        price = 0
        commodity = None
        for buy, sell in zip(listing_buy, listing_sell):
            temprice = sell.get_sell_price()-buy.get_buy_price()
            if temprice > price:
                price = temprice
                commodity = buy.commodity_id

        if commodity is not None:
            commodity = s.query(Commodity).filter(Commodity.id == commodity).first()
        return commodity, price

    @hybrid_property
    def sell_count(self):
        return self.listings.count()

    @sell_count.expression
    def sell_count(cls):
        nl = aliased(Listing)
        st = aliased(cls)
        return (select([func.count(nl.id)]).
                where(nl.station_id == st.id).
                label("child_count")
                )

Base.metadata.create_all(engine)
