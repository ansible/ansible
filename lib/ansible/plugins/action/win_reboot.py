# Copyright: (c) 2018, Matt Davis <mdavis@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from datetime import datetime

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native
from ansible.plugins.action import ActionBase
from ansible.plugins.action.reboot import ActionModule as RebootActionModule
from ansible.utils.display import Display

display = Display()


class TimedOutException(Exception):
    pass


class ActionModule(RebootActionModule, ActionBase):
    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset((
        'connect_timeout', 'connect_timeout_sec', 'msg', 'post_reboot_delay', 'post_reboot_delay_sec', 'pre_reboot_delay', 'pre_reboot_delay_sec',
        'reboot_timeout', 'reboot_timeout_sec', 'shutdown_timeout', 'shutdown_timeout_sec', 'test_command',
    ))

    DEFAULT_BOOT_TIME_COMMAND = "(Get-WmiObject -ClassName Win32_OperatingSystem).LastBootUpTime"
    DEFAULT_CONNECT_TIMEOUT = 5
    DEFAULT_PRE_REBOOT_DELAY = 2
    DEFAULT_SUDOABLE = False
    DEFAULT_SHUTDOWN_COMMAND_ARGS = '/r /t {delay_sec} /c "{message}"'

    DEPRECATED_ARGS = {
        'shutdown_timeout': '2.5',
        'shutdown_timeout_sec': '2.5',
    }

    def __init__(self, *args, **kwargs):
        super(ActionModule, self).__init__(*args, **kwargs)

    def get_distribution(self, task_vars):
        return {'name': 'windows', 'version': '', 'family': ''}

    def get_shutdown_command(self, task_vars, distribution):
        return self.DEFAULT_SHUTDOWN_COMMAND

    def run_test_command(self, distribution, **kwargs):
        # Need to wrap the test_command in our PowerShell encoded wrapper. This is done to align the command input to a
        # common shell and to allow the psrp connection plugin to report the correct exit code without manually setting
        # $LASTEXITCODE for just that plugin.
        test_command = self._task.args.get('test_command', self.DEFAULT_TEST_COMMAND)
        kwargs['test_command'] = self._connection._shell._encode_script(test_command)
        super(ActionModule, self).run_test_command(distribution, **kwargs)

    def perform_reboot(self, task_vars, distribution):
        shutdown_command = self.get_shutdown_command(task_vars, distribution)
        shutdown_command_args = self.get_shutdown_command_args(distribution)
        reboot_command = self._connection._shell._encode_script('{0} {1}'.format(shutdown_command, shutdown_command_args))

        display.vvv("{action}: rebooting server...".format(action=self._task.action))
        display.debug("{action}: distribution: {dist}".format(action=self._task.action, dist=distribution))
        display.debug("{action}: rebooting server with command '{command}'".format(action=self._task.action, command=reboot_command))

        result = {}
        reboot_result = self._low_level_execute_command(reboot_command, sudoable=self.DEFAULT_SUDOABLE)
        result['start'] = datetime.utcnow()

        # Test for "A system shutdown has already been scheduled. (1190)" and handle it gracefully
        stdout = reboot_result['stdout']
        stderr = reboot_result['stderr']
        if reboot_result['rc'] == 1190 or (reboot_result['rc'] != 0 and "(1190)" in reboot_result['stderr']):
            display.warning('A scheduled reboot was pre-empted by Ansible.')

            # Try to abort (this may fail if it was already aborted)
            result1 = self._low_level_execute_command(self._connection._shell._encode_script('shutdown /a'),
                                                      sudoable=self.DEFAULT_SUDOABLE)

            # Initiate reboot again
            result2 = self._low_level_execute_command(reboot_command, sudoable=self.DEFAULT_SUDOABLE)

            reboot_result['rc'] = result2['rc']
            stdout += result1['stdout'] + result2['stdout']
            stderr += result1['stderr'] + result2['stderr']

        if reboot_result['rc'] != 0:
            result['failed'] = True
            result['rebooted'] = False
            result['msg'] = "Reboot command failed, error was: {stdout} {stderr}".format(
                stdout=to_native(stdout.strip()),
                stderr=to_native(stderr.strip()))
            return result

        result['failed'] = False
        return result
