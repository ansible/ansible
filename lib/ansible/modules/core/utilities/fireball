#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: fireball
short_description: Enable fireball mode on remote node
description:
     - This modules launches an ephemeral I(fireball) ZeroMQ message bus daemon on the remote node which
       Ansible can use to communicate with nodes at high speed.
     - The daemon listens on a configurable port for a configurable amount of time.
     - Starting a new fireball as a given user terminates any existing user fireballs.
     - Fireball mode is AES encrypted
version_added: "0.9"
options:
  port:
    description:
      - TCP port for ZeroMQ
    required: false
    default: 5099
    aliases: []
  minutes:
    description:
      - The I(fireball) listener daemon is started on nodes and will stay around for
        this number of minutes before turning itself off.
    required: false
    default: 30
notes:
    - See the advanced playbooks chapter for more about using fireball mode.
requirements: [ "zmq", "keyczar" ]
author: Michael DeHaan
'''

EXAMPLES = '''
# This example playbook has two plays: the first launches 'fireball' mode on all hosts via SSH, and 
# the second actually starts using it for subsequent management over the fireball connection

- hosts: devservers
  gather_facts: false
  connection: ssh
  sudo: yes
  tasks:
      - action: fireball

- hosts: devservers
  connection: fireball
  tasks:
      - command: /usr/bin/anything
'''

import os
import sys
import shutil
import time
import base64
import syslog
import signal
import time
import signal
import traceback

syslog.openlog('ansible-%s' % os.path.basename(__file__))
PIDFILE = os.path.expanduser("~/.fireball.pid")

def log(msg):
    syslog.syslog(syslog.LOG_NOTICE, msg)

if os.path.exists(PIDFILE):
    try:
        data = int(open(PIDFILE).read())
        try:
            os.kill(data, signal.SIGKILL)
        except OSError:
            pass
    except ValueError:
        pass
    os.unlink(PIDFILE)

HAS_ZMQ = False
try:
    import zmq
    HAS_ZMQ = True
except ImportError:
    pass

HAS_KEYCZAR = False
try:
    from keyczar.keys import AesKey
    HAS_KEYCZAR = True
except ImportError:
    pass

# NOTE: this shares a fair amount of code in common with async_wrapper, if async_wrapper were a new module we could move
# this into utils.module_common and probably should anyway

def daemonize_self(module, password, port, minutes):
    # daemonizing code: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
    try:
        pid = os.fork()
        if pid > 0:
            log("exiting pid %s" % pid)
            # exit first parent
            module.exit_json(msg="daemonized fireball on port %s for %s minutes" % (port, minutes))
    except OSError, e:
        log("fork #1 failed: %d (%s)" % (e.errno, e.strerror))
        sys.exit(1)

    # decouple from parent environment
    os.chdir("/")
    os.setsid()
    os.umask(022)

    # do second fork
    try:
        pid = os.fork()
        if pid > 0:
            log("daemon pid %s, writing %s" % (pid, PIDFILE))
            pid_file = open(PIDFILE, "w")
            pid_file.write("%s" % pid)
            pid_file.close()
            log("pidfile written")
            sys.exit(0)
    except OSError, e:
        log("fork #2 failed: %d (%s)" % (e.errno, e.strerror))
        sys.exit(1)

    dev_null = file('/dev/null','rw')
    os.dup2(dev_null.fileno(), sys.stdin.fileno())
    os.dup2(dev_null.fileno(), sys.stdout.fileno())
    os.dup2(dev_null.fileno(), sys.stderr.fileno())
    log("daemonizing successful (%s,%s)" % (password, port))

def command(module, data):
    if 'cmd' not in data:
        return dict(failed=True, msg='internal error: cmd is required')
    if 'tmp_path' not in data:
        return dict(failed=True, msg='internal error: tmp_path is required')
    if 'executable' not in data:
        return dict(failed=True, msg='internal error: executable is required')

    log("executing: %s" % data['cmd'])
    rc, stdout, stderr = module.run_command(data['cmd'], executable=data['executable'], close_fds=True)
    if stdout is None:
        stdout = ''
    if stderr is None:
        stderr = ''
    log("got stdout: %s" % stdout)

    return dict(rc=rc, stdout=stdout, stderr=stderr)

def fetch(data):
    if 'in_path' not in data:
        return dict(failed=True, msg='internal error: in_path is required')

    # FIXME: should probably support chunked file transfer for binary files
    # at some point.  For now, just base64 encodes the file
    # so don't use it to move ISOs, use rsync.

    fh = open(data['in_path'])
    data = base64.b64encode(fh.read())
    return dict(data=data)

def put(data):

    if 'data' not in data:
        return dict(failed=True, msg='internal error: data is required')
    if 'out_path' not in data:
        return dict(failed=True, msg='internal error: out_path is required')

    # FIXME: should probably support chunked file transfer for binary files
    # at some point.  For now, just base64 encodes the file
    # so don't use it to move ISOs, use rsync.

    fh = open(data['out_path'], 'w')
    fh.write(base64.b64decode(data['data']))
    fh.close()

    return dict()

def serve(module, password, port, minutes):


    log("serving")
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    addr = "tcp://*:%s" % port
    log("zmq serving on %s" % addr)
    socket.bind(addr)

    # password isn't so much a password but a serialized AesKey object that we xferred over SSH
    # password as a variable in ansible is never logged though, so it serves well

    key = AesKey.Read(password)

    while True:

        data = socket.recv()

        try:
            data = key.Decrypt(data)
        except:
            continue

        data = json.loads(data)

        mode = data['mode']
        response = {}

        if mode == 'command':
            response = command(module, data)
        elif mode == 'put':
            response = put(data)
        elif mode == 'fetch':
            response = fetch(data)

        data2 = json.dumps(response)
        data2 = key.Encrypt(data2)
        socket.send(data2)

def daemonize(module, password, port, minutes):

    try:
        daemonize_self(module, password, port, minutes)

        def catcher(signum, _):
            module.exit_json(msg='timer expired')

        signal.signal(signal.SIGALRM, catcher)
        signal.setitimer(signal.ITIMER_REAL, 60 * minutes)


        serve(module, password, port, minutes)
    except Exception, e:
        tb = traceback.format_exc()
        log("exception caught, exiting fireball mode: %s\n%s" % (e, tb))
        sys.exit(0)

def main():

    module = AnsibleModule(
        argument_spec = dict(
            port=dict(required=False, default=5099),
            password=dict(required=True),
            minutes=dict(required=False, default=30),
        ),
        supports_check_mode=True
    )

    password  = base64.b64decode(module.params['password'])
    port      = module.params['port']
    minutes   = int(module.params['minutes'])

    if not HAS_ZMQ:
        module.fail_json(msg="zmq is not installed")
    if not HAS_KEYCZAR:
        module.fail_json(msg="keyczar is not installed")

    daemonize(module, password, port, minutes)


# import module snippets
from ansible.module_utils.basic import *
main()
