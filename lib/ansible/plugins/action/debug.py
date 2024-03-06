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
from __future__ import annotations

from ansible.errors import AnsibleUndefinedVariable
from ansible.module_utils.six import string_types
from ansible.module_utils.common.text.converters import to_text
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    ''' Print statements during execution '''

    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset(('msg', 'var', 'verbosity'))
    _requires_connection = False

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        validation_result, new_module_args = self.validate_argument_spec(
            argument_spec={
                'msg': {'type': 'raw', 'default': 'Hello world!'},
                'var': {'type': 'raw'},
                'verbosity': {'type': 'int', 'default': 0},
            },
            mutually_exclusive=(
                ('msg', 'var'),
            ),
        )

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        # get task verbosity
        verbosity = new_module_args['verbosity']

        if verbosity <= self._display.verbosity:
            if new_module_args['var']:
                try:
                    results = self._templar.template(new_module_args['var'], convert_bare=True, fail_on_undefined=True)
                    if results == new_module_args['var']:
                        # if results is not str/unicode type, raise an exception
                        if not isinstance(results, string_types):
                            raise AnsibleUndefinedVariable
                        # If var name is same as result, try to template it
                        results = self._templar.template("{{" + results + "}}", convert_bare=True, fail_on_undefined=True)
                except AnsibleUndefinedVariable as e:
                    results = u"VARIABLE IS NOT DEFINED!"
                    if self._display.verbosity > 0:
                        results += u": %s" % to_text(e)

                if isinstance(new_module_args['var'], (list, dict)):
                    # If var is a list or dict, use the type as key to display
                    result[to_text(type(new_module_args['var']))] = results
                else:
                    result[new_module_args['var']] = results
            else:
                result['msg'] = new_module_args['msg']

            # force flag to make debug output module always verbose
            result['_ansible_verbose_always'] = True
        else:
            result['skipped_reason'] = "Verbosity threshold not met."
            result['skipped'] = True

        result['failed'] = False

        return result
