# (c) 2018, Red Hat Inc.
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
from ansible.plugins.action import ActionBase

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        '''
        Action plugin handler for yum3 vs yum4(dnf) operations

        In the past, there was only yum which is now known as yum3 or yum 3.x
        but now there is a "new yum" known as yum4 or yum 4.x which is actually
        just a yum command-line compatibility layer on top of dnf and since the
        Ansible modules for yum(aka yum3) and dnf(aka yum4) call each of yum3
        and yum4's python APIs natively on the backend, we need to handle this
        here and pass off to the correct Ansible module to execute on the remote
        system
        '''

        self._supports_check_mode = True
        self._supports_async = True

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        # Carry-over concept from the package action plugin
        module = "auto"

        try:
            if self._task.delegate_to:  # if we delegate, we should use delegated host's facts
                module = self._templar.template("{{hostvars['%s']['ansible_facts']['pkg_mgr']}}" % self._task.delegate_to)
            else:
                module = self._templar.template("{{ansible_facts.pkg_mgr}}")
        except Exception:
            pass  # could not get it from template!

        try:
            if module not in ["yum", "yum4", "dnf"]:
                facts = self._execute_module(module_name="setup", module_args=dict(filter="ansible_pkg_mgr", gather_subset="!all"), task_vars=task_vars)
                display.debug("Facts %s" % facts)
                module = facts.get("ansible_facts", {}).get("ansible_pkg_mgr", "auto")

            if module != "auto":

                if module == "yum4":
                    module = "dnf"

                if module not in self._shared_loader_obj.module_loader:
                    raise AnsibleActionFail("Could not find a yum module backend for %s." % module)
                else:
                    # run either the yum (yum3) or dnf (yum4) backend module
                    new_module_args = self._task.args.copy()

                    display.vvvv("Running %s as the backend for the yum action plugin" % module)
                    result.update(self._execute_module(module_name=module, module_args=new_module_args, task_vars=task_vars, wrap_async=self._task.async_val))
            else:
                raise AnsibleActionFail("Could not detect which major revision of yum is in use, which is required to determine module backend.")

        except AnsibleAction as e:
            result.update(e.result)
        finally:
            if not self._task.async_val:
                # remove a temporary path we created
                self._remove_tmp_path(self._connection._shell.tmpdir)

        return result
