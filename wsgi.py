import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
print(sys.path)
from app import create_app, socketio  
app = create_app('development')  

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
