from flask import Flask, request
from flask_cors import CORS
from datetime import datetime
from ex1 import handle_command  # 🔁 directly import command handler

app = Flask(__name__)
CORS(app)

@app.route('/send/<command>', methods=['GET'])
def send_can_command(command):
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    ip = request.remote_addr

    success = handle_command(command)  # ✅ secure sending

    if success:
        print(f"[{timestamp}] ✅ {ip} -> Sent encrypted CAN command: {command}")
        return f'Sent: {command}', 200
    else:
        print(f"[{timestamp}] ❌ Invalid command from {ip}: {command}")
        return f'Invalid command: {command}', 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
