# (c) 2015, Brian Coca  <briancoca+dev@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.errors import AnsibleError, AnsibleAction, _AnsibleActionDone, AnsibleActionFail
from ansible.module_utils._text import to_native
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    TRANSFERS_FILES = True

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        src = self._task.args.get('src', None)
        remote_src = boolean(self._task.args.get('remote_src', 'no'), strict=False)

        try:
            if src is None:
                raise AnsibleActionFail("src is required")
            elif remote_src:
                # everything is remote, so we just execute the module
                # without changing any of the module arguments
                raise _AnsibleActionDone(result=self._execute_module(task_vars=task_vars))

            try:
                src = self._find_needle('files', src)
            except AnsibleError as e:
                raise AnsibleActionFail(to_native(e))

            tmp_src = self._connection._shell.join_path(self._connection._shell.tmpdir, os.path.basename(src))
            self._transfer_file(src, tmp_src)
            self._fixup_perms2((self._connection._shell.tmpdir, tmp_src))

            new_module_args = self._task.args.copy()
            new_module_args.update(
                dict(
                    src=tmp_src,
                )
            )

            result.update(self._execute_module('patch', module_args=new_module_args, task_vars=task_vars))
        except AnsibleAction as e:
            result.update(e.result)
        finally:
            self._remove_tmp_path(self._connection._shell.tmpdir)
        return result
