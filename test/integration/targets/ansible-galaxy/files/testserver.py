from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import ssl
import http.server
import socketserver

if __name__ == '__main__':
    Handler = http.server.SimpleHTTPRequestHandler
    context = ssl.SSLContext()
    context.load_cert_chain(certfile='./cert.pem', keyfile='./key.pem')
    httpd = socketserver.TCPServer(("", 4443), Handler)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    httpd.serve_forever()
