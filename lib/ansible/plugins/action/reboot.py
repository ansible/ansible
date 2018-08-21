# (c) 2018, Matt Davis <mdavis@ansible.com>
# (c) 2018, Sam Doran <sdoran@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import time

from datetime import datetime, timedelta

from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.module_utils._text import to_native


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class TimedOutException(Exception):
    pass


class ActionModule(ActionBase):
    TRANSFERS_FILES = False

    DEFAULT_REBOOT_TIMEOUT = 600
    DEFAULT_CONNECT_TIMEOUT = None
    DEFAULT_PRE_REBOOT_DELAY = 0
    DEFAULT_POST_REBOOT_DELAY = 0
    DEFAULT_TEST_COMMAND = 'whoami'
    DEFAULT_UPTIME_COMMAND = 'uptime'
    DEFAULT_REBOOT_MESSAGE = 'Reboot initiated by Ansible'
    DEFAULT_SHUTDOWN_COMMAND = 'shutdown'
    DEFAULT_SHUTDOWN_COMMAND_ARGS = '-r %d "%s"'
    DEFAULT_SUDOABLE = True

    def deprecated_args(self):
        deprecated_args = self._task.args.get('DEFAULT_DEPRECATED_ARGS')

        if deprecated_args:
            for arg, version in deprecated_args.items():
                if self._task.args.get(arg) is not None:
                    display.warning("Since Ansible %s, %s is no longer a valid option for %s" % (version, arg, self._task.action))

    def construct_command(self):
        self.deprecated_args()

        shutdown_command = str(self.DEFAULT_SHUTDOWN_COMMAND)
        pre_reboot_delay = int(self._task.args.get('pre_reboot_delay', self.DEFAULT_PRE_REBOOT_DELAY))
        msg = str(self._task.args.get('msg', self.DEFAULT_REBOOT_MESSAGE))
        shutdown_command_args = str(self.DEFAULT_SHUTDOWN_COMMAND_ARGS % (pre_reboot_delay, msg))

        reboot_command = '%s %s' % (shutdown_command, shutdown_command_args)
        return reboot_command

    def get_system_uptime(self):
        command_result = self._low_level_execute_command(self.DEFAULT_UPTIME_COMMAND, sudoable=self.DEFAULT_SUDOABLE)

        if command_result['rc'] != 0:
            raise AnsibleError("%s: failed to get host uptime info, rc: %d, stdout: %s, stderr: %s"
                               % (self._task.action, command_result.rc, to_native(command_result['stdout']), to_native(command_result['stderr'])))

        return command_result['stdout'].strip()

    def check_uptime(self, before_uptime):
        display.vvv("Attempting to get system uptime")
        connect_timeout = self._task.args.get('connect_timeout', self.DEFAULT_CONNECT_TIMEOUT)

        # override connection timeout from defaults to custom value
        if connect_timeout:
            try:
                self._connection.set_options(direct={"connection_timeout": connect_timeout})
                self._connection._reset()
            except AttributeError:
                display.warning("Connection plugin does not allow the connection timeout to be overridden")

        # try and get uptime
        try:
            current_uptime = self.get_system_uptime()
        except Exception as e:
            raise e

        if current_uptime == before_uptime:
            raise Exception("uptime has not changed")

    def run_test_command(self, **kwargs):
        test_command = str(self._task.args.get('test_command', self.DEFAULT_TEST_COMMAND))
        display.vvv("Attempting post-reboot test command '%s'" % test_command)
        command_result = self._low_level_execute_command(test_command, sudoable=self.DEFAULT_SUDOABLE)

        result = {}
        if command_result['rc'] != 0:
            result['failed'] = True
            result['msg'] = 'test command failed: %s %s' % (to_native(command_result['stderr'], to_native(command_result['stdout'])))
        else:
            result['msg'] = to_native(command_result['stdout'])

        return result

    def do_until_success_or_timeout(self, action, reboot_timeout, before_uptime, action_desc, fail_sleep=1):
        max_end_time = datetime.utcnow() + timedelta(seconds=reboot_timeout)

        while datetime.utcnow() < max_end_time:
            try:
                action(before_uptime=before_uptime)
                if action_desc:
                    display.debug('%s: %s success' % (self._task.action, action_desc))
                return
            except Exception as e:
                if action_desc:
                    display.debug("%s: %s fail '%s', retrying in %d seconds..." % (self._task.action, action_desc, to_native(e), fail_sleep))
                time.sleep(fail_sleep)

        raise TimedOutException('Timed out waiting for %s' % (action_desc))

    def perform_reboot(self):
        display.debug("Rebooting server")

        remote_command = self.construct_command()
        reboot_result = self._low_level_execute_command(remote_command, sudoable=self.DEFAULT_SUDOABLE)

        result = {}
        if reboot_result['rc'] != 0:
            result['failed'] = True
            result['rebooted'] = False
            result['msg'] = "Shutdown command failed, error was: %s %s" % (
                to_native(reboot_result['stdout'].strip()), to_native(reboot_result['stderr'].strip()))
            return result

        result['failed'] = False
        result['start'] = datetime.utcnow()

        # Get the original connection_timeout option var so it can be reset after
        result['connection_timeout_orig'] = None
        try:
            result['connection_timeout_orig'] = self._connection.get_option('connection_timeout')
        except AnsibleError:
            display.debug("%s: connect_timeout connection option has not been set" % self._task.action)

        return result

    def validate_reboot(self, before_uptime, connection_timeout_orig):
        display.debug('Validating reboot')
        result = {}

        try:
            # keep on checking system uptime with short connection
            reboot_timeout = int(self._task.args.get('reboot_timeout', self.DEFAULT_REBOOT_TIMEOUT))
            connect_timeout = self._task.args.get('connect_timeout', self.DEFAULT_CONNECT_TIMEOUT)
            self.do_until_success_or_timeout(self.check_uptime, reboot_timeout, before_uptime, action_desc="uptime check")

            if connect_timeout:
                # reset the connection to clear the custom connection timeout
                try:
                    self._connection.set_options(direct={"connection_timeout": connection_timeout_orig})
                    self._connection._reset()
                except (AnsibleError, AttributeError) as e:
                    display.debug("Failed to reset connection_timeout back to default: %s" % to_native(e))

            # finally run test command to ensure everything is working
            # FUTURE: add a stability check (system must remain up for N seconds) to deal with self-multi-reboot updates
            self.do_until_success_or_timeout(self.run_test_command, reboot_timeout, before_uptime, action_desc="post-reboot test command")

            result['rebooted'] = True
            result['changed'] = True

        except TimedOutException as toex:
            result['failed'] = True
            result['rebooted'] = True
            result['msg'] = to_native(toex)
            return result

        post_reboot_delay = int(self._task.args.get('post_reboot_delay', self.DEFAULT_POST_REBOOT_DELAY))

        if post_reboot_delay != 0:
            display.vvv("%s: waiting an additional %d seconds" % (self._task.action, post_reboot_delay))
            time.sleep(post_reboot_delay)

        return result

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = True
        self._supports_async = True

        if self._play_context.check_mode:
            return dict(changed=True, elapsed=0, rebooted=True)

        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        if result.get('skipped', False) or result.get('failed', False):
            return result

        # Get current uptime
        try:
            before_uptime = self.get_system_uptime()
        except Exception as e:
            result['failed'] = True
            result['reboot'] = False
            result['msg'] = to_native(e)
            return result

        # Initiate reboot
        reboot_result = self.perform_reboot()

        if reboot_result['failed']:
            result = reboot_result
            elapsed = datetime.utcnow() - reboot_result['start']
            result['elapsed'] = elapsed.seconds
            return result

        # Make sure reboot was successful
        result = self.validate_reboot(before_uptime, reboot_result['connection_timeout_orig'])

        elapsed = datetime.utcnow() - reboot_result['start']
        result['elapsed'] = elapsed.seconds

        return result
