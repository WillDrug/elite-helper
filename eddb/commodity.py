import requests
from . import EDDB

import json

class Commodities:
    def __init__(self, eddb: EDDB):
        self.eddb = eddb
        self.eddb.recache()
        self.reference = []
        self.populate()

    def populate(self):
        for entry in json.loads(self.eddb.read('commodities.json')):  # TODO: refine to use collections and
            commodity = {}
            commodity['msp'] = entry.get('max_sell_price')
            commodity['mbp'] = entry.get('min_buy_price')
            commodity['id'] = entry.get('id')
            commodity['is_marketable'] = True if entry.get('is_non_marketable') == 0 else False
            self.reference.append(commodity)

    def commodities(self, marketable_only=True):
        if marketable_only:
            return [commodity for commodity in self.reference if commodity.get('is_marketable', False)]
        else:
            return [commodity for commodity in self.reference]