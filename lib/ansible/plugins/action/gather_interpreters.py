# Copyright 2018 Andrew Gaffney <andrew@agaffney.org>
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

import os
import re

from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        facts = {
            # Used to prevent gathering interpreters on subsequent plays
            'module_gather_interpreters': True
        }

        overwrite = boolean(self._task.args.pop('overwrite', False))

        if hasattr(self._connection._shell, 'find_binary'):
            # TODO: make list of binary names configurable
            find_result = self._low_level_execute_command(self._connection._shell.find_binary(['python', 'python3', 'foo', 'bar']), sudoable=False)
            if len(find_result['stdout_lines']) > 0:
                for interpreter in find_result['stdout_lines']:
                    basename = os.path.basename(interpreter)
                    interpreter_vars = ['ansible_' + basename + '_interpreter']
                    matches = re.match('(.*[^0-9.]+)([0-9.]+)?$', basename)
                    if matches:
                        interpreter_vars.append('ansible_' + matches.group(1) + '_interpreter')
                    for var in interpreter_vars:
                        if var not in facts and (overwrite or var not in task_vars):
                            facts[var] = interpreter

        result['changed'] = False
        result['ansible_facts'] = facts
        # Setting cacheable to True causes warnings about restricted vars
        result['_ansible_facts_cacheable'] = False
        # hack to keep --verbose from showing the results from this action, like
        # we do with 'setup'
        result['_ansible_verbose_override'] = True
        return result
