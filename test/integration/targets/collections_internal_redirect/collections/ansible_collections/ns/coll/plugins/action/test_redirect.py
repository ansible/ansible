# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleOptionsError
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    ''' Test the redirect list '''

    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset(('name', 'assert', 'plugin_type',))

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        if 'name' not in self._task.args or 'assert' not in self._task.args:
            raise AnsibleOptionsError('"name" and "assert" are required options')
        if self._task.args.get('plugin_type', 'module') not in ('module', 'action'):
            raise AnsibleOptionsError('"plugin_type" should be one of: "module", "action"')

        name = self._task.args.get('name')
        expected_redirect = self._task.args.get('assert')
        plugin_type = self._task.args.get('plugin_type', 'module')

        if plugin_type == 'module':
            context = self._shared_loader_obj.module_loader.find_plugin_with_context(
                name, collection_list=self._task.collections
            )
        else:
            context = self._shared_loader_obj.action_loader.find_plugin_with_context(
                name, collection_list=self._task.collections
            )

        redirect_list = context.redirect_list

        result = {
            'changed': False,
            'assert': expected_redirect,
            'redirect_list': redirect_list,
        }

        if not context.resolved:
            result['failed'] = True
            result['msg'] = 'Could not resolve plugin {0}'.format(name)
        elif expected_redirect != redirect_list:
            result['failed'] = True
            result['msg'] = 'Failed to match the redirect list'
        else:
            result['failed'] = False
            result['msg'] = 'Success'

        return result
