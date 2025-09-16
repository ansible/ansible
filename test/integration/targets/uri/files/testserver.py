from __future__ import annotations

import http.cookies
import http.server
import socketserver
import sys
import urllib.parse

if __name__ == '__main__':
    PORT = int(sys.argv[1])
    content_type_json = "application/json"

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_POST(self):
            if self.path == '/login':
                # For testcase - follow_redirects is None and Cookies are set
                # https://github.com/ansible/ansible/issues/85780
                content_length = int(self.headers['Content-Length'])
                post_data_bytes = self.rfile.read(content_length)
                post_data_str = post_data_bytes.decode('utf-8')
                parsed_data = urllib.parse.parse_qs(post_data_str)
                username = parsed_data.get('username', [None])[0]
                password = parsed_data.get('password', [None])[0]
                if username == "user" and password == "pass":
                    # Set a cookie
                    cookie = http.cookies.SimpleCookie()
                    cookie['session_id'] = 'secure_session_token_123'
                    self.send_response(302)
                    self.send_header('Location', '/success.html')
                    self.send_header('Set-Cookie', cookie.output(header=''))
                    self.end_headers()
            else:
                self.send_error(404)

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
