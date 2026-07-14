from __future__ import annotations

import http.server
import socketserver
import sys

if __name__ == '__main__':
    PORT = int(sys.argv[1])
    content_type_json = "application/json"

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/chunked':
                self.request.sendall(
                    b'HTTP/1.1 200 OK\r\n'
                    b'Transfer-Encoding: chunked\r\n'
                    b'\r\n'
                    b'a\r\n'  # size of the chunk (0xa = 10)
                    b'123456'
                )
            elif self.path.endswith('json'):
                try:
                    with open(self.path[1:]) as f:
                        self.send_response(200)
                        self.send_header("Content-type", content_type_json)
                        self.end_headers()
                        self.wfile.write(bytes(f.read(), "utf-8"))
                except OSError:
                    self.send_error(404)
            else:
                self.send_error(404)

    Handler.extensions_map['.json'] = content_type_json
    httpd = socketserver.TCPServer(("", PORT), Handler)
    httpd.serve_forever()
