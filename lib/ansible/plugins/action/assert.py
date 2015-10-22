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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.playbook.conditional import Conditional
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    ''' Fail with custom message '''

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        if 'that' not in self._task.args:
            raise AnsibleError('conditional required in "that" string')

        msg = None
        if 'msg' in self._task.args:
            msg = self._task.args['msg']

        # make sure the 'that' items are a list
        thats = self._task.args['that']
        if not isinstance(thats, list):
            thats = [thats]

        # Now we iterate over the that items, temporarily assigning them
        # to the task's when value so we can evaluate the conditional using
        # the built in evaluate function. The when has already been evaluated
        # by this point, and is not used again, so we don't care about mangling
        # that value now
        cond = Conditional(loader=self._loader)
        for that in thats:
            cond.when = [that]
            test_result = cond.evaluate_conditional(templar=self._templar, all_vars=task_vars)
            if not test_result:
                result['failed'] = True
                result['evaluated_to'] = test_result
                result['assertion'] = that

                if msg:
                    result['msg'] = msg

                return result

        result['changed'] = False
        result['msg'] = 'all assertions passed'
        return result
