from __future__ import annotations

import http.server
import socketserver
import sys

if __name__ == '__main__':
    PORT = int(sys.argv[1])
    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), Handler)
    httpd.serve_forever()
