from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Integer, create_engine, ForeignKey, Boolean

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

class Station(Base):
    __tablename__ = 'station'

    id = Column(Integer, primary_key=True)

Base.metadata.create_all(engine)

