#!/usr/bin/env python

import asyncore
import smtpd
import sys

port = 25
if len(sys.argv) > 1:
    port = int(sys.argv[1])

print('Start SMTP server on port', port)
smtp_server = smtpd.DebuggingServer(('127.0.0.1', port), None)
asyncore.loop()
