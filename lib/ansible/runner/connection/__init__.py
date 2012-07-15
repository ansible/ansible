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
#

################################################

import local
import paramiko_ssh
import ssh

class Connection(object):
    ''' Handles abstract connections to remote hosts '''

    def __init__(self, runner):
        self.runner = runner

    def connect(self, host, port=None):
        conn = None
        transport = self.runner.transport
        if transport == 'local':
            conn = local.LocalConnection(self.runner, host)
        elif transport == 'paramiko':
            conn = paramiko_ssh.ParamikoConnection(self.runner, host, port)
        elif transport == 'ssh':
            conn = SSHConnection(self.runner, host, port)
        if conn is None:
            raise Exception("unsupported connection type")
        return conn.connect()

