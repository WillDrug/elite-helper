import itertools
from threading import Thread
import pickle
import argparse
import sys, os
from rares import RareLoader, RareGraph, RareNode
from time import time, sleep
from terminaltables import AsciiTable
from eddb.commodity import Commodities
from eddb.system import System
from eddb.station import Station
import logging

import subprocess as sp

class AsciiControl:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ENDC = '\033[0m'

l = logging.getLogger('Helper')
l.handlers = []
l.addHandler(logging.StreamHandler(stream=sys.stdout))
l.setLevel(logging.DEBUG)

from eddi import EDDI
di = EDDI()

# load up current inventory:

class Context:
    def __init__(self, s='L', d=50000, f=True, **kwargs):
        self.rare_controller = RareLoader()
        self.rare_controller.init(ship_size=s, max_distance_from_star=d, filter_needs_permit=f)
        self.current = {'system': None, 'station': None, 'node': None, 'rare_commodity': None}
        self.route = []
        self.cargo = dict()
        self.generated_route = []  # todo: generate route
        self.profit = 0

        self.commodity_controller = Commodities()


    def docked(self, system, station):
        node = self.rare_controller.query(system, station)
        if node is not None:
            system_o = node.system
            station_o = node.station
        else:
            system_o = System(name=system)
            system_o.populate()
            station_o = Station(name=station)
            station_o.populate(system_id=system_o.id)
        if self.generated_route is None:
            self.generated_route = self.rare_controller.generate(system_o, station_o, node=node)  # add route generation
        self.current = {
            'system': system_o,
            'station': station_o,
            'node': node,
            'rare_commodity': None
        }
        self.route.append(self.current)
        self.proposed = self.rare_controller.alternative_determine_next(self.current['system'], self.current['station'])

    def buy(self, commodity_name, amount):
        test = self.commodity_controller.get_by_name(commodity_name)
        if test is None and self.current['node'] is not None:
            self.current['rare_commodity'] = commodity_name

        if commodity_name not in self.cargo.keys():
            self.cargo[commodity_name] = amount
        else:
            self.cargo[commodity_name] += amount


    def sell(self, commodity_name, amount, profit):
        if commodity_name in self.cargo.keys():
            commodity_name['amount'] -= amount
        self.profit += profit


    def draw(self):
        os.system('cls')
        header_table_data = [['System', 'Station', 'Node', 'Buy Rare', 'Profit'],
                             [self.current['system'], self.current['station'], self.current['node'],
                              None if self.current['node'] is None else self.current['node'].name, self.profit]]
        header_table_data[0] = [AsciiControl.HEADER+q+AsciiControl.ENDC for q in header_table_data[0]]
        header_table = AsciiTable(header_table_data)
        print(header_table.table)

        info_table = [['Cargo', 'Route', 'Pre-generated route', 'Proposed Jumps']]
        info_table[0] = [AsciiControl.HEADER + q + AsciiControl.ENDC for q in info_table[0]]




    def run(self):
        self.draw()

    def __listener(self):
        for update in di.update_generator():
            update = update.strip().split(';')
            # switch event
            if update[0] == 'docked':
                self.docked(update[1], update[2])
            elif update[0] == 'buy':
                self.buy(update[1], int(update[2]))
            elif update[0] == 'sell':
                self.sell(update[1], int(update[2]), int(update[3]))
            elif update[0] == 'exit':
                self.shutdown()
                break
            elif update[0] == 'light':
                command = input('> ')
                if command == 'q':
                    self.shutdown()
                    break
            self.draw()
        di.shutdown()

    def shutdown(self):
        l.info(f'Exiting')   # TODO: save session and such

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', choices=['L', 'M', 'None'], help='Ship size', default=None)
    parser.add_argument('-d', type=int, help='Maximum distance from star', default=None)
    parser.add_argument('-f', type=bool, help='Fitler permit requiring systems', default=None)
    parser.add_argument('-n', type=bool, help='Force a new session', default=False)
    args = parser.parse_args()

    cnt = Context(**args.__dict__)
    cnt.run()