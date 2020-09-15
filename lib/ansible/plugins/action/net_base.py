# Copyright: (c) 2015, Ansible Inc,
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import copy

from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        result = {}
        play_context = copy.deepcopy(self._play_context)
        play_context.network_os = self._get_network_os(task_vars)
        new_task = self._task.copy()

        module = self._get_implementation_module(play_context.network_os, self._task.action)
        if not module:
            if self._task.args['fail_on_missing_module']:
                result['failed'] = True
            else:
                result['failed'] = False

            result['msg'] = ('Could not find implementation module %s for %s' %
                             (self._task.action, play_context.network_os))
            return result

        new_task.action = module

        action = self._shared_loader_obj.action_loader.get(play_context.network_os,
                                                           task=new_task,
                                                           connection=self._connection,
                                                           play_context=play_context,
                                                           loader=self._loader,
                                                           templar=self._templar,
                                                           shared_loader_obj=self._shared_loader_obj)
        display.vvvv('Running implementation module %s' % module)
        return action.run(task_vars=task_vars)

    def _get_network_os(self, task_vars):
        if 'network_os' in self._task.args and self._task.args['network_os']:
            display.vvvv('Getting network OS from task argument')
            network_os = self._task.args['network_os']
        elif self._play_context.network_os:
            display.vvvv('Getting network OS from inventory')
            network_os = self._play_context.network_os
        elif 'network_os' in task_vars.get('ansible_facts', {}) and task_vars['ansible_facts']['network_os']:
            display.vvvv('Getting network OS from fact')
            network_os = task_vars['ansible_facts']['network_os']
        else:
            raise AnsibleError('ansible_network_os must be specified on this host to use platform agnostic modules')

        return network_os

    def _get_implementation_module(self, network_os, platform_agnostic_module):
        module_name = network_os.split('.')[-1] + '_' + platform_agnostic_module.partition('_')[2]
        if '.' in network_os:
            fqcn_module = '.'.join(network_os.split('.')[0:-1])
            implementation_module = fqcn_module + '.' + module_name
        else:
            implementation_module = module_name

        if implementation_module not in self._shared_loader_obj.module_loader:
            implementation_module = None

        return implementation_module
