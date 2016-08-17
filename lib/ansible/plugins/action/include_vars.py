# (c) 2013-2014, Benno Joy <benno@ansible.com>
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

from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.utils.unicode import to_str

class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):

        varname = self._task.args.get('name')
        source = self._task.args.get('file')
        if not source:
            source = self._task.args.get('_raw_params')
            if source is None:
                raise AnsibleError("No filename was found for the included vars. " + \
                                   "Use `- include_vars: <filename>` or the `file:` option " + \
                                   "to specify the vars filename.", self._task._ds)

        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        try:
            source = self._find_needle('vars', source)
        except AnsibleError as e:
            result['failed'] = True
            result['message'] = to_str(e)
            return result

        (data, show_content) = self._loader._get_file_contents(source)
        data = self._loader.load(data, show_content)
        if data is None:
            data = {}
        if not isinstance(data, dict):
            result['failed'] = True
            result['message'] = "%s must be stored as a dictionary/hash" % source
        else:
            if varname:
                scope = {}
                scope[varname] = data
                data = scope
            result['ansible_facts'] = data
            result['_ansible_no_log'] = not show_content

        return result
