# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017, Peter Sprygada <psprygad@redhat.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys


def do_fork():
    '''
    Does the required double fork for a daemon process. Based on
    http://code.activestate.com/recipes/66012-fork-a-daemon-process-on-unix/
    '''
    try:
        pid = os.fork()
        if pid > 0:
            return pid

        os.chdir("/")
        os.setsid()
        os.umask(0)

        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)

            # out_file = open('/dev/null', 'ab+')
            # err_file = open('/dev/null', 'ab+', 0)
            dev_null = open('/dev/null', 'r')

            # it is known best practice to remap stdout, stderr but that will
            # not allow the use of Display so this function will leave them be
            # os.dup2(out_file.fileno(), sys.stdout.fileno())
            # os.dup2(err_file.fileno(), sys.stderr.fileno())
            os.dup2(dev_null.fileno(), sys.stdin.fileno())

            return pid
        except OSError as e:
            sys.exit(1)
    except OSError as e:
        sys.exit(1)
