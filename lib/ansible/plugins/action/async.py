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
from ansible.utils.unicode import to_unicode

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
        async_module_path  = self._connection._shell.join_path(tmp, 'async_wrapper')
        remote_module_path = self._connection._shell.join_path(tmp, module_name)

        env_string = self._compute_environment_string()

        module_args = self._task.args.copy()
        if self._play_context.no_log or C.DEFAULT_NO_TARGET_SYSLOG:
            module_args['_ansible_no_log'] = True

        # configure, upload, and chmod the target module
        (module_style, shebang, module_data) = self._configure_module(module_name=module_name, module_args=module_args, task_vars=task_vars)
        self._transfer_data(remote_module_path, module_data)

        # configure, upload, and chmod the async_wrapper module
        (async_module_style, shebang, async_module_data) = self._configure_module(module_name='async_wrapper', module_args=dict(), task_vars=task_vars)
        self._transfer_data(async_module_path, async_module_data)

        argsfile = None
        if module_style == 'non_native_want_json':
            argsfile = self._transfer_data(self._connection._shell.join_path(tmp, 'arguments'), json.dumps(module_args))
        elif module_style == 'old':
            args_data = ""
            for k, v in iteritems(module_args):
                args_data += '%s="%s" ' % (k, pipes.quote(to_unicode(v)))
            argsfile = self._transfer_data(self._connection._shell.join_path(tmp, 'arguments'), args_data)

        self._fixup_perms(tmp, remote_user, execute=True, recursive=True)
        # Only the following two files need to be executable but we'd have to
        # make three remote calls if we wanted to just set them executable.
        # There's not really a problem with marking too many of the temp files
        # executable so we go ahead and mark them all as executable in the
        # line above (the line above is needed in any case [although
        # execute=False is okay if we uncomment the lines below] so that all
        # the files are readable in case the remote_user and become_user are
        # different and both unprivileged)
        #self._fixup_perms(remote_module_path, remote_user, execute=True, recursive=False)
        #self._fixup_perms(async_module_path, remote_user, execute=True, recursive=False)

        async_limit = self._task.async
        async_jid   = str(random.randint(0, 999999999999))

        async_cmd = [env_string, async_module_path, async_jid, async_limit, remote_module_path]
        if argsfile:
            async_cmd.append(argsfile)
        async_cmd = " ".join([to_unicode(x) for x in async_cmd])
        result.update(self._low_level_execute_command(cmd=async_cmd))

        # clean up after
        self._remove_tmp_path(tmp)

        result['changed'] = True

        return result
