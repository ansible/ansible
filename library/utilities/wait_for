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
import re

DOCUMENTATION = '''
---
module: wait_for
short_description: Waits for a condition before continuing.
description:
     - Waiting for a port to become available is useful for when services 
       are not immediately available after their init scripts return - 
       which is true of certain Java application servers. It is also 
       useful when starting guests with the M(virt) module and
       needing to pause until they are ready. This module can 
       also be used to wait for a file to be available on the filesystem
       or with a regex match a string to be present in a file.
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
    required: false
  state:
    description:
      - either C(present), C(started), or C(stopped) 
      - When checking a port C(started) will ensure the port is open, C(stopped) will check that it is closed
      - When checking for a file or a search string C(present) or C(started) will ensure that the file or string is present before continuing
    choices: [ "present", "started", "stopped" ]
    default: "started"
  path:
    version_added: "1.4"
    required: false
    description:
      - path to a file on the filesytem that must exist before continuing
  search_regex:
    version_added: "1.4"
    required: false
    description:
      - with the path option can be used match a string in the file that must match before continuing.  Defaults to a multiline regex.
   
notes: []
requirements: []
author: Jeroen Hoekx, John Jarvis
'''

EXAMPLES = '''

# wait 300 seconds for port 8000 to become open on the host, don't start checking for 10 seconds
- wait_for: port=8000 delay=10"

# wait until the file /tmp/foo is present before continuing
- wait_for: path=/tmp/foo

# wait until the string "completed" is in the file /tmp/foo before continuing
- wait_for: path=/tmp/foo search_regex=completed

'''

def main():

    module = AnsibleModule(
        argument_spec = dict(
            host=dict(default='127.0.0.1'),
            timeout=dict(default=300),
            connect_timeout=dict(default=5),
            delay=dict(default=0),
            port=dict(default=None),
            path=dict(default=None),
            search_regex=dict(default=None),
            state=dict(default='started', choices=['started', 'stopped', 'present']),
        ),
    )

    params = module.params

    host = params['host']
    timeout = int(params['timeout'])
    connect_timeout = int(params['connect_timeout'])
    delay = int(params['delay'])
    if params['port']:
        port = int(params['port'])
    else:
        port = None
    state = params['state']
    path = params['path']
    search_regex = params['search_regex']
    
    if port and path:
        module.fail_json(msg="port and path parameter can not both be passed to wait_for")
    if path and state == 'stopped':
        module.fail_json(msg="state=stopped should only be used for checking a port in the wait_for module")
        
    start = datetime.datetime.now()

    if delay:
        time.sleep(delay)

    if state == 'stopped':
        ### first wait for the stop condition
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

    elif state in ['started', 'present']:
        ### wait for start condition
        end = start + datetime.timedelta(seconds=timeout)
        while datetime.datetime.now() < end:
            if path:
                try:
                    with open(path) as f:
                        if search_regex:
                            if re.search(search_regex, f.read(), re.MULTILINE):
                                break
                            else:
                                time.sleep(1)
                        else:
                            break
                except IOError:
                    time.sleep(1)
                    pass
            elif port:
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
            if port:
                module.fail_json(msg="Timeout when waiting for %s:%s" % (host, port), elapsed=elapsed.seconds)
            elif path:
                if search_regex:
                    module.fail_json(msg="Timeout when waiting for search string %s in %s" % (search_regex, path), elapsed=elapsed.seconds)
                else:
                    module.fail_json(msg="Timeout when waiting for file %s" % (path), elapsed=elapsed.seconds)


    elapsed = datetime.datetime.now() - start
    module.exit_json(state=state, port=port, search_regex=search_regex, path=path, elapsed=elapsed.seconds)

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
main()
