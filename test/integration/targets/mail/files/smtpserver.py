#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import asyncore
import os.path
import ssl
import sys

# Handle TLS and non-TLS support
try:
    import smtpd_tls
    HAS_TLS = True
except ImportError:
    import smtpd
    HAS_TLS = False
    print('Library smtpd-tls is missing or not supported, hence starttls is NOT supported.')

# Handle custom ports
port = '25:465'
if len(sys.argv) > 1:
    port = sys.argv[1]
ports = port.split(':')
if len(ports) > 1:
    port1, port2 = int(ports[0]), int(ports[1])
else:
    port1, port2 = int(port), None

# Handle custom certificate
basename = os.path.splitext(sys.argv[0])[0]
certfile = basename + '.crt'
if len(sys.argv) > 2:
    certfile = sys.argv[2]

# Handle custom key
keyfile = basename + '.key'
if len(sys.argv) > 3:
    keyfile = sys.argv[3]

try:
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
except AttributeError:
    ssl_ctx = None
    if HAS_TLS:
        print('Python ssl library does not support SSLContext, hence starttls and TLS are not supported.')
    import smtpd

if HAS_TLS and ssl_ctx is not None:
    print('Using %s and %s' % (certfile, keyfile))
    ssl_ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)

    print('Start SMTP server on port', port1)
    smtp_server1 = smtpd_tls.DebuggingServer(('127.0.0.1', port1), None, ssl_ctx=ssl_ctx, starttls=True)
    if port2:
        print('Start TLS SMTP server on port', port2)
        smtp_server2 = smtpd_tls.DebuggingServer(('127.0.0.1', port2), None, ssl_ctx=ssl_ctx, starttls=False)
else:
    print('Start SMTP server on port', port1)
    smtp_server1 = smtpd.DebuggingServer(('127.0.0.1', port1), None)
    if port2:
        print('WARNING: TLS is NOT supported on this system, not listening on port %s.' % port2)

asyncore.loop()
