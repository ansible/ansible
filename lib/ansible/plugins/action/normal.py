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
        if task_vars is None:
            task_vars = dict()

        results = super(ActionModule, self).run(tmp, task_vars)
        # remove as modules might hide due to nolog
        del results['invocation']['module_args']
        results = merge_hash(results, self._execute_module(tmp=tmp, task_vars=task_vars))
        # Remove special fields from the result, which can only be set
        # internally by the executor engine. We do this only here in
        # the 'normal' action, as other action plugins may set this.
        #
        # We don't want modules to determine that running the module fires
        # notify handlers.  That's for the playbook to decide.
        for field in ('_ansible_notify',):
            if field in results:
                results.pop(field)

        return results
