# Copyright 2012, Dag Wieers <dag@wieers.com>
# Copyright 2016, Toshio Kuratomi <tkuratomi@ansible.com>
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

from ansible.errors import AnsibleUndefinedVariable
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_text
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    ''' Print statements during execution '''

    TRANSFERS_FILES = False
    VALID_ARGS = frozenset(('msg', 'var', 'verbosity'))

    def _run_templar(self, value):
        try:
            result = self._templar.template(value, convert_bare=True, fail_on_undefined=True, bare_deprecated=False)
            if result == value:
                # if result is not str/unicode type, raise an exception
                if not isinstance(result, string_types):
                    raise AnsibleUndefinedVariable
                # If var name is same as result, try to template it
                result = self._templar.template("{{" + result + "}}", convert_bare=True, fail_on_undefined=True)
            return result
        except AnsibleUndefinedVariable:
            return 'VARIABLE IS NOT DEFINED!'

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        for arg in self._task.args:
            if arg not in self.VALID_ARGS:
                return {"failed": True, "msg": "'%s' is not a valid option in debug" % arg}

        if 'msg' in self._task.args and 'var' in self._task.args:
            return {"failed": True, "msg": "'msg' and 'var' are incompatible options"}

        result = super(ActionModule, self).run(tmp, task_vars)

        verbosity = 0
        # get task verbosity
        if 'verbosity' in self._task.args:
            verbosity = int(self._task.args['verbosity'])

        if verbosity <= self._display.verbosity:
            if 'msg' in self._task.args:
                result['msg'] = self._task.args['msg']

            elif 'var' in self._task.args:
                var = self._task.args['var']
                if isinstance(var, dict):
                    result.update((k, self._run_templar(v)) for k, v in var.items())
                elif isinstance(var, list):
                    result.update((v, self._run_templar(v)) for v in var)
                else:
                    result[var] = self._run_templar(var)
            else:
                result['msg'] = 'Hello world!'

            # force flag to make debug output module always verbose
            result['_ansible_verbose_always'] = True
        else:
            result['skipped_reason'] = "Verbosity threshold not met."
            result['skipped'] = True

        return result
