from __future__ import (absolute_import, division, print_function)

import datetime


def _log(message):
    now = datetime.datetime.now()
    timestamp = now.isoformat()
    b_timestamp = bytes(now.isoformat(), 'utf-8')
    with open('/tmp/unit_test.log', 'a') as f:
        f.write('%s: %s\n' % (timestamp, message))


def pytest_sessionstart(session):
    for name in session.listnames():
        _log('Starting %s' % name)


def pytest_sessionfinish(session):
    for name in session.listnames():
        _log('Stopping %s' % name)
