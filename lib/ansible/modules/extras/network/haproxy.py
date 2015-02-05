#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Ravi Bhure <ravibhure@gmail.com>
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
module: haproxy
version_added: "1.9"
short_description: An Ansible module to handle states enable/disable server and set weight to backend host in haproxy using socket commands.
description:
    - The Enable Haproxy Backend Server, with
      supports get current weight for server (default) and
      set weight for haproxy backend server when provides.

    - The Disable Haproxy Backend Server, with
      supports get current weight for server (default) and
      shutdown sessions while disabling backend host server.
notes:
    - "enable or disable commands are restricted and can only be issued on sockets configured for level 'admin', "
    - "Check - http://haproxy.1wt.eu/download/1.5/doc/configuration.txt, "
    - "Example: 'stats socket /var/run/haproxy.sock level admin'"
options:
  state:
    description:
      - describe the desired state of the given host in lb pool.
    required: true
    default: null
    choices: [ "enabled", "disabled" ]
  host:
    description:
      - Host (backend) to operate in Haproxy.
    required: true
    default: null
  socket:
    description:
      - Haproxy socket file name with path.
    required: false
    default: /var/run/haproxy.sock
  backend:
    description:
      - Name of the haproxy backend pool.
        Required, else auto-detection applied.
    required: false
    default: auto-detected
  weight:
    description:
      - The value passed in argument. If the value ends with the '%' sign, then the new weight will be relative to the initially cnfigured weight. Relative weights are only permitted between 0 and 100% and absolute weights are permitted between 0 and 256.
    required: false
    default: null
  shutdown_sessions:
    description:
      - When disabling server, immediately terminate all the sessions attached to the specified server. This can be used to terminate long-running sessions after a server is put into maintenance mode, for instance.
    required: false
    default: false
'''

EXAMPLES = '''
examples:

# disable server in 'www' backend pool
- haproxy: state=disabled host={{ inventory_hostname }} backend=www

# disable server without backend pool name (apply to all available backend pool)
- haproxy: state=disabled host={{ inventory_hostname }}

# disable server, provide socket file
- haproxy: state=disabled host={{ inventory_hostname }} socket=/var/run/haproxy.sock backend=www

# disable backend server in 'www' backend pool and drop open sessions to it
- haproxy: state=disabled host={{ inventory_hostname }} backend=www socket=/var/run/haproxy.sock shutdown_sessions=true

# enable server in 'www' backend pool
- haproxy: state=enabled host={{ inventory_hostname }} backend=www

# enable server in 'www' backend pool with change server(s) weight
- haproxy: state=enabled host={{ inventory_hostname }} socket=/var/run/haproxy.sock weight=10 backend=www

author: Ravi Bhure <ravibhure@gmail.com>
'''

import socket


DEFAULT_SOCKET_LOCATION="/var/run/haproxy.sock"
RECV_SIZE = 1024
ACTION_CHOICES = ['enabled', 'disabled']

######################################################################
class TimeoutException(Exception):
  pass

class HAProxy(object):
    """
    Used for communicating with HAProxy through its local UNIX socket interface.
    Perform common tasks in Haproxy related to enable server and
    disable server.

    The complete set of external commands Haproxy handles is documented
    on their website:

    http://haproxy.1wt.eu/download/1.5/doc/configuration.txt#Unix Socket commands
    """

    def __init__(self, module):
        self.module = module

        self.state = self.module.params['state']
        self.host = self.module.params['host']
        self.backend = self.module.params['backend']
        self.weight = self.module.params['weight']
        self.socket = self.module.params['socket']
        self.shutdown_sessions = self.module.params['shutdown_sessions']

        self.command_results = []

    def execute(self, cmd, timeout=200):
        """
        Executes a HAProxy command by sending a message to a HAProxy's local
        UNIX socket and waiting up to 'timeout' milliseconds for the response.
        """

        self.client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.client.connect(self.socket)
        self.client.sendall('%s\n' % cmd)
        result = ''
        buf = ''
        buf = self.client.recv(RECV_SIZE)
        while buf:
            result += buf
            buf = self.client.recv(RECV_SIZE)
        self.command_results = result.strip()
        self.client.close()
        return result

    def enabled(self, host, backend, weight):
        """
        Enabled action, marks server to UP and checks are re-enabled,
        also supports to get current weight for server (default) and
        set the weight for haproxy backend server when provides.
        """
        svname = host
        if self.backend is None:
            output = self.execute('show stat')
            #sanitize and make a list of lines
            output = output.lstrip('# ').strip()
            output = output.split('\n')
            result = output

            for line in result:
                if 'BACKEND' in line:
                    result =  line.split(',')[0]
                    pxname = result
                    cmd = "get weight %s/%s ; enable server %s/%s" % (pxname, svname, pxname, svname)
                    if weight:
                        cmd += "; set weight %s/%s %s" % (pxname, svname, weight)
                    self.execute(cmd)

        else:
            pxname = backend
            cmd = "get weight %s/%s ; enable server %s/%s" % (pxname, svname, pxname, svname)
            if weight:
                cmd += "; set weight %s/%s %s" % (pxname, svname, weight)
            self.execute(cmd)

    def disabled(self, host, backend, shutdown_sessions):
        """
        Disabled action, marks server to DOWN for maintenance. In this mode, no more checks will be
        performed on the server until it leaves maintenance,
        also it shutdown sessions while disabling backend host server.
        """
        svname = host
        if self.backend is None:
            output = self.execute('show stat')
            #sanitize and make a list of lines
            output = output.lstrip('# ').strip()
            output = output.split('\n')
            result = output

            for line in result:
                if 'BACKEND' in line:
                    result =  line.split(',')[0]
                    pxname = result
                    cmd = "get weight %s/%s ; disable server %s/%s" % (pxname, svname, pxname, svname)
                    if shutdown_sessions:
                        cmd += "; shutdown sessions server %s/%s" % (pxname, svname)
                    self.execute(cmd)

        else:
            pxname = backend
            cmd = "get weight %s/%s ; disable server %s/%s" % (pxname, svname, pxname, svname)
            if shutdown_sessions:
                cmd += "; shutdown sessions server %s/%s" % (pxname, svname)
            self.execute(cmd)

    def act(self):
        """
        Figure out what you want to do from ansible, and then do it.
        """

        # toggle enable/disbale server
        if self.state == 'enabled':
            self.enabled(self.host, self.backend, self.weight)

        elif self.state == 'disabled':
            self.disabled(self.host, self.backend, self.shutdown_sessions)

        else:
            self.module.fail_json(msg="unknown state specified: '%s'" % self.state)

        self.module.exit_json(stdout=self.command_results, changed=True)

def main():

    # load ansible module object
    module = AnsibleModule(
        argument_spec = dict(
            state = dict(required=True, default=None, choices=ACTION_CHOICES),
            host=dict(required=True, default=None),
            backend=dict(required=False, default=None),
            weight=dict(required=False, default=None),
            socket = dict(required=False, default=DEFAULT_SOCKET_LOCATION),
            shutdown_sessions=dict(required=False, default=False),
        ),

    )

    if not socket:
        module.fail_json(msg="unable to locate haproxy socket")

    ansible_haproxy = HAProxy(module)
    ansible_haproxy.act()

# import module snippets
from ansible.module_utils.basic import *

main()
