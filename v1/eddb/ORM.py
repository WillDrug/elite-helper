from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Integer, Float, create_engine, ForeignKey, Boolean
from . import settings

engine = create_engine(settings.get('engine'))
Session = sessionmaker(bind=engine)
connection = engine.connect()
Base = declarative_base()

class Cache(Base):
    __tablename__ = 'cache'

    name = Column(String, primary_key=True)
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
        return f'<Commodity(name={self.name}, top_profit={self.max_sell_price-self.min_buy_price})>'

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

# Additional Systems tables
class Government(Base):
    __tablename__ = 'government'

    id = Column(Integer, primary_key=True)
    name = Column(String)

class Allegiance(Base):
    __tablename__ = 'allegiance'

    id = Column(Integer, primary_key=True)
    name = Column(String)

class Security(Base):
    __tablename__ = 'security'

    id = Column(Integer, primary_key=True)
    name = Column(String)

class Economy(Base):
    __tablename__ = 'economy'

    id = Column(Integer, primary_key=True)
    name = Column(String)

class Powerstate(Base):
    __tablename__ = 'powerstate'

    id = Column(Integer, primary_key=True)
    name = Column(String)

class Faction(Base):
    __tablename__ = 'faction'

    id = Column(Integer, primary_key=True)
    name = Column(String)

class Reserve(Base):
    __tablename__ = 'reserve'

    id = Column(Integer, primary_key=True)
    name = Column(String)

class Module(Base):
    __tablename__ = 'module'

    id = Column(Integer, primary_key=True)  # fixme: populate
    name = Column(String)

class StationModules(Base):
    __tablename__ = 'stationmodules'

    station_id = Column(Integer, ForeignKey('station.id'), primary_key=True)
    module_id = Column(Integer, ForeignKey('module.id'), primary_key=True)

class StationEconomies(Base):
    __tablename__ = 'stationeconomies'

    station_id = Column(Integer, ForeignKey('station.id'), primary_key=True)
    economy_id = Column(Integer, ForeignKey('economy.id'), primary_key=True)

class State(Base):
    __tablename__ = 'state'

    id = Column(Integer, primary_key=True)
    name = Column(String)

class StationState(Base):
    __tablename__ = 'stationstate'

    station_id = Column(Integer, ForeignKey('station.id'), primary_key=True)
    state_id = Column(Integer, ForeignKey('state.id'), primary_key=True)

class Type(Base):
    __tablename__ = 'type'

    id = Column(Integer, primary_key=True)
    name = Column(String)

class Body(Base):
    __tablename__ = 'body'

    id = Column(Integer, primary_key=True)
    name = Column(String)

class StationCommodities(Base):
    __tablename__ = 'stationcommodities'

    station_id = Column(Integer, ForeignKey('station.id'), primary_key=True)
    commodity_id = Column(Integer, ForeignKey('commodity.id'), primary_key=True)
    usage = Column(Integer, primary_key=True)  # -1 prohibited, 0 import, 1 export

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
    export_commodities = Column(String)      # stringified list. fixme: dict
    import_commodities = Column(String)      # stringified list. fixme: dict
    prohibited_commodities = Column(String)  # stringified list. fixme: dict
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


Base.metadata.create_all(engine)
