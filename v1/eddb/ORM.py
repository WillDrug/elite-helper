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

class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String)


Base.metadata.create_all(engine)

