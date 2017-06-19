# (c) 2016 Matt Clay <matt@mystile.com>
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
import time
import re

from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins.callback import CallbackBase

try:
    from junit_xml import TestSuite, TestCase
    HAS_JUNIT_XML = True
except ImportError:
    HAS_JUNIT_XML = False

try:
    from collections import OrderedDict
    HAS_ORDERED_DICT = True
except ImportError:
    try:
        from ordereddict import OrderedDict
        HAS_ORDERED_DICT = True
    except ImportError:
        HAS_ORDERED_DICT = False


class CallbackModule(CallbackBase):
    """
    This callback writes playbook output to a JUnit formatted XML file.

    Tasks show up in the report as follows:
        'ok': pass
        'failed' with 'EXPECTED FAILURE' in the task name: pass
        'failed' due to an exception: error
        'failed' for other reasons: failure
        'skipped': skipped

    This plugin makes use of the following environment variables:
        JUNIT_OUTPUT_DIR (optional): Directory to write XML files to.
                                     Default: ~/.ansible.log
        JUNIT_TASK_CLASS (optional): Configure the output to be one class per yaml file
                                     Default: False

    Requires:
        junit_xml

    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'junit'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()

        self._output_dir = os.getenv('JUNIT_OUTPUT_DIR', os.path.expanduser('~/.ansible.log'))
        self._task_class = os.getenv('JUNIT_TASK_CLASS', 'False').lower()
        self._playbook_path = None
        self._playbook_name = None
        self._play_name = None
        self._task_data = None

        self.disabled = False

        if not HAS_JUNIT_XML:
            self.disabled = True
            self._display.warning('The `junit_xml` python module is not installed. '
                                  'Disabling the `junit` callback plugin.')

        if HAS_ORDERED_DICT:
            self._task_data = OrderedDict()
        else:
            self.disabled = True
            self._display.warning('The `ordereddict` python module is not installed. '
                                  'Disabling the `junit` callback plugin.')

        if not os.path.exists(self._output_dir):
            os.mkdir(self._output_dir)

    def _start_task(self, task):
        """ record the start of a task for one or more hosts """

        uuid = task._uuid

        if uuid in self._task_data:
            return

        play = self._play_name
        name = task.get_name().strip()
        path = task.get_path()

        if not task.no_log:
            args = ', '.join(('%s=%s' % a for a in task.args.items()))
            if args:
                name += ' ' + args

        self._task_data[uuid] = TaskData(uuid, name, path, play)

    def _finish_task(self, status, result):
        """ record the results of a task for a single host """

        task_uuid = result._task._uuid

        if hasattr(result, '_host'):
            host_uuid = result._host._uuid
            host_name = result._host.name
        else:
            host_uuid = 'include'
            host_name = 'include'

        task_data = self._task_data[task_uuid]

        if status == 'failed' and 'EXPECTED FAILURE' in task_data.name:
            status = 'ok'

        task_data.add_host(HostData(host_uuid, host_name, status, result))

    def _build_test_case(self, task_data, host_data):
        """ build a TestCase from the given TaskData and HostData """

        name = '[%s] %s: %s' % (host_data.name, task_data.play, task_data.name)
        duration = host_data.finish - task_data.start

        if self._task_class == 'true':
            junit_classname = re.sub('\.yml:[0-9]+$', '', task_data.path)
        else:
            junit_classname = task_data.path

        if host_data.status == 'included':
            return TestCase(name, junit_classname, duration, host_data.result)

        res = host_data.result._result
        rc = res.get('rc', 0)
        dump = self._dump_results(res, indent=0)
        dump = self._cleanse_string(dump)

        if host_data.status == 'ok':
            return TestCase(name, junit_classname, duration, dump)

        test_case = TestCase(name, junit_classname, duration)

        if host_data.status == 'failed':
            if 'exception' in res:
                message = res['exception'].strip().split('\n')[-1]
                output = res['exception']
                test_case.add_error_info(message, output)
            elif 'msg' in res:
                message = res['msg']
                test_case.add_failure_info(message, dump)
            else:
                test_case.add_failure_info('rc=%s' % rc, dump)
        elif host_data.status == 'skipped':
            if 'skip_reason' in res:
                message = res['skip_reason']
            else:
                message = 'skipped'
            test_case.add_skipped_info(message)

        return test_case

    def _cleanse_string(self, value):
        """ convert surrogate escapes to the unicode replacement character to avoid XML encoding errors """
        return to_text(to_bytes(value, errors='surrogateescape'), errors='replace')

    def _generate_report(self):
        """ generate a TestSuite report from the collected TaskData and HostData """

        test_cases = []

        for task_uuid, task_data in self._task_data.items():
            for host_uuid, host_data in task_data.host_data.items():
                test_cases.append(self._build_test_case(task_data, host_data))

        test_suite = TestSuite(self._playbook_name, test_cases)
        report = TestSuite.to_xml_string([test_suite])

        output_file = os.path.join(self._output_dir, '%s-%s.xml' % (self._playbook_name, time.time()))

        with open(output_file, 'wb') as xml:
            xml.write(to_bytes(report, errors='surrogate_or_strict'))

    def v2_playbook_on_start(self, playbook):
        self._playbook_path = playbook._file_name
        self._playbook_name = os.path.splitext(os.path.basename(self._playbook_path))[0]

    def v2_playbook_on_play_start(self, play):
        self._play_name = play.get_name()

    def v2_runner_on_no_hosts(self, task):
        self._start_task(task)

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._start_task(task)

    def v2_playbook_on_cleanup_task_start(self, task):
        self._start_task(task)

    def v2_playbook_on_handler_task_start(self, task):
        self._start_task(task)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        if ignore_errors:
            self._finish_task('ok', result)
        else:
            self._finish_task('failed', result)

    def v2_runner_on_ok(self, result):
        self._finish_task('ok', result)

    def v2_runner_on_skipped(self, result):
        self._finish_task('skipped', result)

    def v2_playbook_on_include(self, included_file):
        self._finish_task('included', included_file)

    def v2_playbook_on_stats(self, stats):
        self._generate_report()


class TaskData:
    """
    Data about an individual task.
    """

    def __init__(self, uuid, name, path, play):
        self.uuid = uuid
        self.name = name
        self.path = path
        self.play = play
        self.start = None
        self.host_data = OrderedDict()
        self.start = time.time()

    def add_host(self, host):
        if host.uuid in self.host_data:
            if host.status == 'included':
                # concatenate task include output from multiple items
                host.result = '%s\n%s' % (self.host_data[host.uuid].result, host.result)
            else:
                raise Exception('%s: %s: %s: duplicate host callback: %s' % (self.path, self.play, self.name, host.name))

        self.host_data[host.uuid] = host


class HostData:
    """
    Data about an individual host.
    """

    def __init__(self, uuid, name, status, result):
        self.uuid = uuid
        self.name = name
        self.status = status
        self.result = result
        self.finish = time.time()
