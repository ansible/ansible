from __future__ import annotations

import http.server
import os
import pathlib
import socketserver
import ssl


if __name__ == '__main__':
    Handler = http.server.SimpleHTTPRequestHandler
    context = ssl.SSLContext()
    context.load_cert_chain(certfile='./cert.pem', keyfile='./key.pem')
    httpd = socketserver.TCPServer(("", 4443), Handler)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    pf = pathlib.Path('./testserver.json')

    try:
        pf.write_text(str(os.getpid()))
        httpd.serve_forever()
    except BaseException:
        pf.unlink(missing_ok=True)
        raise
