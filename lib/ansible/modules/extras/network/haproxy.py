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
short_description: Enable, disable, and set weights for HAProxy backend servers using socket commands.
description:
    - Enable, disable, and set weights for HAProxy backend servers using socket
      commands.
notes:
    - Enable and disable commands are restricted and can only be issued on
      sockets configured for level 'admin'. For example, you can add the line
      'stats socket /var/run/haproxy.sock level admin' to the general section of
      haproxy.cfg. See http://haproxy.1wt.eu/download/1.5/doc/configuration.txt.
options:
  backend:
    description:
      - Name of the HAProxy backend pool.
    required: false
    default: auto-detected
  host:
    description:
      - Name of the backend host to change.
    required: true
    default: null
  shutdown_sessions:
    description:
      - When disabling a server, immediately terminate all the sessions attached
        to the specified server. This can be used to terminate long-running
        sessions after a server is put into maintenance mode.
    required: false
    default: false
  socket:
    description:
      - Path to the HAProxy socket file.
    required: false
    default: /var/run/haproxy.sock
  state:
    description:
      - Desired state of the provided backend host.
    required: true
    default: null
    choices: [ "enabled", "disabled" ]
  wait:
    description:
      - Wait until the server reports a status of 'UP' when `state=enabled`, or
        status of 'MAINT' when `state=disabled`.
    required: false
    default: false
    version_added: "2.0"
  wait_interval:
    description:
      - Number of seconds to wait between retries.
    required: false
    default: 5
    version_added: "2.0"
  wait_retries:
    description:
      - Number of times to check for status after changing the state.
    required: false
    default: 25
    version_added: "2.0"
  weight:
    description:
      - The value passed in argument. If the value ends with the `%` sign, then
        the new weight will be relative to the initially configured weight.
        Relative weights are only permitted between 0 and 100% and absolute
        weights are permitted between 0 and 256.
    required: false
    default: null
'''

EXAMPLES = '''
# disable server in 'www' backend pool
- haproxy: state=disabled host={{ inventory_hostname }} backend=www

# disable server without backend pool name (apply to all available backend pool)
- haproxy: state=disabled host={{ inventory_hostname }}

# disable server, provide socket file
- haproxy: state=disabled host={{ inventory_hostname }} socket=/var/run/haproxy.sock backend=www

# disable server, provide socket file, wait until status reports in maintenance
- haproxy: state=disabled host={{ inventory_hostname }} socket=/var/run/haproxy.sock backend=www wait=yes

# disable backend server in 'www' backend pool and drop open sessions to it
- haproxy: state=disabled host={{ inventory_hostname }} backend=www socket=/var/run/haproxy.sock shutdown_sessions=true

# enable server in 'www' backend pool
- haproxy: state=enabled host={{ inventory_hostname }} backend=www

# enable server in 'www' backend pool wait until healthy
- haproxy: state=enabled host={{ inventory_hostname }} backend=www wait=yes

# enable server in 'www' backend pool wait until healthy. Retry 10 times with intervals of 5 seconds to retrieve the health
- haproxy: state=enabled host={{ inventory_hostname }} backend=www wait=yes wait_retries=10 wait_interval=5

# enable server in 'www' backend pool with change server(s) weight
- haproxy: state=enabled host={{ inventory_hostname }} socket=/var/run/haproxy.sock weight=10 backend=www

