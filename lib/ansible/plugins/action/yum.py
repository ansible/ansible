# (c) 2018, Ansible Project
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
from ansible.utils.display import Display

display = Display()


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        '''
        Action plugin handler for yum3 vs yum4(dnf) operations.

        Enables the yum module to use yum3 and/or yum4. Yum4 is a yum
        command-line compatibility layer on top of dnf. Since the Ansible
        modules for yum(aka yum3) and dnf(aka yum4) call each of yum3 and yum4's
        python APIs natively on the backend, we need to handle this here and
        pass off to the correct Ansible module to execute on the remote system.
        '''

        self._supports_check_mode = True
        self._supports_async = True

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        # Carry-over concept from the package action plugin
        module = self._task.args.get('use_backend', "auto")

        if module == 'auto':
            try:
                if self._task.delegate_to:  # if we delegate, we should use delegated host's facts
                    module = self._templar.template("{{hostvars['%s']['ansible_facts']['pkg_mgr']}}" % self._task.delegate_to)
                else:
                    module = self._templar.template("{{ansible_facts.pkg_mgr}}")
            except Exception:
                pass  # could not get it from template!

        if module not in ["yum", "yum4", "dnf"]:
            facts = self._execute_module(module_name="setup", module_args=dict(filter="ansible_pkg_mgr", gather_subset="!all"), task_vars=task_vars)
            display.debug("Facts %s" % facts)
            module = facts.get("ansible_facts", {}).get("ansible_pkg_mgr", "auto")
            if (not self._task.delegate_to or self._task.delegate_facts) and module != 'auto':
                result['ansible_facts'] = {'pkg_mgr': module}

        if module != "auto":

            if module == "yum4":
                module = "dnf"

            if module not in self._shared_loader_obj.module_loader:
                result.update({'failed': True, 'msg': "Could not find a yum module backend for %s." % module})
            else:
                # run either the yum (yum3) or dnf (yum4) backend module
                new_module_args = self._task.args.copy()
                if 'use_backend' in new_module_args:
                    del new_module_args['use_backend']

                display.vvvv("Running %s as the backend for the yum action plugin" % module)
                result.update(self._execute_module(module_name=module, module_args=new_module_args, task_vars=task_vars, wrap_async=self._task.async_val))
                # Now fall through to cleanup
        else:
            result.update(
                {
                    'failed': True,
                    'msg': ("Could not detect which major revision of yum is in use, which is required to determine module backend.",
                            "You can manually specify use_backend to tell the module whether to use the yum (yum3) or dnf (yum4) backend})"),
                }
            )
            # Now fall through to cleanup

        # Cleanup
        if not self._task.async_val:
            # remove a temporary path we created
            self._remove_tmp_path(self._connection._shell.tmpdir)

        return result
