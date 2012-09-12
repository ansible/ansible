# (c) 2012, Tim Bielawa <tbielawa@redhat.com>
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

from ansible.callbacks import vvv

class Connection(object):
    ''' Fake internal-type connection '''

    def __init__(self, runner=None, host=None, port=None):
        self.runner = runner
        self.host = host
        self.port = port

    def connect(self, port=None):
        ''' connect to the local host; nothing to do here '''
        return self

    def exec_command(self, cmd, tmp_path=None, sudo_user=None, sudoable=False):
        ''' run a command locally in this process.
        cmd should be passed as a function reference
        the return from cmd should be a results dict '''
        return cmd()

    def put_file(self, in_path, out_path):
        ''' no need to transfer raw python commands '''
        pass

    def fetch_file(self, in_path, out_path):
        ''' irrelevant '''
        pass

    def close(self):
        ''' terminate the connection; nothing to do here '''
        pass
