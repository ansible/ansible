# (c) 2015, Ansible Inc,
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


from ansible.errors import AnsibleAction, AnsibleActionFail
from ansible.executor.module_common import get_action_args_with_defaults
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    UNUSED_PARAMS = {
        'systemd': ['pattern', 'runlevel', 'sleep', 'arguments', 'args'],
    }

    def run(self, tmp=None, task_vars=None):
        ''' handler for package operations '''

        self._supports_check_mode = True
        self._supports_async = True

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        module = self._task.args.get('use', 'auto').lower()

        if module == 'auto':
            try:
                if self._task.delegate_to:  # if we delegate, we should use delegated host's facts
                    module = self._templar.template("{{hostvars['%s']['ansible_facts']['service_mgr']}}" % self._task.delegate_to)
                else:
                    module = self._templar.template('{{ansible_facts.service_mgr}}')
            except Exception:
                pass  # could not get it from template!

        try:
            if module == 'auto':
                facts = self._execute_module(module_name='setup', module_args=dict(gather_subset='!all', filter='ansible_service_mgr'), task_vars=task_vars)
                self._display.debug("Facts %s" % facts)
                module = facts.get('ansible_facts', {}).get('ansible_service_mgr', 'auto')

            if not module or module == 'auto' or module not in self._shared_loader_obj.module_loader:
                module = 'service'

            if module != 'auto':
                # run the 'service' module
                new_module_args = self._task.args.copy()
                if 'use' in new_module_args:
                    del new_module_args['use']

                if module in self.UNUSED_PARAMS:
                    for unused in self.UNUSED_PARAMS[module]:
                        if unused in new_module_args:
                            del new_module_args[unused]
                            self._display.warning('Ignoring "%s" as it is not used in "%s"' % (unused, module))

                # get defaults for specific module
                new_module_args = get_action_args_with_defaults(module, new_module_args, self._task.module_defaults, self._templar)

                self._display.vvvv("Running %s" % module)
                result.update(self._execute_module(module_name=module, module_args=new_module_args, task_vars=task_vars, wrap_async=self._task.async_val))
            else:
                raise AnsibleActionFail('Could not detect which service manager to use. Try gathering facts or setting the "use" option.')

        except AnsibleAction as e:
            result.update(e.result)
        finally:
            if not self._task.async_val:
                self._remove_tmp_path(self._connection._shell.tmpdir)

        return result
