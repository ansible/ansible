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
    _VALID_ARGS = frozenset(('msg', 'var', 'verbosity'))

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        if 'msg' in self._task.args and 'var' in self._task.args:
            return {"failed": True, "msg": "'msg' and 'var' are incompatible options"}

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        # get task verbosity
        verbosity = int(self._task.args.get('verbosity', 0))

        if verbosity <= self._display.verbosity:
            if 'msg' in self._task.args:
                result['msg'] = self._task.args['msg']

            elif 'var' in self._task.args:
                try:
                    results = self._templar.template(self._task.args['var'], convert_bare=True, fail_on_undefined=True)
                    if results == self._task.args['var']:
                        # if results is not str/unicode type, raise an exception
                        if not isinstance(results, string_types):
                            raise AnsibleUndefinedVariable
                        # If var name is same as result, try to template it
                        results = self._templar.template("{{" + results + "}}", convert_bare=True, fail_on_undefined=True)
                except AnsibleUndefinedVariable as e:
                    results = u"VARIABLE IS NOT DEFINED!"
                    if self._display.verbosity > 0:
                        results += u": %s" % to_text(e)

                if isinstance(self._task.args['var'], (list, dict)):
                    # If var is a list or dict, use the type as key to display
                    result[to_text(type(self._task.args['var']))] = results
                else:
                    result[self._task.args['var']] = results
            else:
                result['msg'] = 'Hello world!'

            # force flag to make debug output module always verbose
            result['_ansible_verbose_always'] = True
        else:
            result['skipped_reason'] = "Verbosity threshold not met."
            result['skipped'] = True

        result['failed'] = False

        return result
