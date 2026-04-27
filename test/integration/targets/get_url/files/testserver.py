from __future__ import annotations

import http.server
import socketserver
import sys

if __name__ == '__main__':
    PORT = int(sys.argv[1])

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/incompleteRead':
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.send_header("Content-Length", "100")
                self.end_headers()
                self.wfile.write(b"ABCD")
            else:
                super().do_GET()

    Handler.extensions_map['.json'] = 'application/json'
    httpd = socketserver.TCPServer(("", PORT), Handler)
    httpd.serve_forever()
