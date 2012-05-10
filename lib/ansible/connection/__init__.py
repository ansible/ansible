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

import os
import re

from local_transport import LocalConnection
from paramiko_transport import ParamikoConnection
from libssh2_transport import LibSSH2Connection

transports = ('local', 'paramiko', 'libssh2')

class Connection(object):
    ''' Handles abstract connections to remote hosts '''

    _LOCALHOSTRE = re.compile(r"^(127.0.0.1|localhost|%s)$" % os.uname()[1])

    def __init__(self, runner, transport,sudo_user):
        self.runner = runner
        self.transport = transport
        self.sudo_user = sudo_user
    def connect(self, host, port=None):
        conn = None
        if self.transport == 'local' and self._LOCALHOSTRE.search(host):
            conn = LocalConnection(self.runner, host)
        elif self.transport == 'paramiko':
            conn = ParamikoConnection(self.runner, host, port)
        elif self.transport == 'libssh2':
            conn = LibSSH2Connection(self.runner, host, port)
        if conn is None:
            raise Exception("unsupported connection type")
        return conn.connect()


