# Copyright 2012, Jeroen Hoekx <jeroen@hoekx.be>
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
from ansible.module_utils.six import string_types


class ActionModule(ActionBase):
    ''' Create inventory groups based on variables '''

    # We need to be able to modify the inventory
    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        if 'key' not in self._task.args:
            result['failed'] = True
            result['msg'] = "the 'key' param is required when using group_by"
            return result

        group_name = self._task.args.get('key')
        parent_groups = self._task.args.get('parents', ['all'])
        if isinstance(parent_groups, string_types):
            parent_groups = [parent_groups]

        result['changed'] = False
        result['add_group'] = group_name.replace(' ', '-')
        result['parent_groups'] = [name.replace(' ', '-') for name in parent_groups]
        return result
