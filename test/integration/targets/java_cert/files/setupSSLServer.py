import BaseHTTPServer
import SimpleHTTPServer
import ssl
import os
import sys

root_dir = sys.argv[1]
port = int(sys.argv[2])

httpd = BaseHTTPServer.HTTPServer(('localhost', port), SimpleHTTPServer.SimpleHTTPRequestHandler)
httpd.socket = ssl.wrap_socket(httpd.socket, server_side=True,
                               certfile=os.path.join(root_dir, 'cert.pem'),
                               keyfile=os.path.join(root_dir, 'key.pem'))
httpd.handle_request()
