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
import pipes
import random

from ansible import constants as C
from ansible.compat.six import iteritems
from ansible.module_utils._text import to_text
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        ''' transfer the given module name, plus the async module, then run it '''
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        if self._play_context.check_mode:
            result['skipped'] = True
            result['msg'] = 'check mode not supported for this module'
            return result

        remote_user = task_vars.get('ansible_ssh_user') or self._play_context.remote_user
        if not tmp:
            tmp = self._make_tmp_path(remote_user)
            self._cleanup_remote_tmp=True

        module_name = self._task.action



        env_string = self._compute_environment_string()

        module_args = self._task.args.copy()
        if self._play_context.no_log or C.DEFAULT_NO_TARGET_SYSLOG:
            module_args['_ansible_no_log'] = True

        # configure, upload, and chmod the target module
        (module_style, shebang, module_data, module_path) = self._configure_module(module_name=module_name, module_args=module_args, task_vars=task_vars)
        remote_module_filename = self._connection._shell.get_remote_filename(module_path)
        remote_module_path = self._connection._shell.join_path(tmp, remote_module_filename)
        if module_style == 'binary':
            self._transfer_file(module_path, remote_module_path)
        else:
            self._transfer_data(remote_module_path, module_data)

        # configure, upload, and chmod the async_wrapper module
        (async_module_style, shebang, async_module_data, async_module_path) = self._configure_module(module_name='async_wrapper', module_args=dict(), task_vars=task_vars)
        async_module_remote_filename = self._connection._shell.get_remote_filename(async_module_path)
        remote_async_module_path = self._connection._shell.join_path(tmp, async_module_remote_filename)
        self._transfer_data(remote_async_module_path, async_module_data)

        argsfile = None
        if module_style in ('non_native_want_json', 'binary'):
            argsfile = self._transfer_data(self._connection._shell.join_path(tmp, 'arguments'), json.dumps(module_args))
        elif module_style == 'old':
            args_data = ""
            for k, v in iteritems(module_args):
                args_data += '%s="%s" ' % (k, pipes.quote(to_text(v)))
            argsfile = self._transfer_data(self._connection._shell.join_path(tmp, 'arguments'), args_data)

        remote_paths = tmp, remote_module_path, remote_async_module_path

        # argsfile doesn't need to be executable, but this saves an extra call to the remote host
        if argsfile:
            remote_paths += argsfile,

        self._fixup_perms2(remote_paths, remote_user, execute=True)

        async_limit = self._task.async
        async_jid   = str(random.randint(0, 999999999999))

        async_cmd = [env_string, remote_async_module_path, async_jid, async_limit, remote_module_path]
        if argsfile:
            async_cmd.append(argsfile)
        else:
            # maintain a fixed number of positional parameters for async_wrapper
            async_cmd.append('_')

        if not self._should_remove_tmp_path(tmp):
            async_cmd.append("-preserve_tmp")

        async_cmd = " ".join(to_text(x) for x in async_cmd)
        result.update(self._low_level_execute_command(cmd=async_cmd))

        result['changed'] = True

        # the async_wrapper module returns dumped JSON via its stdout
        # response, so we (attempt to) parse it here
        parsed_result = self._parse_returned_data(result)

        # Delete tmpdir from controller unless async_wrapper says something else will do it.
        # Windows cannot request deletion of files/directories that are in use, so the async
        # supervisory process has to be responsible for it.
        if parsed_result.get("_suppress_tmpdir_delete", False) != True:
            self._remove_tmp_path(tmp)

        # just return the original result
        if 'skipped' in result and result['skipped'] or 'failed' in result and result['failed']:
            return result

        return parsed_result
