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

from ansible import constants as C
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

        if not tmp:
            tmp = self._make_tmp_path()

        creates = self._task.args.get('creates')
        if creates:
            # do not run the command if the line contains creates=filename
            # and the filename already exists. This allows idempotence
            # of command executions.
            res = self._execute_module(module_name='stat', module_args=dict(path=creates), task_vars=task_vars, tmp=tmp, persist_files=True)
            stat = res.get('stat', None)
            if stat and stat.get('exists', False):
                return dict(skipped=True, msg=("skipped, since %s exists" % creates))

        removes = self._task.args.get('removes')
        if removes:
            # do not run the command if the line contains removes=filename
            # and the filename does not exist. This allows idempotence
            # of command executions.
            res = self._execute_module(module_name='stat', module_args=dict(path=removes), task_vars=task_vars, tmp=tmp, persist_files=True)
            stat = res.get('stat', None)
            if stat and not stat.get('exists', False):
                return dict(skipped=True, msg=("skipped, since %s does not exist" % removes))

        # the script name is the first item in the raw params, so we split it
        # out now so we know the file name we need to transfer to the remote,
        # and everything else is an argument to the script which we need later
        # to append to the remote command
        parts  = self._task.args.get('_raw_params', '').strip().split()
        source = parts[0]
        args   = ' '.join(parts[1:])

        if self._task._role is not None:
            source = self._loader.path_dwim_relative(self._task._role._role_path, 'files', source)
        else:
            source = self._loader.path_dwim_relative(self._loader.get_basedir(), 'files', source)

        # transfer the file to a remote tmp location
        tmp_src = self._connection._shell.join_path(tmp, os.path.basename(source))
        self._connection.put_file(source, tmp_src)

        sudoable = True
        # set file permissions, more permissive when the copy is done as a different user
        if self._play_context.become and self._play_context.become_user != 'root':
            chmod_mode = 'a+rx'
            sudoable = False
        else:
            chmod_mode = '+rx'
        self._remote_chmod(chmod_mode, tmp_src, sudoable=sudoable)

        # add preparation steps to one ssh roundtrip executing the script
        env_string = self._compute_environment_string()
        script_cmd = ' '.join([env_string, tmp_src, args])

        result.update(self._low_level_execute_command(cmd=script_cmd, sudoable=True))

        # clean up after
        if tmp and "tmp" in tmp and not C.DEFAULT_KEEP_REMOTE_FILES:
            self._remove_tmp_path(tmp)

        result['changed'] = True

        return result
