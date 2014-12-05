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
version_added: "1.9"
'''

import logging
import socket
import re

logger = logging.getLogger(__name__)

DEFAULT_SOCKET_LOCATION="/var/run/haproxy.sock"
RECV_SIZE = 1024

def main():
    ACTION_CHOICES = [
        'enabled',
        'disabled',
        ]

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
        supports_check_mode=True,

    )
    state = module.params['state']
    host = module.params['host']
    backend = module.params['backend']
    weight = module.params['weight']
    socket = module.params['socket']
    shutdown_sessions = module.params['shutdown_sessions']

    ##################################################################
    # Required args per state:
    # (enabled/disabled) = (host)
    #
    # AnsibleModule will verify most stuff, we need to verify
    # 'socket' manually.

    ##################################################################

    ##################################################################
    if not socket:
        module.fail_json('unable to locate haproxy.sock')

    ##################################################################
    required_one_of=[['state', 'host']]

    ansible_haproxy = HAProxy(module, **module.params)
    if module.check_mode:
        module.exit_json(changed=True)
    else:
        ansible_haproxy.act()
    ##################################################################

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

    def __init__(self, module, **kwargs):
        self.module = module
        self.state = kwargs['state']
        self.host = kwargs['host']
        self.backend = kwargs['backend']
        self.weight = kwargs['weight']
        self.socket = kwargs['socket']
        self.shutdown_sessions = kwargs['shutdown_sessions']

        self.command_results = []

    def execute(self, cmd, timeout=200):
        """
        Executes a HAProxy command by sending a message to a HAProxy's local
        UNIX socket and waiting up to 'timeout' milliseconds for the response.
        """

        buffer = ""

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
        Enables backend server for a particular backend.

        enable server <backend>/<server>
          If the server was previously marked as DOWN for maintenance, this marks the
          server UP and checks are re-enabled.

          Both the backend and the server may be specified either by their name or by
          their numeric ID, prefixed with a sharp ('#').

          This command is restricted and can only be issued on sockets configured for
          level "admin".

        Syntax: enable server <pxname>/<svname>
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
        Disable backend server for a particular backend.

        disable server <backend>/<server>
          Mark the server DOWN for maintenance. In this mode, no more checks will be
          performed on the server until it leaves maintenance.
          If the server is tracked by other servers, those servers will be set to DOWN
          during the maintenance.

          In the statistics page, a server DOWN for maintenance will appear with a
          "MAINT" status, its tracking servers with the "MAINT(via)" one.

          Both the backend and the server may be specified either by their name or by
          their numeric ID, prefixed with a sharp ('#').

          This command is restricted and can only be issued on sockets configured for
          level "admin".

        Syntax: disable server <pxname>/<svname>
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
              if shutdown_sessions == 'true':
                cmd += "; shutdown sessions server %s/%s" % (pxname, svname)
              self.execute(cmd)

        else:
            pxname = backend
            cmd = "get weight %s/%s ; disable server %s/%s" % (pxname, svname, pxname, svname)
            if shutdown_sessions == 'true':
              cmd += "; shutdown sessions server %s/%s" % (pxname, svname)
            self.execute(cmd)

    def act(self):
        """
        Figure out what you want to do from ansible, and then do the
        needful (at the earliest).
        """
        # toggle enable/disbale server
        if self.state == 'enabled':
            self.enabled(self.host, self.backend, self.weight)

        elif self.state == 'disabled':
            self.disabled(self.host, self.backend, self.shutdown_sessions)

        else:
            self.module.fail_json(msg="unknown state specified: '%s'" % \
                                      self.state)

        self.module.exit_json(stdout=self.command_results, changed=True)

# import module snippets
from ansible.module_utils.basic import *

main()
