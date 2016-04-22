# Copyright 2012, Dag Wieers <dag@wieers.com>
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
from ansible.utils.boolean import boolean
from ansible.utils.unicode import to_unicode
from ansible.errors import AnsibleUndefinedVariable

class ActionModule(ActionBase):
    ''' Print statements during execution '''

    TRANSFERS_FILES = False
    VALID_ARGS = set(['msg', 'var', 'verbosity'])

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
                try:
                    results = self._templar.template(self._task.args['var'], convert_bare=True, fail_on_undefined=True, bare_deprecated=False)
                    if results == self._task.args['var']:
                        raise AnsibleUndefinedVariable
                except AnsibleUndefinedVariable:
                    results = "VARIABLE IS NOT DEFINED!"

                if type(self._task.args['var']) in (list, dict):
                    # If var is a list or dict, use the type as key to display
                    result[to_unicode(type(self._task.args['var']))] = results
                else:
                    result[self._task.args['var']] = results
            else:
                result['msg'] = 'Hello world!'

            # force flag to make debug output module always verbose
            result['_ansible_verbose_always'] = True
        else:
            result['skipped'] = True

        return result
