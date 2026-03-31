# Copyright 2013 Dag Wieers <dag@wieers.com>
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

from ansible.errors import AnsibleActionFail
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.action import ActionBase
from ansible.utils.vars import validate_variable_name
from . import VariableLayer


class ActionModule(ActionBase):

    TRANSFERS_FILES = False
    _requires_connection = False

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        facts = {}
        cacheable = boolean(self._task.args.pop('cacheable', False))

        if self._task.args:
            for (k, v) in self._task.args.items():
                k = self._templar.template(k)  # a rare case where key templating is allowed; backward-compatibility for dynamic storage

                validate_variable_name(k)

                facts[k] = v
        else:
            raise AnsibleActionFail('No key/value pairs provided, at least one is required for this action to succeed')

        if facts:
            # just as _facts actions, we don't set changed=true as we are not modifying the actual host
            if cacheable:
                self.register_host_variables(facts, VariableLayer.CACHEABLE_FACT)
            else:
                self.register_host_variables({}, VariableLayer.CACHEABLE_FACT)  # disable legacy behavior of registering 'ansible_facts' from result dict

            self.register_host_variables(facts, VariableLayer.EPHEMERAL_FACT)

            result['ansible_facts'] = facts
        else:
            # this should not happen, but JIC we get here
            raise AnsibleActionFail('Unable to create any variables with provided arguments')

        return result
