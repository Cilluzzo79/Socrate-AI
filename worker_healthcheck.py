"""
Minimal HTTP server for Celery worker healthcheck on Railway
Runs alongside the Celery worker to respond to Railway's healthcheck
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import os

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"healthy","service":"celery-worker"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress HTTP logs
        pass

def start_healthcheck_server(port=8080):
    """Start a background HTTP server for healthcheck"""
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[Healthcheck] HTTP server started on port {port}")
    return server

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    start_healthcheck_server(port)
    print("[Healthcheck] Server running, press Ctrl+C to stop")

    # Keep main thread alive
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[Healthcheck] Shutting down")
