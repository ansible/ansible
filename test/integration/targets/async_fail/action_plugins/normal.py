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
from __future__ import annotations

from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):

        # individual modules might disagree but as the generic the action plugin, pass at this point.
        self._supports_check_mode = True
        self._supports_async = True

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        if not result.get('skipped'):

            if result.get('invocation', {}).get('module_args'):
                # avoid passing to modules in case of no_log
                # should not be set anymore but here for backwards compatibility
                del result['invocation']['module_args']

            # FUTURE: better to let _execute_module calculate this internally?
            wrap_async = self._task.async_val and not self._connection.has_native_async

            # do work!
            result = merge_hash(result, self._execute_module(task_vars=task_vars, wrap_async=wrap_async))

            # hack to keep --verbose from showing all the setup module result
            # moved from setup module as now we filter out all _ansible_ from result
            if self._task.action == 'setup':
                result['_ansible_verbose_override'] = True

        # Simulate a transient network failure
        if self._task.action == 'async_status' and 'finished' in result and result['finished'] != 1:
            raise AnsibleError('Pretend to fail somewhere in executing async_status')

        if not wrap_async:
            # remove a temporary path we created
            self._remove_tmp_path(self._connection._shell.tmpdir)

        return result
