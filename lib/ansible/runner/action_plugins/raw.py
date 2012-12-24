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

import shlex

from ansible import utils
from ansible.runner.return_data import ReturnData

class ActionModule(object):
    NEEDS_TMPPATH = False

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject):
        executable = None
        pty = False
        args = []
        for arg in module_args.split(' '):
            if arg.startswith('executable='):
                executable = '='.join(arg.split('=')[1:])
            elif arg.startswith('pty='):
                pty = utils.boolean('='.join(arg.split('=')[1:]))
            else:
                args.append(arg)
        module_args = ' '.join(args).encode('utf-8')

        result = self.runner._low_level_exec_command(conn, module_args, tmp, sudoable=True, executable=executable, pty=pty)
        result.update(dict(changed=True))

        return ReturnData(conn=conn, result=result)
