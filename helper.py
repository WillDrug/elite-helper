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
                self.rare_holder[commodity_name] = self.rare_controller.query_by_commodity(name=commodity_name, cid=eddbid)
        else:
            rare = self.commodity_controller.get_by_id(eddbid)
            if rare is not None and rare["is_rare"]:
                self.rare_holder[commodity_name] = self.rare_controller.query_by_commodity(cid=rare['id'])
            elif rare is None:
                self.rare_holder[commodity_name] = self.rare_controller.query_by_commodity(name=commodity_name)

        if commodity_name not in self.cargo.keys():
            self.cargo[commodity_name] = amount
        else:
            self.cargo[commodity_name] += amount
        self.proposed = self.rare_controller.alternative_determine_next(self.current['system'], self.current['station'],
                                                                        visited=[self.rare_holder[k] for k in
                                                                                 self.rare_holder])


    def sell(self, commodity_name, amount, profit, eddbid):
        if commodity_name in self.cargo.keys():
            self.cargo[commodity_name] -= amount
            if self.cargo[commodity_name] <= 0:
                del self.cargo[commodity_name]
                if commodity_name in self.rare_holder.keys():
                    del self.rare_holder[commodity_name]
        self.profit += profit
        self.proposed = self.rare_controller.alternative_determine_next(self.current['system'], self.current['station'],
                                                                        visited=[self.rare_holder[k] for k in
                                                                                 self.rare_holder])


    def draw(self):
        res = os.system('cls')
        if res != 0:
            os.system('clear')
        header_table_data = [['System', 'Station', 'Node', 'Buy Here', 'Profit'],
                             [None if self.current['system'] is None else self.current['system'].name,
                              None if self.current['station'] is None else self.current['station'].name,
                              self.current['node'],
                              '<none>' if self.current["node"] is None else ', '.join([q['name'] for q in self.current["node"].commodities])
                              , self.profit]]
        header_table_data[0] = [AsciiControl.HEADER+q+AsciiControl.ENDC for q in header_table_data[0]]
        header_table = AsciiTable(header_table_data)
        header_table.title = 'Current Info'
        print(header_table.table)

        info_table_data = [['Generated Jump', 'Sell Here', 'Generated Commodity', 'Proposed Jump', 'Proposed Commodity']]
        info_table_data[0] = [AsciiControl.HEADER + q + AsciiControl.ENDC for q in info_table_data[0]]
        cargo_table_data = [['Cargo', 'Route']]
        cargo_table_data[0] = [AsciiControl.HEADER + q + AsciiControl.ENDC for q in cargo_table_data[0]]

        for loop_step, proposed_step in itertools.zip_longest(self.generated_route, self.proposed):
            loop_step_text = ''
            loop_step_commodity = ''
            loop_step_sell = ''
            if loop_step is not None:
                loop_step_text = f'{AsciiControl.UNDERLINE}{loop_step["node"].system.name}:{loop_step["node"].station.name}{AsciiControl.ENDC} ({round(loop_step["distance"], 2)} LY)'
                if loop_step["profit"] is not None and loop_step["profit"] > 0:
                    loop_step_commodity = f'{AsciiControl.OKBLUE + loop_step["commodity"].name + AsciiControl.ENDC}:{AsciiControl.OKGREEN if loop_step["profit"] > 1000 else AsciiControl.FAIL}{loop_step["profit"]}{AsciiControl.ENDC} Cz/T ({round(loop_step["updated"], 2)} h)'
                if loop_step['sell'].__len__() > 0:
                    selling = [f"{', '.join([z['name'] for z in q.commodities])} ({round(q.system.distance(loop_step['node'].system), 2)})" for q in loop_step['sell']]
                    loop_step_sell = ';\n'.join(selling)
            proposed_step_text = ''
            proposed_step_commodity = ''
            if proposed_step is not None:
                proposed_step_text = f'{AsciiControl.UNDERLINE}{proposed_step["system"]}:{proposed_step["station"]}{AsciiControl.ENDC} ({round(proposed_step["distance"], 2)} LY);'
                if proposed_step["profit"] is not None and proposed_step["profit"] > 0:
                    proposed_step_commodity = f'{AsciiControl.OKBLUE + proposed_step["buy"] + AsciiControl.ENDC} {AsciiControl.OKGREEN if proposed_step["profit"] > 1000 else AsciiControl.FAIL}{proposed_step["profit"]}{AsciiControl.ENDC} Cz/T ({round(proposed_step["updated"], 2)} h)'
            info_table_data.append([loop_step_text, loop_step_sell, loop_step_commodity, proposed_step_text, proposed_step_commodity])

        for commodity, made_step in itertools.zip_longest(self.cargo, self.route):
            commodity_text = ''
            if commodity is not None:
                commodity_text = f'{AsciiControl.OKGREEN if commodity in self.rare_holder.keys() else AsciiControl.OKBLUE}{commodity}{AsciiControl.ENDC} ({self.cargo[commodity]})'
                if commodity in self.rare_holder.keys():
                    dst = self.rare_controller.check_sell(self.current["system"], self.rare_holder[commodity])
                    if dst is not None:
                        commodity_text += f'{AsciiControl.HEADER} SELL {round(dst, 2)}{AsciiControl.ENDC}'
            made_step_text = ''
            if made_step is not None:
                made_step_text = f'{AsciiControl.UNDERLINE}{made_step["system"].name}:{made_step["station"].name}{AsciiControl.ENDC}'

            cargo_table_data.append([commodity_text, made_step_text])
        info_table = AsciiTable(info_table_data)
        cargo_table = AsciiTable(cargo_table_data)
        info_table.inner_row_border = True
        cargo_table.inner_row_border = True
        info_table.title = 'Route Options'
        cargo_table.title = 'Cargo and Route'
        print(info_table.table)
        print(cargo_table.table)



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
                    self.generated_route = self.rare_controller.generate(self.current["system"],
                                                                         self.current["station"],
                                                                         node=self.current["node"],
                                                                         max_ly=self.max_ly)
                elif command == 'u':
                    l = input('max_ly>')
                    l = int(l)
                    p = input('sell_dst>')
                    p = int(p)
                    self.max_ly = l
                    self.rare_controller.sell_distance = p
                    self.generated_route = self.rare_controller.generate(self.current["system"],
                                                                         self.current["station"],
                                                                         node=self.current["node"],
                                                                         max_ly=self.max_ly)
            elif update[0] == 'load_session':
                update.pop(0)
                self.docked(update.pop(0), update.pop(0))


                while update.__len__() > 1:
                    self.buy(update.pop(0), int(update.pop(0)), None)
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
    cnt.run()
    # cnt.docked('HIP 10175', 'Stefanyshyn-Piper Station')
    # cnt.draw()
    # for jump in cnt.generated_route:
    #     input(f'<{jump["node"].system.name}, {jump["node"].station.name}>')
    #     cnt.docked(jump["node"].system.name, jump["node"].station.name)
    #     for commodity in jump["node"].commodities:
    #         cnt.buy(commodity['name'], 20, commodity['id'])
    #     cnt.draw()
