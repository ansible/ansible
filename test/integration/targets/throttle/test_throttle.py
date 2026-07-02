#!/usr/bin/env python

from __future__ import annotations

import os
import sys
import time

# read the args from sys.argv
throttledir, inventory_hostname, max_throttle = sys.argv[1:]
# format/create additional vars
max_throttle = int(max_throttle)
throttledir = os.path.expanduser(throttledir)
throttlefile = os.path.join(throttledir, inventory_hostname)
try:
    # create the file
    with open(throttlefile, 'a'):
        os.utime(throttlefile, None)
    # count the number of files in the dir
    throttlelist = os.listdir(throttledir)
    print("tasks: %d/%d" % (len(throttlelist), max_throttle))
    # if we have too many files, fail
    if len(throttlelist) > max_throttle:
        print(throttlelist)
        raise ValueError("Too many concurrent tasks: %d/%d" % (len(throttlelist), max_throttle))
    time.sleep(1.5)
finally:
    # remove the file, then wait to make sure it's gone
    os.unlink(throttlefile)
    while True:
        if not os.path.exists(throttlefile):
            break
        time.sleep(0.1)
