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
from ansible.utils.vars import merge_hash


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):

        # individual modules might disagree but as the generic the action plugin, pass at this point.
        self._supports_check_mode = True
        self._supports_async      = True

        results = super(ActionModule, self).run(tmp, task_vars)

        if not results.get('skipped'):

            if results.get('invocation', {}).get('module_args'):
                # avoid passing to modules in case of no_log
                # should not be set anymore but here for backwards compatibility
                del results['invocation']['module_args']

            # FUTURE: better to let _execute_module calculate this internally?
            wrap_async = self._task.async and not self._connection.has_native_async

            # do work!
            results = merge_hash(results, self._execute_module(tmp=tmp, task_vars=task_vars, wrap_async=wrap_async))

            # hack to keep --verbose from showing all the setup module results
            # moved from setup module as now we filter out all _ansible_ from results
            if self._task.action == 'setup':
                results['_ansible_verbose_override'] = True

        return results
