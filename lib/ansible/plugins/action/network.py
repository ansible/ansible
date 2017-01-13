#
# (c) 2016 Red Hat Inc.
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

import datetime

from ansible.plugins.action import ActionBase, display
from ansible.module_utils.local import _modify_module
from ansible.errors import AnsibleModuleExit

class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)
        del result['invocation']['module_args']

        module_name = self._task.action
        self._update_module_args(module_name, self._task.args, task_vars)

        try:
            _modify_module(self._task.args, self._connection)
            path = self._shared_loader_obj.module_loader.find_plugin(self._task.action)
            pkg = '.'.join(['ansible', 'modules', self._task.action])
            module = self._shared_loader_obj.module_loader._load_module_source(pkg, path)
            start_time = datetime.datetime.now()
            module.main()

        except AnsibleModuleExit as exc:
            result.update(exc.result)
            for field in ('_ansible_notify',):
                if field in result:
                    result.pop(field)

        except Exception as exc:
            if display.verbosity > 2:
                raise
            result.update(dict(failed=True, msg=str(exc)))

        end_time = datetime.datetime.now()
        delta = end_time - start_time

        result.update({
            'start': str(start_time),
            'end': str(end_time),
            'delta': str(delta)
        })

        return result

