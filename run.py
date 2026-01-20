from app import create_app
from flask import send_from_directory
import os

app = create_app()

# Serve uploaded files
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    upload_folder = os.path.join(os.path.dirname(__file__), 'uploads')
    return send_from_directory(upload_folder, filename)

if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"\n{'='*50}")
    print(f"Charity Backend Server")
    print(f"{'='*50}")
    print(f"Local:   http://127.0.0.1:5000")
    print(f"Network: http://{local_ip}:5000")
    print(f"{'='*50}\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
