# (c) 2016, Matt Davis <mdavis@ansible.com>
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

# CI-required python3 boilerplate
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import time
from datetime import datetime, timedelta

from ansible.plugins.action import ActionBase

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class TimedOutException(Exception):
    pass


class ActionModule(ActionBase):
    TRANSFERS_FILES = False

    DEFAULT_SHUTDOWN_TIMEOUT_SEC = 600
    DEFAULT_REBOOT_TIMEOUT_SEC = 600
    DEFAULT_CONNECT_TIMEOUT_SEC = 5
    DEFAULT_PRE_REBOOT_DELAY_SEC = 2
    DEFAULT_POST_REBOOT_DELAY_SEC = 0
    DEFAULT_TEST_COMMAND = 'whoami'
    DEFAULT_REBOOT_MESSAGE = 'Reboot initiated by Ansible.'

    def do_until_success_or_timeout(self, what, timeout_sec, connect_timeout, what_desc, fail_sleep_sec=1):
        max_end_time = datetime.utcnow() + timedelta(seconds=timeout_sec)

        e = None
        while datetime.utcnow() < max_end_time:
            try:
                what(connect_timeout)
                if what_desc:
                    display.debug("win_reboot: %s success" % what_desc)
                return
            except Exception as e:
                if what_desc:
                    display.debug("win_reboot: %s fail (expected), retrying in %d seconds..." % (what_desc, fail_sleep_sec))
                time.sleep(fail_sleep_sec)

        raise TimedOutException("timed out waiting for %s: %s" % (what_desc, e))

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        shutdown_timeout_sec = int(self._task.args.get('shutdown_timeout_sec', self.DEFAULT_SHUTDOWN_TIMEOUT_SEC))
        reboot_timeout_sec = int(self._task.args.get('reboot_timeout_sec', self.DEFAULT_REBOOT_TIMEOUT_SEC))
        connect_timeout_sec = int(self._task.args.get('connect_timeout_sec', self.DEFAULT_CONNECT_TIMEOUT_SEC))
        pre_reboot_delay_sec = int(self._task.args.get('pre_reboot_delay_sec', self.DEFAULT_PRE_REBOOT_DELAY_SEC))
        post_reboot_delay_sec = int(self._task.args.get('post_reboot_delay_sec', self.DEFAULT_POST_REBOOT_DELAY_SEC))
        test_command = str(self._task.args.get('test_command', self.DEFAULT_TEST_COMMAND))
        msg = str(self._task.args.get('msg', self.DEFAULT_REBOOT_MESSAGE))

        if self._play_context.check_mode:
            display.vvv("win_reboot: skipping for check_mode")
            return dict(skipped=True)

        result = super(ActionModule, self).run(tmp, task_vars)

        # Initiate reboot
        (rc, stdout, stderr) = self._connection.exec_command('shutdown /r /t %d /c "%s"' % (pre_reboot_delay_sec, msg))

        # Test for "A system shutdown has already been scheduled. (1190)" and handle it gracefully
        if rc == 1190:
            display.warning('A scheduled reboot was pre-empted by Ansible.')

            # Try to abort (this may fail if it was already aborted)
            (rc, stdout1, stderr1) = self._connection.exec_command('shutdown /a')

            # Initiate reboot again
            (rc, stdout2, stderr2) = self._connection.exec_command('shutdown /r /t %d' % pre_reboot_delay_sec)
            stdout += stdout1 + stdout2
            stderr += stderr1 + stderr2

        if rc != 0:
            result['failed'] = True
            result['rebooted'] = False
            result['msg'] = "Shutdown command failed, error text was %s" % stderr
            return result

        def ping_module_test(connect_timeout):
            ''' Test ping module, if available '''
            display.vvv("win_reboot: attempting ping module test")
            # call connection reset between runs if it's there
            try:
                self._connection._reset()
            except AttributeError:
                pass

            # Use win_ping on powershell
            ping_result = self._execute_module(module_name='win_ping', module_args=dict(), tmp=tmp, task_vars=task_vars)

            # Test module output
            if ping_result['ping'] != 'pong':
                raise Exception('ping test failed')

        def run_test_command(connect_timeout):
            display.vvv("win_reboot: attempting post-reboot test command '%s'" % test_command)
            # call connection reset between runs if it's there
            try:
                self._connection._reset()
            except AttributeError:
                pass

            (rc, stdout, stderr) = self._connection.exec_command(test_command)

            if rc != 0:
                raise Exception('test command failed')

        start = datetime.now()

        try:
            # If the connection has a transport_test method, use it first
            if hasattr(self._connection, 'transport_test'):
                self.do_until_success_or_timeout(self._connection.transport_test, reboot_timeout_sec, connect_timeout_sec,
                    what_desc="connection port up")

            # FUTURE: ensure that a reboot has actually occurred by watching for change in last boot time fact
            # FUTURE: add a stability check (system must remain up for N seconds) to deal with self-multi-reboot updates

            # Use the ping module test to determine end-to-end connectivity
            if test_command:
                self.do_until_success_or_timeout(run_test_command, reboot_timeout_sec, connect_timeout_sec, what_desc="post-reboot test command success")
            else:
                self.do_until_success_or_timeout(ping_module_test, reboot_timeout_sec, connect_timeout_sec, what_desc="ping module test success")

            result['rebooted'] = True
            result['changed'] = True

        except TimedOutException as toex:
            result['failed'] = True
            result['rebooted'] = True
            result['msg'] = toex.message

        if post_reboot_delay_sec != 0:
            display.vvv("win_reboot: waiting an additional %d seconds" % post_reboot_delay_sec)
            time.sleep(post_reboot_delay_sec)

        elapsed = datetime.now() - start
        result['elapsed'] = elapsed.seconds

        return result
