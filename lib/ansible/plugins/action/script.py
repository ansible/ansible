# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    TRANSFERS_FILES = True

    def run(self, tmp=None, task_vars=None):
        ''' handler for file transfer operations '''
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
            self._cleanup_remote_tmp = True

        creates = self._task.args.get('creates')
        if creates:
            # do not run the command if the line contains creates=filename
            # and the filename already exists. This allows idempotence
            # of command executions.
            if self._remote_file_exists(creates):
                self._remove_tmp_path(tmp)
                return dict(skipped=True, msg=("skipped, since %s exists" % creates))

        removes = self._task.args.get('removes')
        if removes:
            # do not run the command if the line contains removes=filename
            # and the filename does not exist. This allows idempotence
            # of command executions.
            if not self._remote_file_exists(removes):
                self._remove_tmp_path(tmp)
                return dict(skipped=True, msg=("skipped, since %s does not exist" % removes))

        # the script name is the first item in the raw params, so we split it
        # out now so we know the file name we need to transfer to the remote,
        # and everything else is an argument to the script which we need later
        # to append to the remote command
        parts  = self._task.args.get('_raw_params', '').strip().split()
        source = parts[0]
        args   = ' '.join(parts[1:])

        try:
            source = self._loader.get_real_file(self._find_needle('files', source))
        except AnsibleError as e:
            return dict(failed=True, msg=to_native(e))

        # transfer the file to a remote tmp location
        tmp_src = self._connection._shell.join_path(tmp, os.path.basename(source))
        self._transfer_file(source, tmp_src)

        # set file permissions, more permissive when the copy is done as a different user
        self._fixup_perms2((tmp, tmp_src), remote_user, execute=True)

        # add preparation steps to one ssh roundtrip executing the script
        env_string = self._compute_environment_string()
        script_cmd = ' '.join([env_string, tmp_src, args])

        result.update(self._low_level_execute_command(cmd=script_cmd, sudoable=True))

        # clean up after
        self._remove_tmp_path(tmp)

        result['changed'] = True

        return result
