#
# Copyright 2015 Peter Sprygada <psprygada@ansible.com>
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
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from ansible.plugins.action import ActionBase
from ansible.plugins.action.net_template import ActionModule as NetActionModule

class ActionModule(NetActionModule, ActionBase):

    def run(self, tmp=None, task_vars=None):
        if self._connection.transport == 'local':
            return super(ActionModule, self).run(tmp, task_vars)

        result = dict(changed=False)

        if isinstance(self._task.args['src'], basestring):
            self._handle_template()

        result.update(self._execute_module(module_name=self._task.action,
            module_args=self._task.args, task_vars=task_vars))

        if self._task.args.get('backup') and result.get('_backup'):
            contents = json.dumps(result['_backup'], indent=4)
            self._write_backup(task_vars['inventory_hostname'], contents)

        if '_backup' in result:
            del result['_backup']

        return result


