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

class ActionModule(ActionBase):
    ''' Print statements during execution '''

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        if 'msg' in self._task.args:
            if 'fail' in self._task.args and boolean(self._task.args['fail']):
                result['failed'] = True
                result['msg'] = self._task.args['msg']
            else:
                result['msg'] = self._task.args['msg']
        # FIXME: move the LOOKUP_REGEX somewhere else
        elif 'var' in self._task.args: # and not utils.LOOKUP_REGEX.search(self._task.args['var']):
            results = self._templar.template(self._task.args['var'], convert_bare=True, fail_on_undefined=False)
            if type(self._task.args['var']) in (list, dict):
                # If var is a list or dict, use the type as key to display
                result[to_unicode(type(self._task.args['var']))] = results
            else:
                # If var name is same as result, try to template it
                if results == self._task.args['var']:
                    try:
                        results = self._templar.template("{{" + results + "}}", convert_bare=True, fail_on_undefined=True)
                    except:
                        results = "VARIABLE IS NOT DEFINED!"
                result[self._task.args['var']] = results
        else:
            result['msg'] = 'here we are'

        # force flag to make debug output module always verbose
        result['_ansible_verbose_always'] = True

        return result
