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
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "YOUR_IP"
    print(f"\n{'='*50}")
    print(f"Charity Backend Server")
    print(f"{'='*50}")
    print(f"Local:   http://127.0.0.1:5000")
    print(f"Network: http://{local_ip}:5000")
    print(f"{'='*50}\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
