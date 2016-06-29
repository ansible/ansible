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

from ansible.plugins.callback import CallbackBase
from ansible import constants as C
from ansible.utils.color import colorize, hostcolor
import time

HAS_PPRINT = True
try:
    import pprint
except ImportError:
    HAS_PPRINT = False


class CallbackModule(CallbackBase):
    """
    This callback plugin is intended to be used with integration test playbooks.
    The plugin reports only on tasks of action type 'assert' and provides a report
    similar to that of running make tests with nosetests.

    The assert_summary callback plugin is best used together with the 'test' strategy
    plugin, as it makes sure to run all of the tasks in the play and provide a summary
    report at the end, instead of the default ansible strategy which halts execution on
    failed tasks.

    Sample output:

    Assert Summary *****************************************************************
    testhost                   : Total=3    passed=2    failed=1

    Tests failed:
        assert setup task
        Task:	{"changed": false, ... }
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'assert_summary'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        self.assert_ok = dict()
        self.assert_failed = dict()
        self.failed_msgs = dict()

        self.start_time = time.time()
        self.end_time = None

        super(CallbackModule, self).__init__()

    def _process_result(self, where_to, status, result):
        """
        Gather task name, host name and task args from result._task
        Save into dictionaries for final report and display current status
        to provide progress reporting during play execution
        """

        hostname = result._host.get_name().strip()
        taskname = result._task.get_name().strip()

        self._display.display("%s :\t%s ... %s" % (hostname, taskname, status))

        the_dict = getattr(self, where_to)
        task_data = dict(name=taskname, args=result._task.args, result=result._result)
        if hostname in the_dict:
            task_list = the_dict[hostname]
            task_list.append(task_data)
            the_dict[hostname] = task_list
        else:
            task_list = [task_data]
            the_dict[hostname] = task_list

    def v2_runner_on_ok(self, result):
        """
        Save the result of successfully completed assert tasks
        """

        if result._task.action == "assert":
            self._process_result("assert_ok", "ok", result)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """
        Save the result of failed assert tasks
        """

        if result._task.action == "assert":
            self._process_result("assert_failed", "failed", result)

    def v2_playbook_on_start(self, playbook):
        """
        Display header explaining that the plugin has loaded
        """

        from os.path import basename
        self._display.banner("PLAYBOOK: %s" % basename(playbook._file_name))

        if self._display.verbosity:
            self._display.display("")
            self._display.display("Assert Summary Callback Plugin in use.")
            self._display.display("")
            self._display.display("\tNote: The plugin assumes the following:")
            self._display.display("\t----------------------------------------")
            self._display.display("\tEvery task is followed by an 'assert' task")
            self._display.display("\tEvery task has ignore_error: yes")
            self._display.display("\tEvery non assert task uses register: result")
            self._display.display("\tEvery assert task has last: \"{{ result }}\" as an argument")

        self._display.display("")
        self._display.display("Running Tests:", C.COLOR_HIGHLIGHT)
        self._display.display("")

    def v2_playbook_on_stats(self, stats):
        """
        Display final report for assert tasks completion status,
        including the results of the tasks asserting against.

        By default will only display detailed report on failed assert tasks.
        If verbosity is greater than 1, will report on successfull assert tasks
        as well.
        """

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

    def _detailed_report(self, header, host, where_from):
        """
        print a detailed report per host grouped by status (failed / ok)
        """

        the_dict = getattr(self, where_from)
        if host in the_dict:
            self._display.display(header, C.COLOR_DEPRECATE)
            self._display.display("-" * (len(header)+1), C.COLOR_DEPRECATE)
            for task_data in the_dict[host]:
                args_data = task_data.get('args')
                result_data = self._dump_results(task_data.get('result'))

                self._display.display("\t%s" % task_data["name"], C.COLOR_DEPRECATE)
                self._display.display("\ttask result:", C.COLOR_HIGHLIGHT)
                self._display.display("\t%s" % _pretty_json(args_data['last']))
                self._display.display("\tassert:", C.COLOR_HIGHLIGHT)
                self._display.display("\t%s" % _pretty_json(args_data['that']))
                self._display.display("\tassert result:", C.COLOR_HIGHLIGHT)
                self._display.display("\t%s" % result_data)

                self._display.display("")


def _pretty_json(json):
    if HAS_PPRINT:
        pp = pprint.PrettyPrinter(indent=8, depth=4)
        json = pp.pformat(json)
    return json
