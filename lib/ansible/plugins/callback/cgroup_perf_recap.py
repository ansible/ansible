# -*- coding: utf-8 -*-
# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
    callback: cgroup_perf_recap
    callback_type: aggregate
    requirements:
      - whitelist in configuration
      - cgroups
    short_description: Profiles system activity of tasks and full execution using cgroups
    version_added: "2.6"
    description:
        - This is an ansible callback plugin utilizes cgroups to profile system activity of ansible and
          individual tasks, and display a recap at the end of the playbook execution
    notes:
        - Requires ansible to be run from within a cgroup, such as with
          C(cgexec -g cpuacct,memory:ansible_profile ansible-playbook ...)
        - This cgroup should only be used by ansible to get accurate results
        - To create the cgroup, first use a command such as
          C(sudo cgcreate -a ec2-user:ec2-user -t ec2-user:ec2-user -g cpuacct,memory:ansible_profile)
    options:
      control_group:
        required: True
        description: Name of cgroups control group
        env:
          - name: CGROUP_CONTROL_GROUP
        ini:
          - section: callback_cgroup_perf_recap
            key: control_group
      csv_output_dir:
        description: Output path for CSV file containing recorded memory readings. If the value contains a single %s,
                     the start time of the playbook run will be inserted in that space
        type: path
        env:
          - name: CGROUP_CSV_OUTPUT_DIR
        ini:
          - section: callback_cgroup_perf_recap
            key: csv_output_dir
      cpu_poll_interval:
        description: Interval between CPU polling for determining CPU usage. A lower value may produce inaccurate
                     results, a higher value may not be short enough to collect results for short tasks.
        default: 0.25
        type: float
        env:
          - name: CGROUP_CPU_POLL_INTERVAL
        ini:
          - section: callback_cgroup_perf_recap
            key: cpu_poll_interval
