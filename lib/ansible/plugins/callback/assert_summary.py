# (c) 2016, Radware LTD.

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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from ansible.plugins.callback.default import CallbackModule as CallbackModule_default
from ansible import constants as C
from ansible.utils.color import colorize, hostcolor
import time


class CallbackModule(CallbackModule_default):
    """
    This callback plugin is intended to be used with integration test playbooks.
    The intent is for the output to look like nosetests output.

    The plugin reports on the outcome of assert tasks.
    During task execution there'll be a brief report (task name, ok/failed) for assert tasks only.
    At the end a summary will be printed:
        Total number of tests, number of passes/fails.
    Detailed report of failed asserts (test task outcome, assert conditions, assert outcome)
    If verbosity is higher than zero - progress will be reported for every task, and a
    detailed report of successful asserts will be printed as well.

    IMPORTANT:
    The plugin assumes that assert tasks appear directly after test tasks with no other task between them.

    Sample output:

    Assert Summary ***************************************************************

      localhost                  : run=4    passed=2    failed=2

    Failed task report
    -------------------
        task: failed task 2
        task result:
        {"changed": false, "cmd": "/bin/tru", "failed": true, "msg": "[Errno 2] No such file or directory", "rc": 2}
        assert:
        {u'that': [u'not result.failed']}
        assert result:
        {"assertion": "not result.failed", "changed": false, "evaluated_to": false, "failed": true}

    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'assert_summary'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        self.assert_ok = dict()
        self.assert_failed = dict()
        self.stack = []
        self.failures = False

        self.start_time = time.time()
        self.end_time = None

        self.super_ref = super(CallbackModule, self)
        self.super_ref.__init__()

    def v2_playbook_on_task_start(self, task, is_conditional):
        """
        bypass printing task banner for tasks other than assert.
        If verbosity>0 don't bypass
        """
        # task name is printed by the result handler
        if task.action == "assert" or self._display.verbosity:
            self.super_ref.v2_playbook_on_task_start(task, is_conditional)

    def v2_runner_on_skipped(self, result):
        """
        bypass printing on skipped tasks unless verbosity>0
        """
        if self._display.verbosity:
            self.super_ref.v2_runner_on_skipped(result)

    def v2_runner_on_ok(self, result):
        """
        Save the result of successfully completed tasks.
        Asserts are saved with the previous task result as well.
        """

        if result._task.action == "assert":
            orig_result = self.stack.pop()
            self._process_result("assert_ok", "ok", result, orig_result)
            self.super_ref.v2_runner_on_ok(result)
        else:
            self.stack.append(result)
            if self._display.verbosity:
                self._display.display("done")

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """
        Save the results of failed tasks (with ignore errors).
        For tasks without ignore errors - dump the results.

        Asserts are saved with the previous task result as well.
        """

        if not ignore_errors:
            self.failures = True
            self.super_ref.v2_runner_on_failed(result, ignore_errors)
        else:
            if result._task.action == "assert":
                orig_result = self.stack.pop()
                self._process_result("assert_failed", "failed", result, orig_result)
                self.super_ref.v2_runner_on_failed(result, ignore_errors)
            else:
                self.stack.append(result)
                if self._display.verbosity:
                    self._display.display("done")

    def v2_playbook_on_stats(self, stats):
        """
        Display final report for assert tasks completion status,
        including the results of the tasks asserting against.

        By default will only display detailed report on failed assert tasks.
        If verbosity is greater than 1, will report on successful assert tasks
        as well.
        """

        # if any of the regular tasks failed don't display the assert report
        if self.failures:
            self._display.banner("Failure detected, processing halted")
            return

        self.end_time = time.time()

        self._display.banner("Assert Summary")
        self._display.display("")

        hosts = sorted(stats.processed.keys())
        total_tests = 0

        for h in hosts:
            count_ok = len(self.assert_ok.get(h,[]))
            count_failed = len(self.assert_failed.get(h,[]))
            count_total = count_ok + count_failed
            total_tests += count_total

            # getting hostcolor - green if all tests passed. red otherwise
            fake_stats = dict(
                ok=count_ok,
                failures=count_failed,
                unreachable=0,
                changed=0,
                skipped=0
            )

            self._display.display(u"  %s : %s %s %s" % (
                  hostcolor(h, fake_stats),
                  colorize(u'run', count_total, C.COLOR_OK),
                  colorize(u'passed', count_ok, C.COLOR_OK),
                  colorize(u'failed', count_failed, C.COLOR_ERROR)
                  ),
                  screen_only=True
            )

            self._display.display("")

            # detailed report on failed tasks
            if self._display.verbosity > 0:
                # detailed report on successful tasks
                self._detailed_report("Successful task report", h, "assert_ok")
            # detailed report on failed tasks
            self._detailed_report("Failed task report", h, "assert_failed")

        self._display.display("-----------------------------------------------------------------------")
        self._display.display("Ran %s tests on %s host%s in %0.1fs" % (
                total_tests,
                len(hosts),
                "s" if len(hosts) > 1 else "",
                (self.end_time-self.start_time)
            ))
        self._display.display("")

    def _process_result(self, where_to, status, result, original_result):
        """
        Gather task name, host name and task args from result._task
        Save into dictionaries for final report
        """

        hostname = result._host.get_name().strip()
        taskname = original_result._task.get_name().strip()

        the_dict = getattr(self, where_to)
        task_data = dict(
            name=taskname,
            assert_expr=result._task.args,
            assert_result=result._result,
            test_result=original_result._result
        )

        if hostname in the_dict:
            task_list = the_dict[hostname]
            task_list.append(task_data)
            the_dict[hostname] = task_list
        else:
            task_list = [task_data]
            the_dict[hostname] = task_list

    def _detailed_report(self, header, host, where_from):
        """
        print a detailed report per host grouped by status (failed / ok)
        """

        the_dict = getattr(self, where_from)
        if host in the_dict:
            self._display.display(header, C.COLOR_DEPRECATE)
            self._display.display("-" * (len(header)+1), C.COLOR_DEPRECATE)
            for task_data in the_dict[host]:
                assert_expr = task_data.get('assert_expr')
                test_result = self._dump_results(task_data.get('test_result'))
                assert_result = self._dump_results(task_data.get('assert_result'))

                self._display.display("\ttask: %s" % task_data["name"], C.COLOR_DEPRECATE)
                self._display.display("\ttask result:", C.COLOR_HIGHLIGHT)
                self._display.display("\t%s" % test_result.replace('\n',''))
                self._display.display("\tassert:", C.COLOR_HIGHLIGHT)
                self._display.display("\t%s" % assert_expr)
                self._display.display("\tassert result:", C.COLOR_HIGHLIGHT)
                self._display.display("\t%s" % assert_result)

                self._display.display("")
