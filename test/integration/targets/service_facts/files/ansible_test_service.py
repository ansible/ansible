#!/usr/bin/env python

# this is mostly based off of the code found here:
# http://code.activestate.com/recipes/278731-creating-a-daemon-the-python-way/

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import resource
import signal
import time

UMASK = 0
WORKDIR = "/"
MAXFD = 1024

if (hasattr(os, "devnull")):
    REDIRECT_TO = os.devnull
else:
    REDIRECT_TO = "/dev/null"


def createDaemon():
    try:
        pid = os.fork()
    except OSError as e:
        raise Exception("%s [%d]" % (e.strerror, e.errno))

    if (pid == 0):
        os.setsid()

        try:
            pid = os.fork()
        except OSError as e:
            raise Exception("%s [%d]" % (e.strerror, e.errno))

        if (pid == 0):
            os.chdir(WORKDIR)
            os.umask(UMASK)
        else:
            f = open('/var/run/ansible_test_service.pid', 'w')
            f.write("%d\n" % pid)
            f.close()
            os._exit(0)
    else:
        os._exit(0)

    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if (maxfd == resource.RLIM_INFINITY):
        maxfd = MAXFD

    for fd in range(0, maxfd):
        try:
            os.close(fd)
        except OSError:  # ERROR, fd wasn't open to begin with (ignored)
            pass

    os.open(REDIRECT_TO, os.O_RDWR)
    os.dup2(0, 1)
    os.dup2(0, 2)

    return (0)


if __name__ == "__main__":

    signal.signal(signal.SIGHUP, signal.SIG_IGN)

    retCode = createDaemon()

    while True:
        time.sleep(1000)