'''

import csv
import datetime
import os
import time
import threading

from abc import ABCMeta, abstractmethod

from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.six import with_metaclass
from ansible.plugins.callback import CallbackBase


class BaseProf(with_metaclass(ABCMeta, threading.Thread)):
    def __init__(self, path, obj=None, csvwriter=None):
        threading.Thread.__init__(self)
        self.obj = obj
        self.path = path
        self.max = 0
        self.running = True
        self.csvwriter = csvwriter

    def run(self):
        while self.running:
            self.poll()

    @abstractmethod
    def poll(self):
        pass


class MemoryProf(BaseProf):
    """Python thread for recording memory usage"""
    def poll(self):
        with open(self.path) as f:
            val = int(f.read().strip()) / 1024**2
        if val > self.max:
            self.max = val
        if self.csvwriter:
            try:
                self.csvwriter.writerow([time.time(), self.obj.get_name(), val])
            except ValueError:
                # We may be profiling after the playbook has ended
                self.running = False
        time.sleep(0.001)


class CpuProf(BaseProf):
    def __init__(self, path, poll_interval=0.25, obj=None, csvwriter=None):
        super(CpuProf, self).__init__(path, obj=obj, csvwriter=csvwriter)
        self._poll_interval = poll_interval

    def poll(self):
        with open(self.path) as f:
            start_time = time.time() * 1000**2
            start_usage = int(f.read().strip()) / 1000
        time.sleep(self._poll_interval)
        with open(self.path) as f:
            end_time = time.time() * 1000**2
            end_usage = int(f.read().strip()) / 1000
        val = (end_usage - start_usage) / (end_time - start_time) * 100
        if val > self.max:
            self.max = val
        if self.csvwriter:
            try:
                self.csvwriter.writerow([time.time(), self.obj.get_name(), val])
            except ValueError:
                # We may be profiling after the playbook has ended
                self.running = False


class PidsProf(BaseProf):
    def poll(self):
        with open(self.path) as f:
            val = int(f.read().strip())
        if val > self.max:
            self.max = val
        if self.csvwriter:
            try:
                self.csvwriter.writerow([time.time(), self.obj.get_name(), val])
            except ValueError:
                # We may be profiling after the playbook has ended
                self.running = False
        time.sleep(0.001)


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'cgroup_memory_recap'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display)


        self._features = ('memory', 'cpu', 'pids')

        self._units = {
            'memory': 'MB',
            'cpu': '%',
            'pids': '',
        }

        self.task_results = {
            'memory': [],
            'cpu': [],
            'pids': [],
        }

        self._profilers = dict.fromkeys(self._features)
        self._csv_files = dict.fromkeys(self._features)
        self._csv_writers = dict.fromkeys(self._features)

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self._cpu_poll_interval = self.get_option('cpu_poll_interval')

        self.control_group = to_bytes(self.get_option('control_group'), errors='surrogate_or_strict')
        self.mem_max_file = b'/sys/fs/cgroup/memory/%s/memory.max_usage_in_bytes' % self.control_group
        self.mem_current_file = b'/sys/fs/cgroup/memory/%s/memory.usage_in_bytes' % self.control_group
        self.cpu_usage_file = b'/sys/fs/cgroup/cpuacct/%s/cpuacct.usage' % self.control_group
        self.pid_current_file = b'/sys/fs/cgroup/pids/%s/pids.current' % self.control_group

        for path in (self.mem_max_file, self.mem_current_file, self.cpu_usage_file, self.pid_current_file):
            try:
                with open(path) as f:
                    pass
            except Exception as e:
                self._display.warning(
                    u'Cannot open %s for reading (%s). Disabling %s' % (to_text(path), to_text(e), self.CALLBACK_NAME)
                )
                self.disabled = True
                return

        try:
            with open(self.mem_max_file, 'w+') as f:
                f.write('0')
        except Exception as e:
            self._display.warning(
                u'Unable to reset max memory value in %s: %s' % (to_text(self.mem_max_file), to_text(e))
            )
            self.disabled = True
            return

        try:
            with open(self.cpu_usage_file, 'w+') as f:
                f.write('0')
        except Exception as e:
            self._display.warning(
                u'Unable to reset CPU usage value in %s: %s' % (to_text(self.cpu_usage_file), to_text(e))
            )
            self.disabled = True
            return

        csv_output_dir = self.get_option('csv_output_dir')
        try:
            csv_output_dir %= datetime.datetime.now().isoformat()
        except TypeError:
            pass

        if csv_output_dir:
            if not os.path.exists(csv_output_dir):
                os.mkdir(csv_output_dir)
            for feature in self._features:
                self._csv_files[feature] = open(os.path.join(csv_output_dir, '%s.csv' % feature), 'w+')
                self._csv_writers[feature] = csv.writer(self._csv_files[feature])

    def _profile(self, obj=None):
        prev_task = None
        results = dict.fromkeys(self._features)
        try:
            for name, prof in self._profilers.items():
                prof.running = False

            for name, prof in self._profilers.items():
                results[name] = prof.max
            prev_task = prof.obj
        except AttributeError:
            pass

        for name, result in results.items():
            if result is not None:
                try:
                    self.task_results[name].append((prev_task, result))
                except ValueError:
                    pass

        if obj is not None:
            self._profilers['memory'] = MemoryProf(self.mem_current_file, obj=obj, csvwriter=self._csv_writers['memory'])
            self._profilers['cpu'] = CpuProf(self.cpu_usage_file, poll_interval=self._cpu_poll_interval, obj=obj,
                                             csvwriter=self._csv_writers['cpu'])
            self._profilers['pids'] = PidsProf(self.pid_current_file,  obj=obj, csvwriter=self._csv_writers['pids'])
            for name, prof in self._profilers.items():
                prof.start()

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._profile(task)

    def v2_playbook_on_stats(self, stats):
        self._profile()

        with open(self.mem_max_file) as f:
            max_results = int(f.read().strip()) / 1024 / 1024

        self._display.banner('CGROUP PERF RECAP')
        self._display.display('Memory Execution Maximum: %0.2fMB\n' % max_results)
        for name, data in self.task_results.items():
            if name == 'memory':
                continue
            try:
                self._display.display('%s Execution Maximum: %0.2f%s\n' % (name, max((t[1] for t in data)), self._units[name]))
            except Exception as e:
                self._display.display('%s profiling error: no results collected: %s\n' % (name, e))

        self._display.display('\n')

        for name, data in self.task_results.items():
            if data:
                self._display.display('%s:\n' % name)
            for task, value in data:
                self._display.display('%s (%s): %0.2f%s' % (task.get_name(), task._uuid, value, self._units[name]))

        for dummy, f in self._csv_files.items():
            try:
                f.close()
            except Exception:
                pass
