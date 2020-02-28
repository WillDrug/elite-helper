from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from eddb.logger import EliteLogger
l = EliteLogger('flask')
async_mode = None

app = Flask(__name__, static_url_path='', static_folder='templates')
app.config['SECRET_KEY'] = 'secret!'
app.logger = l
socketio = SocketIO(app, async_mode=async_mode)

from eddb.loader import EDDBLoader
el = EDDBLoader()
# el.recache_all()

from eddb.trading import Trader
t = Trader(ship_size='L', distance_from_star=200)

from eddi import EDDI
e = EDDI()
e.startup()

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@socketio.on('connect', namespace='/trade')
def connected():
    read_config()

@socketio.on('read_config')
def read_config():
    data = {
        'requires_permit': t.requires_permit,
        'distance_from_star': t.distance_from_star,
        'lock_system': t.lock_system,
        'ship_size': t.ship_size.size,
        'limit_planetary': t.limit_planetary,
        'limit_types': t.limit_types,
        'limit_sell_count': t.limit_sell_count
    }
    socketio.emit('read_config_done', data=data, namespace='/trade')

@socketio.on('set_config')
def set_config(config):
    t.requires_permit = config.get('requires_permit', False)
    t.distance_from_star = config.get('distance_from_star', -1)
    t.lock_system = config.get('lock_system', None)
    t.ship_size = config.get('ship_size', '')
    t.limit_planetary = config.get('limit_planetary', False)
    t.limit_types = config.get('limit_types', None)
    if t.limit_types == '':
        t.limit_types = None
    t.limit_sell_count = config.get('limit_sell_count')
    if t.limit_sell_count == 0:
        t.limit_sell_count = None
    read_config()


@socketio.on('quit')
def shutdown():
    e.shutdown()
    socketio.stop()
    quit()

if __name__ == '__main__':
    socketio.run(app, debug=True)