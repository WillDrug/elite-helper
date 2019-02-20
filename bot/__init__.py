import telepot
from telepot.loop import MessageLoop


class EliteBot:
    def __init__(self, token):
        self.bot = telepot.Bot(token)
        self.trading = True


    def run(self):
        def handler(msg):
            pass
        ml = MessageLoop(self.bot, handler)
        ml.run_as_thread()

