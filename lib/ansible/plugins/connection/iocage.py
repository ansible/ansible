# based on jail.py    (c) 2013, Michael Scherer <misc@zarb.org>
#                     (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2016, Stephan Lohse <dev-github@ploek.org>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import distutils.spawn
import os
import subprocess
from jail import Connection as jail

from ansible.errors import AnsibleError
from ansible.plugins.connection import ConnectionBase, BUFSIZE

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(ConnectionBase):
    ''' Local iocage based connections '''

    transport = 'iocage'
    has_pipelining = jail.has_pipelining
    become_methods = jail.become_methods

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self.ioc_jail = self._play_context.remote_addr

        if os.geteuid() != 0:
            raise AnsibleError("iocage/jail connection requires running as root")

        self.iocage_cmd = jail._search_executable('iocage')

        jail_uuid = self.get_jail_uuid()

        play_context.remote_addr = 'ioc-{}'.format(jail_uuid)

        display.vvv(u"Jail {iocjail} has been translated to {rawjail}".format(iocjail = self.ioc_jail, rawjail = play_context.remote_addr))
        
        self.jail_connector = jail(play_context, new_stdin, *args, **kwargs)

    def get_jail_uuid(self):
        p = subprocess.Popen([self.iocage_cmd, 'get', 'host_hostuuid', self.ioc_jail],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        
        stdout, stderr = p.communicate()
        # otherwise p.returncode would not be set
        p.wait()

        if p.returncode != 0:
            raise AnsibleError(u"iocage returned an error: {}".format(stdout))

        return stdout.strip('\n')
    
    def _connect(self):
        self.jail_connector.connect()
        self._connected = self.jail_connector._connected

    def exec_command(self, cmd, in_data=None, sudoable=True):
        return self.jail_connector.exec_command(cmd, in_data, sudoable)

    def put_file(self, in_path, out_path):
        return self.jail_connector.put_file(in_path, out_path)

    def fetch_file(self, in_path, out_path):
        return self.jail_connector.fetch_file(in_path, out_path)

    def close(self):
        self.jail_connector.close()
        self._connected = False

