import itertools
from threading import Thread
import pickle
import argparse
import sys, os
from rares import RareLoader, RareGraph, RareNode
from time import time, sleep
from terminaltables import AsciiTable, DoubleTable
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
    def __init__(self, s='L', d=50000, f=True, p=150, l=None, **kwargs):
        self.rare_controller = RareLoader(sell_distance=p)
        self.rare_controller.init(ship_size=s, max_distance_from_star=d, filter_needs_permit=f)
        self.current = {'system': None, 'station': None, 'node': None, 'rare_commodity': None}
        self.route = []
        self.cargo = dict()
        self.generated_route = []  # todo: generate route
        self.profit = 0
        self.proposed = []
        self.commodity_controller = Commodities()
        self.rare_holder = {}
        self.max_ly = l


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
        if self.generated_route.__len__() == 0:  # TODO: route-regen command
            self.generated_route = self.rare_controller.generate(system_o, station_o, node=node, max_ly=self.max_ly)  # add route generation
        self.current = {
            'system': system_o,
            'station': station_o,
            'node': node,
            'rare_commodity': None
        }
        self.route.append(self.current)
        self.proposed = self.rare_controller.alternative_determine_next(self.current['system'], self.current['station'], visited=[self.rare_holder[k] for k in self.rare_holder])

    def buy(self, commodity_name, amount, eddbid):
        if eddbid is None:
            test = self.commodity_controller.get_by_name(commodity_name)
            if (test is None or test.get('is_rare')) and self.current['node'] is not None:
                self.current['rare_commodity'] = commodity_name
                self.rare_holder[commodity_name] = self.current['node']
        else:
            rare = self.commodity_controller.get_by_id(eddbid)
            if rare is not None and rare["is_rare"]:
                self.rare_holder[commodity_name] = self.current['node']  # todo: fix this when loading up
            elif rare is None:
                self.rare_holder[commodity_name] = self.current['node']

        if commodity_name not in self.cargo.keys():
            self.cargo[commodity_name] = amount
        else:
            self.cargo[commodity_name] += amount


    def sell(self, commodity_name, amount, profit, eddbid):
        if commodity_name in self.cargo.keys():
            self.cargo[commodity_name] -= amount
            if self.cargo[commodity_name] <= 0:
                del self.cargo[commodity_name]
                if commodity_name in self.rare_holder.keys():
                    del self.rare_holder[commodity_name]
        self.profit += profit


    def draw(self):
        res = os.system('cls')
        if res != 0:
            os.system('clear')
        header_table_data = [['System', 'Station', 'Node', 'Profit'],
                             [None if self.current['system'] is None else self.current['system'].name,
                              None if self.current['station'] is None else self.current['station'].name,
                              self.current['node'], self.profit]]
        header_table_data[0] = [AsciiControl.HEADER+q+AsciiControl.ENDC for q in header_table_data[0]]
        header_table = AsciiTable(header_table_data)
        header_table.title = 'Current Info'
        print(header_table.table)

        info_table_data = [['Cargo', 'Route', 'Generated Jump', 'Generated Commodity', 'Proposed Jump', 'Proposed Commodity']]
        info_table_data[0] = [AsciiControl.HEADER + q + AsciiControl.ENDC for q in info_table_data[0]]
        for commodity, made_step, loop_step, proposed_step in itertools.zip_longest(self.cargo, self.route, self.generated_route, self.proposed):
            commodity_text = ''
            if commodity is not None:
                commodity_text = f'{AsciiControl.OKGREEN if commodity in self.rare_holder.keys() else AsciiControl.OKBLUE}{commodity}{AsciiControl.ENDC} ({self.cargo[commodity]})'
                if commodity in self.rare_holder.keys():
                    dst = self.rare_controller.check_sell(self.current["system"], self.rare_holder[commodity])
                    if dst is not None:
                        commodity_text += f'{AsciiControl.WARNING}Sellable {dst}{AsciiControl.ENDC}'
            made_step_text = ''
            if made_step is not None:
                made_step_text = f'{AsciiControl.UNDERLINE}{made_step["system"].name}:{made_step["station"].name}{AsciiControl.ENDC} (Rare: {None if made_step["node"] is None else AsciiControl.OKGREEN + made_step["node"].name + AsciiControl.ENDC})'
            loop_step_text = ''
            loop_step_commodity = ''
            if loop_step is not None:
                loop_step_text = f'{AsciiControl.UNDERLINE}{loop_step["node"].system.name}:{loop_step["node"].station.name}{AsciiControl.ENDC} ({round(loop_step["distance"], 2)} LY)'
                if loop_step["profit"] is not None and loop_step["profit"] > 0:
                    loop_step_commodity = f'{AsciiControl.OKBLUE + loop_step["commodity"].name + AsciiControl.ENDC}:{AsciiControl.OKGREEN if loop_step["profit"] > 1000 else AsciiControl.FAIL}{loop_step["profit"]}{AsciiControl.ENDC} Cz/T ({round(loop_step["updated"], 2)} h)'
            proposed_step_text = ''
            proposed_step_commodity = ''
            if proposed_step is not None:
                proposed_step_text = f'{AsciiControl.UNDERLINE}{proposed_step["system"]}:{proposed_step["station"]}{AsciiControl.ENDC} ({round(proposed_step["distance"], 2)} LY);'
                if proposed_step["profit"] is not None and proposed_step["profit"] > 0:
                    proposed_step_commodity = f'{AsciiControl.OKBLUE + proposed_step["buy"] + AsciiControl.ENDC} {AsciiControl.OKGREEN if proposed_step["profit"] > 1000 else AsciiControl.FAIL}{proposed_step["profit"]}{AsciiControl.ENDC} Cz/T ({round(proposed_step["updated"], 2)} h)'
            info_table_data.append([commodity_text, made_step_text, loop_step_text, loop_step_commodity, proposed_step_text, proposed_step_commodity])
        info_table = AsciiTable(info_table_data)
        info_table.inner_row_border = True
        info_table.title = 'Stats'
        if info_table.ok:
            print(info_table.table)
        else:
            info_table_data_one = [q[:2] for q in info_table_data]
            info_table_data_two = [q[2:] for q in info_table_data]
            table_one = AsciiTable(info_table_data_one)
            table_one.inner_row_border = True
            table_two = AsciiTable(info_table_data_two)
            table_two.inner_row_border = True

            print(table_two.table)
            print(table_one.table)



    def run(self):
        self.draw()
        self.__listener()

    def __listener(self):
        for update in di.update_generator():
            update = update.strip().split(';')
            # switch event

            if update[0] == 'docked':
                self.docked(update[1], update[2])
            elif update[0] == 'buy':
                try:
                    eddb_id = int(update[3])
                except ValueError:
                    eddb_id = None
                self.buy(update[1], int(update[2]), eddb_id)
            elif update[0] == 'sell':
                try:
                    eddb_id = int(update[4])
                except ValueError:
                    eddb_id = None
                self.sell(update[1], int(update[2]), int(update[3]), eddb_id)
            elif update[0] == 'exit':
                self.shutdown()
                break
            elif update[0] == 'light':
                command = input('> ')
                if command == 'q':
                    self.shutdown()
                    break
                elif command == 'r':
                    self.generated_route = self.rare_controller.generate(self.current["system"], self.current["station"], node=self.current["node"])
            elif update[0] == 'load_session':
                update.pop(0)
                self.docked(update.pop(0), update.pop(0))


                while update.__len__() > 1:
                    self.buy(update.pop(0), update.pop(0), None)
            self.draw()
        di.shutdown()

    def shutdown(self):
        l.info(f'Exiting')   # TODO: save session and such

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', choices=['L', 'M', 'None'], help='Ship size', default='L')
    parser.add_argument('-d', type=int, help='Maximum distance from star', default=50000)
    parser.add_argument('-f', type=bool, help='Fitler permit requiring systems', default=True)
    parser.add_argument('-n', type=bool, help='Force a new session', default=False)
    parser.add_argument('-p', type=int, help='Selling distance for rares', default=150)
    parser.add_argument('-l', type=int, help='Max light years between generated route jumps', default=None)
    args = parser.parse_args()

    cnt = Context(**args.__dict__)
    # cnt.run()
    cnt.docked('Aganippe', 'Julian Market')
    cnt.buy('Aganippe Rush', 20, 179)
    cnt.draw()
    # print(cnt.proposed)