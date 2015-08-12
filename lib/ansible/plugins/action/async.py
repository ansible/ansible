# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

import json
import random

from ansible import constants as C
from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=dict()):
        ''' transfer the given module name, plus the async module, then run it '''

        if self._play_context.check_mode:
            return dict(skipped=True, msg='check mode not supported for this module')

        if not tmp:
            tmp = self._make_tmp_path()

        module_name = self._task.action
        async_module_path  = self._connection._shell.join_path(tmp, 'async_wrapper')
        remote_module_path = self._connection._shell.join_path(tmp, module_name)

        env_string = self._compute_environment_string()

        # configure, upload, and chmod the target module
        (module_style, shebang, module_data) = self._configure_module(module_name=module_name, module_args=self._task.args, task_vars=task_vars)
        self._transfer_data(remote_module_path, module_data)
        self._remote_chmod(tmp, 'a+rx', remote_module_path)

        # configure, upload, and chmod the async_wrapper module
        (async_module_style, shebang, async_module_data) = self._configure_module(module_name='async_wrapper', module_args=dict(), task_vars=task_vars)
        self._transfer_data(async_module_path, async_module_data)
        self._remote_chmod(tmp, 'a+rx', async_module_path)

        argsfile = self._transfer_data(self._connection._shell.join_path(tmp, 'arguments'), json.dumps(self._task.args))

        async_limit = self._task.async
        async_jid   = str(random.randint(0, 999999999999))

        async_cmd = " ".join([str(x) for x in [async_module_path, async_jid, async_limit, remote_module_path, argsfile]])
        result = self._low_level_execute_command(cmd=async_cmd, tmp=None)

        # clean up after
        if tmp and "tmp" in tmp and not C.DEFAULT_KEEP_REMOTE_FILES:
            self._remove_tmp_path(tmp)

        result['changed'] = True

        return result


