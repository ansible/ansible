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

from ansible import utils

class ReturnData(object):
    ''' internal return class for runner execute methods, not part of public API signature '''

    __slots__ = [ 'result', 'comm_ok', 'host' ]

    def __init__(self, conn=None, host=None, result=None, comm_ok=True):

        # which host is this ReturnData about?
        if conn is not None:
            delegate_for = getattr(conn, '_delegate_for', None)
            if delegate_for:
                self.host = delegate_for
            else:
                self.host = conn.host
        else:
            self.host = host

        self.result = result
        self.comm_ok = comm_ok

        if type(self.result) in [ str, unicode ]:
            self.result = utils.parse_json(self.result)

        if self.host is None:
            raise Exception("host not set")
        if type(self.result) != dict:
            raise Exception("dictionary result expected")

    def communicated_ok(self):
        return self.comm_ok

    def is_successful(self):
        return self.comm_ok and ('failed' not in self.result) and (self.result.get('rc',0) == 0)

    def daisychain(self, module_name, module_args):
        ''' request a module call follow this one '''
        if self.is_successful():
            self.result['daisychain'] = module_name
            self.result['daisychain_args'] = module_args
        return self

