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

import socket
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
    DEFAULT_TEST_COMMAND = 'whoami'
    DEFAULT_REBOOT_MESSAGE = 'Reboot initiated by Ansible.'

    def do_until_success_or_timeout(self, what, timeout_sec, what_desc, fail_sleep_sec=1):
        max_end_time = datetime.utcnow() + timedelta(seconds=timeout_sec)

        while datetime.utcnow() < max_end_time:
            try:
                what()
                if what_desc:
                    display.debug("win_reboot: %s success" % what_desc)
                return
            except:
                if what_desc:
                    display.debug("win_reboot: %s fail (expected), sleeping before retry..." % what_desc)
                time.sleep(fail_sleep_sec)

        raise TimedOutException("timed out waiting for %s" % what_desc)

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        shutdown_timeout_sec = int(self._task.args.get('shutdown_timeout_sec', self.DEFAULT_SHUTDOWN_TIMEOUT_SEC))
        reboot_timeout_sec = int(self._task.args.get('reboot_timeout_sec', self.DEFAULT_REBOOT_TIMEOUT_SEC))
        connect_timeout_sec = int(self._task.args.get('connect_timeout_sec', self.DEFAULT_CONNECT_TIMEOUT_SEC))
        pre_reboot_delay_sec = int(self._task.args.get('pre_reboot_delay_sec', self.DEFAULT_PRE_REBOOT_DELAY_SEC))
        test_command = str(self._task.args.get('test_command', self.DEFAULT_TEST_COMMAND))
        msg = str(self._task.args.get('msg', self.DEFAULT_REBOOT_MESSAGE))

        if self._play_context.check_mode:
            display.vvv("win_reboot: skipping for check_mode")
            return dict(skipped=True)

        winrm_host = self._connection._winrm_host
        winrm_port = self._connection._winrm_port

        result = super(ActionModule, self).run(tmp, task_vars)
        result['warnings'] = []

        # Initiate reboot
        (rc, stdout, stderr) = self._connection.exec_command('shutdown /r /t %d /c "%s"' % (pre_reboot_delay_sec, msg))

        # Test for "A system shutdown has already been scheduled. (1190)" and handle it gracefully
        if rc == 1190:
            result['warnings'].append('A scheduled reboot was pre-empted by Ansible.')

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

        def raise_if_port_open():
            try:
                sock = socket.create_connection((winrm_host, winrm_port), connect_timeout_sec)
                sock.close()
            except:
                return False

            raise Exception("port is open")

        try:
            self.do_until_success_or_timeout(raise_if_port_open, shutdown_timeout_sec, what_desc="winrm port down")

            def connect_winrm_port():
                sock = socket.create_connection((winrm_host, winrm_port), connect_timeout_sec)
                sock.close()

            self.do_until_success_or_timeout(connect_winrm_port, reboot_timeout_sec, what_desc="winrm port up")

            def run_test_command():
                display.vvv("attempting post-reboot test command '%s'" % test_command)
                # call connection reset between runs if it's there
                try:
                    self._connection._reset()
                except AttributeError:
                    pass

                (rc, stdout, stderr) = self._connection.exec_command(test_command)

                if rc != 0:
                    raise Exception('test command failed')

            # FUTURE: ensure that a reboot has actually occurred by watching for change in last boot time fact
            # FUTURE: add a stability check (system must remain up for N seconds) to deal with self-multi-reboot updates

            self.do_until_success_or_timeout(run_test_command, reboot_timeout_sec, what_desc="post-reboot test command success")

            result['rebooted'] = True
            result['changed'] = True

        except TimedOutException as toex:
            result['failed'] = True
            result['rebooted'] = True
            result['msg'] = toex.message

        return result
