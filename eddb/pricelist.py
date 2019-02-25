from time import time
from eddb import eddb_prime
from eddb.commodity import Commodities
from eddb.progress_tracker import generate_bar
commodity_controller = Commodities()
this_api = 'listings.csv'

def listing_loader(refs: list):  # refs are expected to be station ids (!)
    eddb_prime.recache(this_api)
    gen = eddb_prime.read_iter(this_api)
    header = gen.__next__().split(',')
    header = [q.strip() for q in header]
    # recreate list into a weird dict
    listing_dict = dict()
    for ref_dict in refs:
        listing_dict[ref_dict] = list()

    bar = generate_bar(gen.size, 'Parsing listings')
    bar.start()
    for line in gen:
        bar.update(bar.value+line.encode('utf-8').__len__())
        sp = line.split(',')
        sp = [q.strip() for q in sp]
        if int(sp[header.index('station_id')]) in listing_dict.keys():
            ref_dict = dict()

            for h in header:
                ref_dict[h] = sp[header.index(h)]
            listing_dict[int(sp[header.index('station_id')])].append(ref_dict)

    bar.finish()

    bar = generate_bar(listing_dict.keys().__len__(), 'Creating stations')
    bar.start()
    ret_list = list()
    for k in listing_dict:
        bar.update(bar.value + 1)
        listing = StationPriceList(k)
        listing._populate(listing_dict[k])
        ret_list.append(listing)
    bar.finish()
    return ret_list


class Commodity:
    def __init__(self, commodity_id, supply, buy_price, sell_price, demand, collected_at, **kwargs):
        self.cid = int(commodity_id)
        self.supply = int(supply)
        self.buy = int(buy_price)
        self.sell = int(sell_price)
        self.demand = int(demand)
        self.timestamp = int(collected_at)
        self.name = commodity_controller.get_name_by_id(self.cid)

    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return '<NONE>' if self.name is None else self.name

    def __sub__(self, other):  # minus stands for difference between "sell there, buy here"
        return other.sell - self.buy


class StationPriceList:
    def __init__(self, station):
        self.station = station
        self.listings = []

    def _populate(self, listing: list):
        self.listings = []
        for comm in listing:
            self.listings.append(Commodity(**comm))

    def populate(self):
        gen = eddb_prime.read_iter(this_api)
        header = gen.__next__().split(',')
        header = [q.strip() for q in header]
        # recreate list into a weird dict
        listings = []
        bar = generate_bar(gen.size, 'Parsing listings')
        bar.start()
        for line in gen:
            bar.update(bar.value + line.encode('utf-8').__len__())
            sp = line.split(',')
            sp = [q.strip() for q in sp]
            if int(sp[header.index('station_id')]) == self.station:
                ref_dict = dict()
                for h in header:
                    ref_dict[h] = sp[header.index(h)]
                listings.append(ref_dict)
        bar.finish()
        self._populate(listings)  # just one station


    def get_commodity(self, cid):
        for cm in self.listings:
            if cm.cid == cid:
                return cm
        return None

    def __sub__(self, other):
        if other is None:
            return None, 0
        current_best = None
        max_diff = 0
        for cm in self.listings:
            if not commodity_controller.is_marketable(cm.cid) or not commodity_controller.buyable(cm.cid) or not commodity_controller.sellable(cm.cid):
                continue
            ref = other.get_commodity(cm.cid)
            if ref is not None and cm.supply > 0 and ref.demand > 0:
                if max_diff < cm - ref:
                    current_best = cm
                    max_diff = cm - ref
        return current_best, max_diff

    def updated(self):
        updates = [(time() - q.timestamp)/60/60 for q in self.listings]
        return sum(updates)/updates.__len__()

    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return f'StationPriceList<{self.station}>'


class CommodityPriceList:
    pass  # todo: implement one commodity matching per commodity and not per station

if __name__ == '__main__':
    test = listing_loader([1, 3])
    commodity, best_price = test[1]-test[0]
    print(commodity.name, best_price)