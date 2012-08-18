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

from ansible import utils
from ansible.errors import AnsibleError

import os.path
dirname = os.path.dirname(__file__)
modules = utils.import_plugins(os.path.join(dirname, 'connections'))

# rename this module
modules['paramiko'] = modules['paramiko_ssh']
del modules['paramiko_ssh']

class Connection(object):
    ''' Handles abstract connections to remote hosts '''

    def __init__(self, runner):
        self.runner = runner

    def connect(self, host, port=None):
        conn = None
        transport = self.runner.transport
        module = modules.get(transport, None)
        if module is None:
            raise AnsibleError("unsupported connection type: %s" % transport)
        conn = module.Connection(self.runner, host, port)
        return conn.connect()

