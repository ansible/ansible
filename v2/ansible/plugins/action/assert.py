# Copyright 2012, Dag Wieers <dag@wieers.com>
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

from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):
    ''' Fail with custom message '''

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=dict()):

        # note: the fail module does not need to pay attention to check mode
        # it always runs.

        msg = None
        if 'msg' in self._task.args:
            msg = self._task.args['msg']

        if not 'that' in self._task.args:
            raise AnsibleError('conditional required in "that" string')

        for that in self._task.args['that']:
            self._task.when = [ that ]
            test_result = self._task.evaluate_conditional(all_vars=task_vars)
            if not test_result:
                result = dict(
                   failed       = True,
                   evaluated_to = test_result,
                   assertion    = that,
                )

                if msg:
                    result['msg'] = msg

                return result

        return dict(changed=False, msg='all assertions passed')

