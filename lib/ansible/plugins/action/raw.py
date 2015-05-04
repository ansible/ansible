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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):
    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=dict()):

        # FIXME: need to rework the noop stuff still
        #if self.runner.noop_on_check(inject):
        #    # in --check mode, always skip this module execution
        #    return ReturnData(conn=conn, comm_ok=True, result=dict(skipped=True))

        executable = self._task.args.get('executable')
        result = self._low_level_execute_command(self._task.args.get('_raw_params'), tmp=tmp, executable=executable)

        # for some modules (script, raw), the sudo success key
        # may leak into the stdout due to the way the sudo/su
        # command is constructed, so we filter that out here
        if result.get('stdout','').strip().startswith('SUDO-SUCCESS-'):
            result['stdout'] = re.sub(r'^((\r)?\n)?SUDO-SUCCESS.*(\r)?\n', '', result['stdout'])

        return result
