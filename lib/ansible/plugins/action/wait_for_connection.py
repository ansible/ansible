# (c) 2017, Dag Wieers <dag@wieers.com>
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
from __future__ import annotations

import math
import time
from datetime import datetime

from ansible.module_utils.common.text.converters import to_text
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()


class TimedOutException(Exception):
    pass


class ActionModule(ActionBase):
    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset(('connect_timeout', 'delay', 'sleep', 'timeout'))

    DEFAULT_CONNECT_TIMEOUT = 5
    DEFAULT_DELAY = 0
    DEFAULT_SLEEP = 1
    DEFAULT_TIMEOUT = 600

    def do_until_success_or_timeout(self, what, timeout, connect_timeout, what_desc, sleep=1):
        max_end_time = time.monotonic() + timeout
        error = None
        while True:
            time_left = max_end_time - time.monotonic()
            if time_left <= 0:
                break

            # Connection plugin timeouts are whole seconds, so give the attempt
            # the time left rounded up. It can then finish up to one second
            # past the deadline.
            attempt_timeout = min(connect_timeout, math.ceil(time_left))
            if attempt_timeout < 1:
                # SSH treats 0 as no timeout; a non-positive connect_timeout is
                # not a usable budget either.
                break

            try:
                what(attempt_timeout)
                if what_desc:
                    display.debug("wait_for_connection: %s success" % what_desc)
                return
            except Exception as e:
                error = e  # PY3 compatibility to store exception for use outside of this block
                time_left = max_end_time - time.monotonic()
                if time_left <= 0:
                    break
                sleep_time = min(sleep, time_left)
                if what_desc:
                    display.debug("wait_for_connection: %s fail (expected), retrying in %.1f seconds..." % (what_desc, sleep_time))
                time.sleep(sleep_time)

        if error is None:
            raise TimedOutException("timed out waiting for %s" % what_desc)
        raise TimedOutException("timed out waiting for %s: %s" % (what_desc, error))

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        connect_timeout = int(self._task.args.get('connect_timeout', self.DEFAULT_CONNECT_TIMEOUT))
        delay = int(self._task.args.get('delay', self.DEFAULT_DELAY))
        sleep = int(self._task.args.get('sleep', self.DEFAULT_SLEEP))
        timeout = int(self._task.args.get('timeout', self.DEFAULT_TIMEOUT))

        if self._task.check_mode:
            display.vvv("wait_for_connection: not executing in check_mode")
            return dict(skipped=True,  # deprecated: description='returning skipped from actions/modules' core_version='2.25'
                        changed=False,
                        msg='`wait_for_connection` did not execute due to check mode')

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        original_connection_timeout = None
        original_reconnection_retries = None
        if self._connection.has_option('timeout'):
            original_connection_timeout = self._connection.get_option('timeout')
        if self._connection.has_option('reconnection_retries'):
            original_reconnection_retries = self._connection.get_option('reconnection_retries')

        def ping_module_test(attempt_timeout):
            """ Test ping module, if available """
            display.vvv("wait_for_connection: attempting ping module test")
            # re-run interpreter discovery if we ran it in the first iteration
            if self._discovered_interpreter_key:
                task_vars['ansible_facts'].pop(self._discovered_interpreter_key, None)
            # call connection reset between runs if it's there
            try:
                self._connection.reset()
            except AttributeError:
                pass

            if original_connection_timeout is not None:
                self._connection.set_option('timeout', attempt_timeout)

            ping_result = self._execute_module(module_name='ansible.legacy.ping', module_args=dict(), task_vars=task_vars)

            # Test module output
            if ping_result['ping'] != 'pong':
                raise Exception('ping test failed')

        start = datetime.now()

        if delay:
            time.sleep(delay)

        try:
            # If the connection has a transport_test method, use it first
            if hasattr(self._connection, 'transport_test'):
                self.do_until_success_or_timeout(self._connection.transport_test, timeout, connect_timeout, what_desc="connection port up", sleep=sleep)

            # The outer loop owns retries, so do not let the connection plugin retry inside one attempt.
            if original_reconnection_retries is not None:
                self._connection.set_option('reconnection_retries', 0)

            # Use the ping module test to determine end-to-end connectivity
            self.do_until_success_or_timeout(ping_module_test, timeout, connect_timeout, what_desc="ping module test", sleep=sleep)

        except TimedOutException as e:
            result['failed'] = True
            result['msg'] = to_text(e)
        finally:
            if original_connection_timeout is not None:
                self._connection.set_option('timeout', original_connection_timeout)
            if original_reconnection_retries is not None:
                self._connection.set_option('reconnection_retries', original_reconnection_retries)

        elapsed = datetime.now() - start
        result['elapsed'] = elapsed.seconds

        # remove a temporary path we created
        self._remove_tmp_path(self._connection._shell.tmpdir)

        return result
