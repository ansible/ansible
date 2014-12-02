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
short_description: An Ansible module to handle actions enable/disable server and set/get weight from haproxy using socket commands.
description:
    - Enable/Diable Haproxy Backend Server,
    - Get/Set weight of Haproxy Backend Server,
      using haproxy socket commands - http://haproxy.1wt.eu
notes:
    - "enable or disable or set weight commands are restricted and can only be issued on sockets configured for level 'admin', "
    - "Check - http://haproxy.1wt.eu/download/1.5/doc/configuration.txt, "
    - "Example: 'stats socket /var/run/haproxy.sock level admin'"
options:
  action:
    description:
      - Action to take.
    required: true
    default: null
    choices: [ "enable_server", "disable_server", "get_weight", "set_weight" ]
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
# disable backend server in 'www' backend
- haproxy: action=disable_server host={{ inventory_hostname }} backend=www

# disable backend server without backend name (applied to all)
- haproxy: action=disable_server host={{ inventory_hostname }}

# disable server, provide socket file
- haproxy: action=disable_server host={{ inventory_hostname }} socket=/var/run/haproxy.sock backend=www

# disable backend server in 'www' backend and drop open sessions to it
- haproxy: action=disable_server host={{ inventory_hostname }} backend=www shutdown_sessions=true

# enable backend server in 'www' backend
- haproxy: action=enable_server host={{ inventory_hostname }} backend=www

# report a server's current weight in 'www' backend
- haproxy: action=get_weight host={{ inventory_hostname }} backend=www

# change a server's current weight in 'www' backend
- haproxy: action=set_weight host={{ inventory_hostname }} backend=www weight=10

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
        'enable_server',
        'disable_server',
        'get_weight',
        'set_weight'
        ]

    # load ansible module object
    module = AnsibleModule(
        argument_spec = dict(
            action = dict(required=True, default=None, choices=ACTION_CHOICES),
            host=dict(required=True, default=None),
            backend=dict(required=False, default=None),
            weight=dict(required=False, default=None),
            socket = dict(required=False, default=DEFAULT_SOCKET_LOCATION),
            shutdown_sessions=dict(required=False, default=False),
        ),
    )
    action = module.params['action']
    host = module.params['host']
    backend = module.params['backend']
    weight = module.params['weight']
    socket = module.params['socket']
    shutdown_sessions = module.params['shutdown_sessions']

    ##################################################################
    # Required args per action:
    # (enable/disable)_server = (host)
    #
    # AnsibleModule will verify most stuff, we need to verify
    # 'socket' manually.

    ##################################################################

    if action in ['enable_server', 'disable_server', 'get_weight', 'set_weight']:
        if not host:
            module.fail_json(msg='no host specified for action requiring one')
    ##################################################################
    if not socket:
        module.fail_json('unable to locate haproxy.sock')

    ##################################################################
    supports_check_mode=True,
    required_one_of=[['action', 'host']]

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
        self.action = kwargs['action']
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

    def enable_server(self, host, backend):
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
              cmd = "enable server %s/%s" % (pxname, svname)
              self.execute(cmd)

        else:
            pxname = backend
            cmd = "enable server %s/%s" % (pxname, svname)
            self.execute(cmd)

    def disable_server(self, host, backend, shutdown_sessions):
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
              cmd = "disable server %s/%s" % (pxname, svname)
              if shutdown_sessions:
                cmd += "; shutdown sessions server %s/%s" % (pxname, svname)
              self.execute(cmd)

        else:
            pxname = backend
            cmd = "disable server %s/%s" % (pxname, svname)
            if shutdown_sessions:
              cmd += "; shutdown sessions server %s/%s" % (pxname, svname)
            self.execute(cmd)

    def get_weight(self, host, backend):
        """
        Report a server's current weight.

        get weight <backend>/<server>
          Report the current weight and the initial weight of server <server> in
          backend <backend> or an error if either doesn't exist. The initial weight is
          the one that appears in the configuration file. Both are normally equal
          unless the current weight has been changed. Both the backend and the server
          may be specified either by their name or by their numeric ID, prefixed with a
          sharp ('#').

        Syntax: get weight <pxname>/<svname>
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
              cmd = "get weight %s/%s" % (pxname, svname)
              self.execute(cmd)

        else:
            pxname = backend
            cmd = "get weight %s/%s" % (pxname, svname)
            self.execute(cmd)

    def set_weight(self, host, backend, weight):
        """
        Change a server's current weight.

        set weight <backend>/<server> <weight>[%]
          Change a server's weight to the value passed in argument. If the value ends
          with the '%' sign, then the new weight will be relative to the initially
          configured weight. Relative weights are only permitted between 0 and 100%,
          and absolute weights are permitted between 0 and 256. Servers which are part
          of a farm running a static load-balancing algorithm have stricter limitations
          because the weight cannot change once set. Thus for these servers, the only
          accepted values are 0 and 100% (or 0 and the initial weight). Changes take
          effect immediately, though certain LB algorithms require a certain amount of
          requests to consider changes. A typical usage of this command is to disable
          a server during an update by setting its weight to zero, then to enable it
          again after the update by setting it back to 100%. This command is restricted
          and can only be issued on sockets configured for level "admin". Both the
          backend and the server may be specified either by their name or by their
          numeric ID, prefixed with a sharp ('#').

        Syntax: set weight <pxname>/<svname>
        """
        svname = host
        weight = weight
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
              cmd = "set weight %s/%s %s" % (pxname, svname, weight)
              self.execute(cmd)

        else:
            pxname = backend
            cmd = "set weight %s/%s %s" % (pxname, svname, weight)
            self.execute(cmd)

    def act(self):
        """
        Figure out what you want to do from ansible, and then do the
        needful (at the earliest).
        """
        # toggle enable/disbale server
        if self.action == 'enable_server':
            self.enable_server(self.host, self.backend)

        elif self.action == 'disable_server':
            self.disable_server(self.host, self.backend, self.shutdown_sessions)

        # toggle get/set weight
        elif self.action == 'get_weight':
            self.get_weight(self.host, self.backend)

        elif self.action == 'set_weight':
            self.set_weight(self.host, self.backend, self.weight)
        # wtf?
        else:
            self.module.fail_json(msg="unknown action specified: '%s'" % \
                                      self.action)

        self.module.exit_json(stdout=self.command_results, changed=True)

# import module snippets
from ansible.module_utils.basic import *

main()
