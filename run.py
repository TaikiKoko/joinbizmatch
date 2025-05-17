
import eventlet
eventlet.monkey_patch()

from app import create_app, socketio
from config import ProductionConfig

app = create_app(ProductionConfig)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True) 