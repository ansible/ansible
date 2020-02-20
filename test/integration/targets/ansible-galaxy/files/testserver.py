from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import ssl

if __name__ == '__main__':
    if sys.version_info[0] >= 3:
        import http.server
        import socketserver
        Handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(("", 4443), Handler)
    else:
        import BaseHTTPServer
        import SimpleHTTPServer
        Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        httpd = BaseHTTPServer.HTTPServer(("", 4443), Handler)

    httpd.socket = ssl.wrap_socket(httpd.socket, certfile='./cert.pem', keyfile='./key.pem', server_side=True)
    httpd.serve_forever()
