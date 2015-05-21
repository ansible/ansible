# (c) 2012-2013, Michael DeHaan <michael.dehaan@gmail.com>
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
import stat
import errno

from ansible import utils
from ansible.errors import AnsibleError

class Connector(object):
    ''' Handles abstract connections to remote hosts '''

    def __init__(self, runner):
        self.runner = runner

    def connect(self, host, port, user, password, transport, private_key_file, delegate_host):
        conn = utils.plugins.connection_loader.get(transport, self.runner, host, port, user=user, password=password, private_key_file=private_key_file)
        if conn is None:
            raise AnsibleError("unsupported connection type: %s" % transport)
        conn.delegate = delegate_host
        if private_key_file:
            # If private key is readable by user other than owner, flag an error
            st = None
            try:
                st = os.stat(private_key_file)
            except (IOError, OSError), e:
                if e.errno != errno.ENOENT: # file is missing, might be agent
                    raise(e)

            if st is not None and st.st_mode & (stat.S_IRGRP | stat.S_IROTH):
                raise AnsibleError("private_key_file (%s) is group-readable or world-readable and thus insecure - "
                                   "you will probably get an SSH failure"
                                   % (private_key_file,))
        self.active = conn.connect()
        return self.active
