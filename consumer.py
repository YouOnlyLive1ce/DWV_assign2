from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
from threading import Lock
from collections import defaultdict
import os

app = Flask(__name__)
CORS(app)

# Thread-safe data storage
received_data = []
data_lock = Lock()
request_stats = defaultdict(int)
last_cleanup = datetime.now()

def cleanup_old_points():
    global received_data, last_cleanup
    now = datetime.now()
    if (now - last_cleanup).total_seconds() > 5:  # Cleanup every 5 seconds
        with data_lock:
            received_data = [p for p in received_data 
                           if (now - datetime.fromtimestamp(p['time'])).total_seconds() <= 10]
        last_cleanup = now

@app.route('/')
def index():
    return render_template('map.html')

@app.route('/api/data', methods=['POST'])
def receive_data():
    global received_data
    try:
        data = request.json
        timestamp = datetime.now().timestamp()
        
        if not isinstance(data, list):
            data = [data]
        
        processed_data = []
        with data_lock:
            for item in data:
                new_point = {
                    'ip': item.get('ip address', ''),
                    'lat': float(item.get('Latitude', 0)),
                    'lon': float(item.get('Longitude', 0)),
                    'suspicious': float(item.get('suspicious', 0)),
                    'time': timestamp
                }
                received_data.append(new_point)
                processed_data.append(new_point)
        
        # Update request statistics (for the chart)
        current_second = int(timestamp)
        request_stats[current_second] += len(processed_data)
        
        cleanup_old_points()
        return jsonify({"status": "success", "received": len(processed_data)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/points')
def get_points():
    cleanup_old_points()
    with data_lock:
        return jsonify({
            "points": received_data,
            "stats": {
                "total": len(received_data),
                "suspicious": sum(1 for p in received_data if p['suspicious'] > 0.5),
                "normal": sum(1 for p in received_data if p['suspicious'] <= 0.5)
            }
        })

@app.route('/api/request-stats')
def get_request_stats():
    # Get stats for last 60 seconds
    current_second = int(datetime.now().timestamp())
    stats = [request_stats.get(current_second - i, 0) 
             for i in range(60)][::-1]  # Reverse to show newest last
    return jsonify({"stats": stats})

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    print(f'host port {host} {port}')
    app.run(host=host, port=port, debug=True)