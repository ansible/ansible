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

import re

import ansible.constants as C
from ansible import utils
from ansible import errors
from ansible.runner.return_data import ReturnData

class ActionModule(object):
    TRANSFERS_FILES = False

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):

        if self.runner.noop_on_check(inject):
            # in --check mode, always skip this module execution
            return ReturnData(conn=conn, comm_ok=True, result=dict(skipped=True))

        executable = ''
        # From library/command, keep in sync
        r = re.compile(r'(^|\s)(executable)=(?P<quote>[\'"])?(.*?)(?(quote)(?<!\\)(?P=quote))((?<!\\)\s|$)')
        for m in r.finditer(module_args):
            v = m.group(4).replace("\\", "")
            if m.group(2) == "executable":
                executable = v
        module_args = r.sub("", module_args)

        result = self.runner._low_level_exec_command(conn, module_args, tmp, sudoable=True, executable=executable,
                                                     become=self.runner.become)
        # for some modules (script, raw), the sudo success key
        # may leak into the stdout due to the way the sudo/su
        # command is constructed, so we filter that out here
        if result.get('stdout','').strip().startswith('BECOME-SUCCESS-'):
            result['stdout'] = re.sub(r'^((\r)?\n)?BECOME-SUCCESS.*(\r)?\n', '', result['stdout'])

        return ReturnData(conn=conn, result=result)
