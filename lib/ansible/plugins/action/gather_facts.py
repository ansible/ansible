# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import time

from ansible.module_utils.common._collections_compat import MutableMapping

from ansible import constants as C
from ansible.plugins.action import ActionBase
from ansible.utils.vars import combine_vars


class ActionModule(ActionBase):

    def _get_module_args(self, fact_module, task_vars):
        mod_args = task_vars.get('ansible_facts_modules', {}).get(fact_module, {})
        if isinstance(mod_args, MutableMapping):
            mod_args.update(self._task.args.copy())
        else:
            mod_args = self._task.args.copy()

        if fact_module != 'setup':
            mod_args.pop('gather_subset', None)

        return mod_args

    def run(self, tmp=None, task_vars=None):
        ''' handler for package operations '''

        self._supports_check_mode = True

        result = super(ActionModule, self).run(tmp, task_vars)
        result['ansible_facts'] = {}

        jobs = {}
        modules = C.config.get_config_value('FACTS_MODULES', variables=task_vars)
        if len(modules) > 1:
            for fact_module in modules:

                mod_args = self._get_module_args(fact_module, task_vars)
                self._display.vvvv("Running %s" % fact_module)
                jobs[fact_module] = (self._execute_module(module_name=fact_module, module_args=mod_args, task_vars=task_vars, wrap_async=True))

            failed = {}
            skipped = {}
            while jobs:
                for module in jobs:
                    poll_args = {'jid': jobs[module]['ansible_job_id'], '_async_dir': os.path.dirname(jobs[module]['results_file'])}
                    res = self._execute_module(module_name='async_status', module_args=poll_args, task_vars=task_vars, wrap_async=False)
                    if 'finished' in res:
                        if res.get('failed', False):
                            failed[module] = res.get('msg')
                        elif res.get('skipped', False):
                            skipped[module] = res.get('msg')
                        else:
                            result = combine_vars(result, {'ansible_facts': res.get('ansible_facts', {})})
                        del jobs[module]
                        break
                else:
                    time.sleep(0.5)

            if skipped:
                result['msg'] = "The following modules where skipped: %s\n" % (', '.join(skipped.keys()))
                for skip in skipped:
                    result['msg'] += '  %s: %s\n' % (skip, skipped[skip])
                if len(skipped) == len(modules):
                    result['skipped'] = True

            if failed:
                result['failed'] = True
                result['msg'] += "The following modules failed to execute: %s\n" % (', '.join(failed.keys()))
                for fail in failed:
                    result['msg'] += '  %s: %s\n' % (fail, failed[fail])
        else:
            # just one module, no need for fancy async
            mod_args = self._get_module_args(modules[0], task_vars)
            result.update(self._execute_module(module_name=modules[0], module_args=mod_args, task_vars=task_vars, wrap_async=False))

        # tell executor facts were gathered
        result['ansible_facts']['_ansible_facts_gathered'] = True

        return result
