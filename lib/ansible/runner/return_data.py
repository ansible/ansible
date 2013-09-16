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

from ansible import utils

class ReturnData(object):
    ''' internal return class for runner execute methods, not part of public API signature '''

    __slots__ = [ 'result', 'comm_ok', 'host', 'diff', 'flags' ]

    def __init__(self, conn=None, host=None, result=None, 
        comm_ok=True, diff=dict(), flags=None):

        # which host is this ReturnData about?
        if conn is not None:
            self.host = conn.host
            delegate = getattr(conn, 'delegate', None)
            if delegate is not None:
                self.host = delegate

        else:
            self.host = host

        self.result = result
        self.comm_ok = comm_ok

        # if these values are set and used with --diff we can show
        # changes made to particular files
        self.diff = diff

        if type(self.result) in [ str, unicode ]:
            self.result = utils.parse_json(self.result)


        if self.host is None:
            raise Exception("host not set")
        if type(self.result) != dict:
            raise Exception("dictionary result expected")

        if flags is None:
            flags = []
        self.flags = []

    def communicated_ok(self):
        return self.comm_ok

    def is_successful(self):
        return self.comm_ok and (self.result.get('failed', False) == False) and ('failed_when_result' in self.result and [not self.result['failed_when_result']] or [self.result.get('rc',0) == 0])[0]

