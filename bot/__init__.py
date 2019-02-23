import telepot
from telepot.loop import MessageLoop
import pickle
import os
import sys
import logging
# TODO: util-up logger setup to split into a microservice later
l = logging.getLogger('Bot')
l.handlers = []
l.addHandler(logging.StreamHandler(stream=sys.stdout))
l.setLevel(logging.DEBUG)


class EliteBot:
    def __init__(self, token, trader):
        l.info(f'Initializing bot')
        self.bot = telepot.Bot(token)
        self.trader = trader
        try:
            l.info(f'Loaded config')
            self.config = pickle.loads(open(f'{os.path.dirname(os.path.realpath(__file__))}/bot_config.pcl', 'rb+').read())
        except FileNotFoundError:
            l.info(f'Failed to fetch config, reloading defaults')
            self.default()
        self.trading = True

    def default(self, k=None):
        default = {
            'trading': True,
            'ship_size': 'None',
            'max_distance_from_star': -1
        }
        if k is None:
            self.config = default
        else:
            self.config[k] = default[k]

    def save_config(self):
        pickle.dump(self.config, open(f'{os.path.dirname(os.path.realpath(__file__))}/bot_config.pcl', 'wb'))

    def cget(self, k):
        if k not in self.config.keys():
            l.warning(f'Defaulting config value for {k}')
            self.default(k)
        return self.config[k]

    def cset(self, k, v):
        l.debug(f'Setting config {k} to {v}')
        self.config[k] = v
        self.save_config()

    def handler(self, msg):
        l.debug(f'Got a message')
        if 'chat' not in msg.keys():
            return False
        if msg.get('chat').get('type') != 'private':
            return False
        if msg.get('from', {}).get('id', 0) != 391834810:  # todo: reword this when switching to multiple-user microservice architecture
            return False
        command_string = msg.get('text').split(' ')
        command = command_string[0]
        args = command_string[1:]

        if command == '/trade':
            if self.cget('trading'):
                self.cset('trading', False)
                self.trader.clear()
                self.bot.sendMessage(msg.get('from', {}).get('id', 391834810), 'Trading helper is off')
            else:
                bot.cset('trading', True)
                self.trader.init()
                self.bot.sendMessage(msg.get('from', {}).get('id', 391834810), 'Trading helper is on')
        elif command == '/ship':
            size = args[0]
            if size not in ['None', 'M', 'L']:
                self.bot.sendMessage(msg.get('from', {}).get('id', 391834810), 'Invalid ship size')
                return False
            self.cset('ship_size', size)
            self.bot.sendMessage(msg.get('from', {}).get('id', 391834810), 'Ship size set')
        elif command == '/star_distance':
            dst = args[0]
            try:
                dst = int(dst)
            except ValueError:
                self.bot.sendMessage(msg.get('from', {}).get('id', 391834810), 'Not a number')
            self.cset('max_distance_from_star', dst)
            self.bot.sendMessage(msg.get('from', {}).get('id', 391834810), 'Max distance from star set')
        elif command == '/report':
            k = args[0]
            self.bot.sendMessage(msg.get('from', {}).get('id', 391834810), f'{k}: {self.cget(k)}')

    def run(self):
        l.debug(f'Running bot loop')
        MessageLoop(self.bot, handle=self.handler).run_as_thread()
        l.debug(f'Ran')


if __name__ == '__main__':
    from config import telegram_token
    bot = EliteBot(telegram_token)
    bot.run()
