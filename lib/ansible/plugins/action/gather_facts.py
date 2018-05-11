# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from collections import MutableMapping

from ansible import constants as C
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        ''' handler for package operations '''

        self._supports_check_mode = True
        self._supports_async = True

        result = super(ActionModule, self).run(tmp, task_vars)
        result['ansible_facts'] = {}

        for fact_module in C.config.get_config_value('FACTS_MODULES', variables=task_vars):

            mod_args = task_vars.get('ansible_facts_modules', {}).get(fact_module, {})
            if isinstance(mod_args, MutableMapping):
                mod_args.update(self._task.args.copy())
            else:
                mod_args = self._task.args.copy()

            if fact_module != 'setup':
                del mod_args['gather_subset']

            self._display.vvvv("Running %s" % fact_module)
            result.update(self._execute_module(module_name=fact_module, module_args=mod_args, task_vars=task_vars, wrap_async=self._task.async_val))

        # tell executor facts were gathered
        result['ansible_facts']['_ansible_facts_gathered'] = True

        return result