author: "Ravi Bhure (@ravibhure)"
'''

import socket
import csv
import time


DEFAULT_SOCKET_LOCATION="/var/run/haproxy.sock"
RECV_SIZE = 1024
ACTION_CHOICES = ['enabled', 'disabled']
WAIT_RETRIES=25
WAIT_INTERVAL=5

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
        self.wait = self.module.params['wait']
        self.wait_retries = self.module.params['wait_retries']
        self.wait_interval = self.module.params['wait_interval']
        self.command_results = []
        self.status_servers = []
        self.status_weights = []
        self.previous_weights = []
        self.previous_states  = []
        self.current_states   = []
        self.current_weights  = []

    def execute(self, cmd, timeout=200, capture_output=True):
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
        if capture_output:
            self.command_results = result.strip()
        self.client.close()
        return result

    def wait_until_status(self, pxname, svname, status):
        """
        Wait for a service to reach the specified status. Try RETRIES times
        with INTERVAL seconds of sleep in between. If the service has not reached
        the expected status in that time, the module will fail. If the service was 
        not found, the module will fail.
        """
        for i in range(1, self.wait_retries):
            data = self.execute('show stat', 200, False).lstrip('# ')
            r = csv.DictReader(data.splitlines())
            found = False
            for row in r:
                if row['pxname'] == pxname and row['svname'] == svname:
                    found = True
                    if row['status'] == status:
                        return True;
                    else:
                        time.sleep(self.wait_interval)

            if not found:
                self.module.fail_json(msg="unable to find server %s/%s" % (pxname, svname))

        self.module.fail_json(msg="server %s/%s not status '%s' after %d retries. Aborting." % (pxname, svname, status, self.wait_retries))

    def get_current_state(self, host, backend):
        """
        Gets the each original state value from show stat. 
        Runs before and after to determine if values are changed. 
        This relies on weight always being the next element after 
        status in "show stat" as well as status states remaining
        as indicated in status_states and haproxy documentation.
        """
   
        output = self.execute('show stat')
        output = output.lstrip('# ').strip()
        output = output.split(',')
        result = output
        status_states = [ 'UP','DOWN','DRAIN','NOLB','MAINT' ]
        self.status_server = []
        status_weight_pos = []
        self.status_weight = []

        for check, status in enumerate(result):
            if status in status_states:
                self.status_server.append(status) 
                status_weight_pos.append(check + 1) 

        for weight in status_weight_pos:
                self.status_weight.append(result[weight])

        return{'self.status_server':self.status_server, 'self.status_weight':self.status_weight}

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
                    if self.wait:
                        self.wait_until_status(pxname, svname, 'UP')

        else:
            pxname = backend
            cmd = "get weight %s/%s ; enable server %s/%s" % (pxname, svname, pxname, svname)
            if weight:
                cmd += "; set weight %s/%s %s" % (pxname, svname, weight)
            self.execute(cmd)
            if self.wait:
                self.wait_until_status(pxname, svname, 'UP')

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
                    if self.wait:
                        self.wait_until_status(pxname, svname, 'MAINT')

        else:
            pxname = backend
            cmd = "get weight %s/%s ; disable server %s/%s" % (pxname, svname, pxname, svname)
            if shutdown_sessions:
                cmd += "; shutdown sessions server %s/%s" % (pxname, svname)
            self.execute(cmd)
            if self.wait:
                self.wait_until_status(pxname, svname, 'MAINT')

    def act(self):
        """
        Figure out what you want to do from ansible, and then do it.
        """

        self.get_current_state(self.host, self.backend)
        self.previous_states = ','.join(self.status_server)
        self.previous_weights = ','.join(self.status_weight)

        # toggle enable/disbale server
        if self.state == 'enabled':
            self.enabled(self.host, self.backend, self.weight)

        elif self.state == 'disabled':
            self.disabled(self.host, self.backend, self.shutdown_sessions)

        else:
            self.module.fail_json(msg="unknown state specified: '%s'" % self.state)

        self.get_current_state(self.host, self.backend)
        self.current_states = ','.join(self.status_server)
        self.current_weights = ','.join(self.status_weight)


        if self.current_weights != self.previous_weights:
            self.module.exit_json(stdout=self.command_results, changed=True)  
        elif self.current_states != self.previous_states:
            self.module.exit_json(stdout=self.command_results, changed=True)
        else:
            self.module.exit_json(stdout=self.command_results, changed=False)  

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
            wait=dict(required=False, default=False, type='bool'),
            wait_retries=dict(required=False, default=WAIT_RETRIES, type='int'),
            wait_interval=dict(required=False, default=WAIT_INTERVAL, type='int'),
        ),

    )

    if not socket:
        module.fail_json(msg="unable to locate haproxy socket")

    ansible_haproxy = HAProxy(module)
    ansible_haproxy.act()

# import module snippets
from ansible.module_utils.basic import *

main()
