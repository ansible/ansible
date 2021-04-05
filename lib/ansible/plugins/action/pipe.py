"""
Copyright (C) 2021 LoveIsGrief
GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import subprocess

from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_bytes, to_native
from ansible.plugins.action import ActionBase
from ansible.utils.shlex import shlex_split


class ActionModule(ActionBase):
    _VALID_ARGS = frozenset([
        'local',
        'remote',
    ])

    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)

        local_command = self._task.args['local']
        remote_command = self._task.args['remote']
        try:
            local_proc = subprocess.Popen(
                shlex_split(local_command),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                # bufsize=0,
            )
        except Exception as e:
            raise AnsibleError(
                'Could not execute local command(%s): %s' % (
                    to_native(local_command),
                    to_native(e),
                )
            )

        try:
            dest_return_code, dest_stdout, dest_stderr = self._connection.exec_command(
                to_bytes(remote_command),
                in_data=local_proc.stdout,
            )
        except Exception as e:
            raise AnsibleError('Could not execute remote command: %s' % to_native(e))

        local_proc.wait(timeout=5)
        return {
            'src': {
                'return_code': local_proc.returncode,
            },
            'dest': {
                'return_code': dest_return_code,
            }
        }
