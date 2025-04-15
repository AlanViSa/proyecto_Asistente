import http.server
import socketserver
import sys

PORT = 8000

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Hello, world!')

print(f"Starting HTTP server on port {PORT}")
print(f"Try accessing: http://localhost:{PORT} or http://127.0.0.1:{PORT}")
print("Press Ctrl+C to stop the server")

try:
    with socketserver.TCPServer(("", PORT), SimpleHTTPRequestHandler) as httpd:
        print(f"Server running at port {PORT}")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("Server stopped.")
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1) 