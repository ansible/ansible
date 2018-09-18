# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2018, Will Thames <will@thames.id.au>
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

import os

from ansible.errors import AnsibleError, AnsibleAction, AnsibleActionFail, AnsibleFileNotFound
from ansible.module_utils._text import to_text
from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash


class ActionModule(ActionBase):

    TRANSFERS_FILES = True

    def run(self, tmp=None, task_vars=None):
        ''' handler for aws_s3 operations '''
        self._supports_async = True

        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        source = self._task.args.get('src', None)

        try:
            new_module_args = self._task.args.copy()
            if source:
                source = os.path.expanduser(source)

                # For backward compatibility check if the file exists on the remote; it should take precedence
                if not self._remote_file_exists(source):
                    try:
                        source = self._loader.get_real_file(self._find_needle('files', source), decrypt=False)
                        new_module_args['src'] = source
                    except AnsibleFileNotFound as e:
                        # module handles error message for nonexistent files
                        new_module_args['src'] = source
                    except AnsibleError as e:
                        raise AnsibleActionFail(to_text(e))

            wrap_async = self._task.async_val and not self._connection.has_native_async
            # execute the aws_s3 module with the updated args
            result = merge_hash(result, self._execute_module(module_args=new_module_args, task_vars=task_vars, wrap_async=wrap_async))

            if not wrap_async:
                # remove a temporary path we created
                self._remove_tmp_path(self._connection._shell.tmpdir)

        except AnsibleAction as e:
            result.update(e.result)
        return result
