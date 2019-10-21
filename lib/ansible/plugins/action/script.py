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
import re
import shlex

from ansible.errors import AnsibleError, AnsibleAction, _AnsibleActionDone, AnsibleActionFail, AnsibleActionSkip
from ansible.executor.powershell import module_manifest as ps_manifest
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    TRANSFERS_FILES = True

    # On Windows platform, absolute paths begin with a (back)slash
    # after chopping off a potential drive letter.
    windows_absolute_path_detection = re.compile(r'^(?:[a-zA-Z]\:)?(\\|\/)')

    def run(self, tmp=None, task_vars=None):
        ''' handler for file transfer operations '''
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        try:
            creates = self._task.args.get('creates')
            if creates:
                # do not run the command if the line contains creates=filename
                # and the filename already exists. This allows idempotence
                # of command executions.
                if self._remote_file_exists(creates):
                    raise AnsibleActionSkip("%s exists, matching creates option" % creates)

            removes = self._task.args.get('removes')
            if removes:
                # do not run the command if the line contains removes=filename
                # and the filename does not exist. This allows idempotence
                # of command executions.
                if not self._remote_file_exists(removes):
                    raise AnsibleActionSkip("%s does not exist, matching removes option" % removes)

            # The chdir must be absolute, because a relative path would rely on
            # remote node behaviour & user config.
            chdir = self._task.args.get('chdir')
            if chdir:
                # Powershell is the only Windows-path aware shell
                if getattr(self._connection._shell, "_IS_WINDOWS", False) and \
                        not self.windows_absolute_path_detection.match(chdir):
                    raise AnsibleActionFail('chdir %s must be an absolute path for a Windows remote node' % chdir)
                # Every other shell is unix-path-aware.
                if not getattr(self._connection._shell, "_IS_WINDOWS", False) and not chdir.startswith('/'):
                    raise AnsibleActionFail('chdir %s must be an absolute path for a Unix-aware remote node' % chdir)

            # Split out the script as the first item in raw_params using
            # shlex.split() in order to support paths and files with spaces in the name.
            # Any arguments passed to the script will be added back later.
            raw_params = to_native(self._task.args.get('_raw_params', ''), errors='surrogate_or_strict')
            parts = [to_text(s, errors='surrogate_or_strict') for s in shlex.split(raw_params.strip())]
            source = parts[0]

            # Support executable paths and files with spaces in the name.
            executable = to_native(self._task.args.get('executable', ''), errors='surrogate_or_strict')

            try:
                source = self._loader.get_real_file(self._find_needle('files', source), decrypt=self._task.args.get('decrypt', True))
            except AnsibleError as e:
                raise AnsibleActionFail(to_native(e))

            # now we execute script, always assume changed.
            result['changed'] = True

            if not self._play_context.check_mode:
                # transfer the file to a remote tmp location
                tmp_src = self._connection._shell.join_path(self._connection._shell.tmpdir,
                                                            os.path.basename(source))

                # Convert raw_params to text for the purpose of replacing the script since
                # parts and tmp_src are both unicode strings and raw_params will be different
                # depending on Python version.
                #
                # Once everything is encoded consistently, replace the script path on the remote
                # system with the remainder of the raw_params. This preserves quoting in parameters
                # that would have been removed by shlex.split().
                target_command = to_text(raw_params).strip().replace(parts[0], tmp_src)

                self._transfer_file(source, tmp_src)

                # set file permissions, more permissive when the copy is done as a different user
                self._fixup_perms2((self._connection._shell.tmpdir, tmp_src), execute=True)

                # add preparation steps to one ssh roundtrip executing the script
                env_dict = dict()
                env_string = self._compute_environment_string(env_dict)

                if executable:
                    script_cmd = ' '.join([env_string, executable, target_command])
                else:
                    script_cmd = ' '.join([env_string, target_command])

            if self._play_context.check_mode:
                raise _AnsibleActionDone()

            script_cmd = self._connection._shell.wrap_for_exec(script_cmd)

            exec_data = None
            # PowerShell runs the script in a special wrapper to enable things
            # like become and environment args
            if getattr(self._connection._shell, "_IS_WINDOWS", False):
                # FUTURE: use a more public method to get the exec payload
                pc = self._play_context
                exec_data = ps_manifest._create_powershell_wrapper(
                    to_bytes(script_cmd), source, {}, env_dict, self._task.async_val,
                    pc.become, pc.become_method, pc.become_user,
                    pc.become_pass, pc.become_flags, "script", task_vars
                )
                # build the necessary exec wrapper command
                # FUTURE: this still doesn't let script work on Windows with non-pipelined connections or
                # full manual exec of KEEP_REMOTE_FILES
                script_cmd = self._connection._shell.build_module_command(env_string='', shebang='#!powershell', cmd='')

            result.update(self._low_level_execute_command(cmd=script_cmd, in_data=exec_data, sudoable=True, chdir=chdir))

            if 'rc' in result and result['rc'] != 0:
                raise AnsibleActionFail('non-zero return code')

        except AnsibleAction as e:
            result.update(e.result)
        finally:
            self._remove_tmp_path(self._connection._shell.tmpdir)

        return result
