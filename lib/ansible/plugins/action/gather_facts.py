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
            subset = mod_args.pop('gather_subset', None)
            if subset not in ('all', ['all']):
                self._display.warning('Ignoring subset(%s) for %s' % (subset, fact_module))

        return mod_args

    def run(self, tmp=None, task_vars=None):

        self._supports_check_mode = True

        result = super(ActionModule, self).run(tmp, task_vars)
        result['ansible_facts'] = {}

        parallel = task_vars.pop('ansible_facts_parallel', self._task.args.pop('parallel', None))

        modules = task_vars.get('ansible_facts_modules', {}).keys()
        override_vars = {}
        if modules:
            override_vars['ansible_facts_modules'] = modules
        modules = C.config.get_config_value('FACTS_MODULES', variables=override_vars)

        failed = {}
        skipped = {}
        if parallel is False or (len(modules) == 1 and parallel is None):
            # serially execute each module
            for fact_module in modules:
                # just one module, no need for fancy async
                mod_args = self._get_module_args(fact_module, task_vars)
                res = self._execute_module(module_name=fact_module, module_args=mod_args, task_vars=task_vars, wrap_async=False)
                if res.get('failed', False):
                    failed[fact_module] = res.get('msg')
                elif res.get('skipped', False):
                    skipped[fact_module] = res.get('msg')
                else:
                    result = combine_vars(result, {'ansible_facts': res.get('ansible_facts', {})})
        else:
            # do it async
            jobs = {}
            for fact_module in modules:

                mod_args = self._get_module_args(fact_module, task_vars)
                self._display.vvvv("Running %s" % fact_module)
                jobs[fact_module] = (self._execute_module(module_name=fact_module, module_args=mod_args, task_vars=task_vars, wrap_async=True))

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
            result['msg'] = "The following modules were skipped: %s\n" % (', '.join(skipped.keys()))
            for skip in skipped:
                result['msg'] += '  %s: %s\n' % (skip, skipped[skip])
            if len(skipped) == len(modules):
                result['skipped'] = True

        if failed:
            result['failed'] = True
            result['msg'] += "The following modules failed to execute: %s\n" % (', '.join(failed.keys()))
            for fail in failed:
                result['msg'] += '  %s: %s\n' % (fail, failed[fail])

        # tell executor facts were gathered
        result['ansible_facts']['_ansible_facts_gathered'] = True

        return result
