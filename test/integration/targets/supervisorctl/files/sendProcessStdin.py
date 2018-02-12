#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import time

proc = sys.argv[1]
value = sys.argv[2]
username = sys.argv[3]
password = sys.argv[4]

if sys.version_info[0] == 2:
    from xmlrpclib import ServerProxy
    from urllib import quote
else:
    from xmlrpc.client import ServerProxy
    from urllib.parse import quote

if username:
    url = 'http://%s:%s@127.0.0.1:9001/RPC2' % (quote(username, safe=''), quote(password, safe=''))
else:
    url = 'http://127.0.0.1:9001/RPC2'

server = ServerProxy(url, verbose=True)
server.supervisor.sendProcessStdin(proc, 'import sys; print(%s); sys.stdout.flush();\n' % value)
