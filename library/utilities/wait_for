#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Jeroen Hoekx <jeroen@hoekx.be>
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

import socket
import datetime
import time
import sys

DOCUMENTATION = '''
---
module: wait_for
short_description: Waits for a given port to become accessible on a server.
description:
     - This is useful for when services are not immediately available after
       their init scripts return - which is true of certain Java application
       servers. It is also useful when starting guests with the M(virt) module and
       needing to pause until they are ready.
version_added: "0.7"
options:
  host:
    description:
      - hostname or IP address to wait for
    required: false
    default: "127.0.0.1"
    aliases: []
  timeout:
    description:
      - maximum number of seconds to wait for
    required: false
    default: 300
  delay:
    description:
      - number of seconds to wait before starting to poll
    required: false
    default: 0
  port:
    description:
      - port number to poll
    required: true
  state:
    description:
      - either C(started), or C(stopped) depending on whether the module should 
        poll for the port being open or closed.
    choices: [ "started", "stopped" ]
    default: "started"
notes: []
requirements: []
author: Jeroen Hoekx
'''

EXAMPLES = '''
# wait 300 seconds for port 8000 to become open on the host, don't start checking for 10 seconds
- wait_for: port=8000 delay=10"
'''

def main():

    module = AnsibleModule(
        argument_spec = dict(
            host=dict(default='127.0.0.1'),
            timeout=dict(default=300),
            connect_timeout=dict(default=5),
            delay=dict(default=0),
            port=dict(required=True),
            state=dict(default='started', choices=['started', 'stopped']),
        ),
    )

    params = module.params

    host = params['host']
    timeout = int(params['timeout'])
    connect_timeout = int(params['connect_timeout'])
    delay = int(params['delay'])
    port = int(params['port'])
    state = params['state']

    start = datetime.datetime.now()

    if delay:
        time.sleep(delay)

    if state == 'stopped':
        ### first wait for the host to go down
        end = start + datetime.timedelta(seconds=timeout)

        while datetime.datetime.now() < end:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(connect_timeout)
            try:
                s.connect( (host, port) )
                s.shutdown(socket.SHUT_RDWR)
                s.close()
                time.sleep(1)
            except:
                break
        else:
            elapsed = datetime.datetime.now() - start
            module.fail_json(msg="Timeout when waiting for %s:%s to stop." % (host, port), elapsed=elapsed.seconds)

    elif state == 'started':
        ### wait for the host to come up
        end = start + datetime.timedelta(seconds=timeout)

        while datetime.datetime.now() < end:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(connect_timeout)
            try:
                s.connect( (host, port) )
                s.shutdown(socket.SHUT_RDWR)
                s.close()
                break
            except:
                time.sleep(1)
                pass
        else:
            elapsed = datetime.datetime.now() - start
            module.fail_json(msg="Timeout when waiting for %s:%s" % (host, port), elapsed=elapsed.seconds)

    elapsed = datetime.datetime.now() - start
    module.exit_json(state=state, port=port, elapsed=elapsed.seconds)

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
main()
