from __future__ import annotations

import http.server
import socketserver
import sys

if __name__ == '__main__':
    PORT = int(sys.argv[1])

    class Handler(http.server.SimpleHTTPRequestHandler):
        pass

    Handler.extensions_map['.json'] = 'application/json'
    httpd = socketserver.TCPServer(("", PORT), Handler)
    httpd.serve_forever()
