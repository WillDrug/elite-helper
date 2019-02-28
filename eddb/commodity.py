import requests
from eddb import eddb_prime

import json
this_api = 'commodities.json'
class Commodities:
    def __init__(self):
        eddb_prime.recache(this_api)
        self.reference = []
        self.populate()

    def populate(self):
        for entry in json.loads(eddb_prime.read('commodities.json')):  # TODO: refine to use collections and
            commodity = {}
            commodity['name'] = entry.get('name')
            commodity['msp'] = entry.get('max_sell_price')
            commodity['mbp'] = entry.get('min_buy_price')
            commodity['id'] = entry.get('id')
            commodity['is_marketable'] = True if entry.get('is_non_marketable') == 0 else False
            commodity['is_rare'] = True if entry.get('is_rare', 0) == 1 else False
            self.reference.append(commodity)

    def buyable(self, cid):
        ref = self.get_by_id(cid)
        if ref is None:
            return None
        return True if ref['mbp'] is not None else False

    def sellable(self, cid):
        ref = self.get_by_id(cid)
        if ref is None:
            return None
        return True if ref['msp'] is not None else False

    def commodities(self, marketable_only=True):
        if marketable_only:
            return [commodity for commodity in self.reference if commodity.get('is_marketable', False)]
        else:
            return [commodity for commodity in self.reference]

    def get_by_name(self, name):
        for ref in self.reference:
            if ref['name'] == name:
                return ref

        return None

    def get_by_id(self, cid):
        for ref in self.reference:
            if ref['id'] == cid:
                return ref
        return None

    def get_name_by_id(self, cid):
        ref = self.get_by_id(cid)
        return None if ref is None else ref['name']

    def is_marketable(self, cid):
        ref = self.get_by_id(cid)
        return None if ref is None else ref['is_marketable']


if __name__ == '__main__':
    comm = Commodities()
    print(comm.commodities())
    print(comm.get_name_by_id(1))
    print(comm.get_by_name('Galactic Travel Guides'))