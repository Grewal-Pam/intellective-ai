from http.server import SimpleHTTPRequestHandler, HTTPServer

HOST = '127.0.0.1'
PORT = 8000

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            super().do_GET()

if __name__ == '__main__':
    print(f"Starting dev server at http://{HOST}:{PORT}")
    server = HTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        print('Server stopped')
