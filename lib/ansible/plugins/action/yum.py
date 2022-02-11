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

from ansible.errors import AnsibleActionFail
from ansible.module_utils.common.arg_spec import ArgumentSpecValidator
from ansible.module_utils.errors import UnsupportedError
from ansible.module_utils.yumdnf import yumdnf_argument_spec
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()

VALID_BACKENDS = frozenset(('yum', 'yum4', 'dnf'))


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    def validate_argument_spec(self, argument_spec=None,
                               mutually_exclusive=None,
                               required_together=None,
                               required_one_of=None,
                               required_if=None,
                               required_by=None,
                               ):
        # We should probably put this on ActionBase

        new_module_args = self._task.args.copy()

        validator = ArgumentSpecValidator(
            argument_spec,
            mutually_exclusive=mutually_exclusive,
            required_together=required_together,
            required_one_of=required_one_of,
            required_if=required_if,
            required_by=required_by,
        )
        validation_result = validator.validate(new_module_args)

        new_module_args.update(validation_result.validated_parameters)

        try:
            error = validation_result.errors[0]
        except IndexError:
            error = None

        # Fail for validation errors, even in check mode
        if error:
            msg = validation_result.errors.msg
            if isinstance(error, UnsupportedError):
                msg = "Unsupported parameters for ({name}) {kind}: {msg}".format(name=self._load_name, kind='module', msg=msg)

            raise AnsibleActionFail(msg)

        return validation_result, new_module_args


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

        yumdnf_argument_spec.pop('supports_check_mode', None)
        yumdnf_argument_spec['argument_spec']['use_backend'] = dict(default='auto', choices=['auto', 'yum', 'yum4', 'dnf'], aliases=['use'])

        validation_result, new_module_args = self.validate_argument_spec(**yumdnf_argument_spec)

        module = new_module_args.get('use_backend', 'auto')

        if module == 'auto':
            try:
                if self._task.delegate_to:  # if we delegate, we should use delegated host's facts
                    module = self._templar.template("{{hostvars['%s']['ansible_facts']['pkg_mgr']}}" % self._task.delegate_to)
                else:
                    module = self._templar.template("{{ansible_facts.pkg_mgr}}")
            except Exception:
                pass  # could not get it from template!

        if module not in VALID_BACKENDS:
            facts = self._execute_module(
                module_name="ansible.legacy.setup", module_args=dict(filter="ansible_pkg_mgr", gather_subset="!all"),
                task_vars=task_vars)
            display.debug("Facts %s" % facts)
            module = facts.get("ansible_facts", {}).get("ansible_pkg_mgr", "auto")
            if (not self._task.delegate_to or self._task.delegate_facts) and module != 'auto':
                result['ansible_facts'] = {'pkg_mgr': module}

        if module not in VALID_BACKENDS:
            result.update(
                {
                    'failed': True,
                    'msg': ("Could not detect which major revision of yum is in use, which is required to determine module backend.",
                            "You should manually specify use_backend to tell the module whether to use the yum (yum3) or dnf (yum4) backend})"),
                }
            )

        else:
            if module == "yum4":
                module = "dnf"

            # eliminate collisions with collections search while still allowing local override
            module = 'ansible.legacy.' + module

            if not self._shared_loader_obj.module_loader.has_plugin(module):
                result.update({'failed': True, 'msg': "Could not find a yum module backend for %s." % module})
            else:
                # run either the yum (yum3) or dnf (yum4) backend module
                new_module_args.pop('use', None)

                display.vvvv("Running %s as the backend for the yum action plugin" % module)
                result.update(self._execute_module(
                    module_name=module, module_args=new_module_args, task_vars=task_vars, wrap_async=self._task.async_val))

        # Cleanup
        if not self._task.async_val:
            # remove a temporary path we created
            self._remove_tmp_path(self._connection._shell.tmpdir)

        return result
