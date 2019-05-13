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
    version_added: "2.8"
    description:
        - This is an ansible callback plugin utilizes cgroups to profile system activity of ansible and
          individual tasks, and display a recap at the end of the playbook execution
    notes:
        - Requires ansible to be run from within a cgroup, such as with
          C(cgexec -g cpuacct,memory,pids:ansible_profile ansible-playbook ...)
        - This cgroup should only be used by ansible to get accurate results
        - To create the cgroup, first use a command such as
          C(sudo cgcreate -a ec2-user:ec2-user -t ec2-user:ec2-user -g cpuacct,memory,pids:ansible_profile)
    options:
      control_group:
        required: True
        description: Name of cgroups control group
        env:
          - name: CGROUP_CONTROL_GROUP
        ini:
          - section: callback_cgroup_perf_recap
            key: control_group
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
      memory_poll_interval:
        description: Interval between memory polling for determining memory usage. A lower value may produce inaccurate
                     results, a higher value may not be short enough to collect results for short tasks.
        default: 0.25
        type: float
        env:
          - name: CGROUP_MEMORY_POLL_INTERVAL
        ini:
          - section: callback_cgroup_perf_recap
            key: memory_poll_interval
      pid_poll_interval:
        description: Interval between PID polling for determining PID count. A lower value may produce inaccurate
                     results, a higher value may not be short enough to collect results for short tasks.
        default: 0.25
        type: float
        env:
          - name: CGROUP_PID_POLL_INTERVAL
        ini:
          - section: callback_cgroup_perf_recap
            key: pid_poll_interval
      display_recap:
        description: Controls whether the recap is printed at the end, useful if you will automatically
                     process the output files
        env:
          - name: CGROUP_DISPLAY_RECAP
        ini:
          - section: callback_cgroup_perf_recap
            key: display_recap
        type: bool
        default: true
      file_name_format:
        description: Format of filename. Accepts C(%(counter)s), C(%(task_uuid)s),
                     C(%(feature)s), C(%(ext)s). Defaults to C(%(feature)s.%(ext)s) when C(file_per_task) is C(False)
                     and C(%(counter)s-%(task_uuid)s-%(feature)s.%(ext)s) when C(True)
        env:
          - name: CGROUP_FILE_NAME_FORMAT
        ini:
          - section: callback_cgroup_perf_recap
            key: file_name_format
        type: str
        default: '%(feature)s.%(ext)s'
      output_dir:
        description: Output directory for files containing recorded performance readings. If the value contains a
                     single %s, the start time of the playbook run will be inserted in that space. Only the deepest
                     level directory will be created if it does not exist, parent directories will not be created.
        type: path
        default: /tmp/ansible-perf-%s
        env:
          - name: CGROUP_OUTPUT_DIR
        ini:
          - section: callback_cgroup_perf_recap
            key: output_dir
      output_format:
        description: Output format, either CSV or JSON-seq
        env:
          - name: CGROUP_OUTPUT_FORMAT
        ini:
          - section: callback_cgroup_perf_recap
            key: output_format
        type: str
        default: csv
        choices:
          - csv
          - json
      file_per_task:
        description: When set as C(True) along with C(write_files), this callback will write 1 file per task
                     instead of 1 file for the entire playbook run
        env:
          - name: CGROUP_FILE_PER_TASK
        ini:
          - section: callback_cgroup_perf_recap
            key: file_per_task
        type: bool
        default: False
      write_files:
        description: Dictates whether files will be written containing performance readings
        env:
          - name: CGROUP_WRITE_FILES
        ini:
          - section: callback_cgroup_perf_recap
            key: write_files
        type: bool
        default: false
'''

import csv
import datetime
import os
import time
import threading

from abc import ABCMeta, abstractmethod

from functools import partial

from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.six import with_metaclass
from ansible.parsing.ajson import AnsibleJSONEncoder, json
from ansible.plugins.callback import CallbackBase


RS = '\x1e'  # RECORD SEPARATOR
LF = '\x0a'  # LINE FEED


def dict_fromkeys(keys, default=None):
    d = {}
    for key in keys:
        d[key] = default() if callable(default) else default
    return d


class BaseProf(with_metaclass(ABCMeta, threading.Thread)):
    def __init__(self, path, obj=None, writer=None):
        threading.Thread.__init__(self)  # pylint: disable=non-parent-init-called
        self.obj = obj
        self.path = path
        self.max = 0
        self.running = True
        self.writer = writer

    def run(self):
        while self.running:
            self.poll()

    @abstractmethod
    def poll(self):
        pass


class MemoryProf(BaseProf):
    """Python thread for recording memory usage"""
    def __init__(self, path, poll_interval=0.25, obj=None, writer=None):
        super(MemoryProf, self).__init__(path, obj=obj, writer=writer)
        self._poll_interval = poll_interval

    def poll(self):
        with open(self.path) as f:
            val = int(f.read().strip()) / 1024**2
        if val > self.max:
            self.max = val
        if self.writer:
            try:
                self.writer(time.time(), self.obj.get_name(), self.obj._uuid, val)
            except ValueError:
                # We may be profiling after the playbook has ended
                self.running = False
        time.sleep(self._poll_interval)


class CpuProf(BaseProf):
    def __init__(self, path, poll_interval=0.25, obj=None, writer=None):
        super(CpuProf, self).__init__(path, obj=obj, writer=writer)
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
        if self.writer:
            try:
                self.writer(time.time(), self.obj.get_name(), self.obj._uuid, val)
            except ValueError:
                # We may be profiling after the playbook has ended
                self.running = False


class PidsProf(BaseProf):
    def __init__(self, path, poll_interval=0.25, obj=None, writer=None):
        super(PidsProf, self).__init__(path, obj=obj, writer=writer)
        self._poll_interval = poll_interval

    def poll(self):
        with open(self.path) as f:
            val = int(f.read().strip())
        if val > self.max:
            self.max = val
        if self.writer:
            try:
                self.writer(time.time(), self.obj.get_name(), self.obj._uuid, val)
            except ValueError:
                # We may be profiling after the playbook has ended
                self.running = False
        time.sleep(self._poll_interval)


def csv_writer(writer, timestamp, task_name, task_uuid, value):
    writer.writerow([timestamp, task_name, task_uuid, value])


def json_writer(writer, timestamp, task_name, task_uuid, value):
    data = {
        'timestamp': timestamp,
        'task_name': task_name,
        'task_uuid': task_uuid,
        'value': value,
    }
    writer.write('%s%s%s' % (RS, json.dumps(data, cls=AnsibleJSONEncoder), LF))


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'cgroup_perf_recap'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display)

        self._features = ('memory', 'cpu', 'pids')

        self._units = {
            'memory': 'MB',
            'cpu': '%',
            'pids': '',
        }

        self.task_results = dict_fromkeys(self._features, default=list)
        self._profilers = dict.fromkeys(self._features)
        self._files = dict.fromkeys(self._features)
        self._writers = dict.fromkeys(self._features)

        self._file_per_task = False
        self._counter = 0

    def _open_files(self, task_uuid=None):
        output_format = self._output_format
        output_dir = self._output_dir

        for feature in self._features:
            data = {
                b'counter': to_bytes(self._counter),
                b'task_uuid': to_bytes(task_uuid),
                b'feature': to_bytes(feature),
                b'ext': to_bytes(output_format)
            }

            if self._files.get(feature):
                try:
                    self._files[feature].close()
                except Exception:
                    pass

            filename = self._file_name_format % data

            self._files[feature] = open(os.path.join(output_dir, filename), 'w+')
            if output_format == b'csv':
                self._writers[feature] = partial(csv_writer, csv.writer(self._files[feature]))
            elif output_format == b'json':
                self._writers[feature] = partial(json_writer, self._files[feature])

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        cpu_poll_interval = self.get_option('cpu_poll_interval')
        memory_poll_interval = self.get_option('memory_poll_interval')
        pid_poll_interval = self.get_option('pid_poll_interval')
        self._display_recap = self.get_option('display_recap')

        control_group = to_bytes(self.get_option('control_group'), errors='surrogate_or_strict')
        self.mem_max_file = b'/sys/fs/cgroup/memory/%s/memory.max_usage_in_bytes' % control_group
        mem_current_file = b'/sys/fs/cgroup/memory/%s/memory.usage_in_bytes' % control_group
        cpu_usage_file = b'/sys/fs/cgroup/cpuacct/%s/cpuacct.usage' % control_group
        pid_current_file = b'/sys/fs/cgroup/pids/%s/pids.current' % control_group

        for path in (self.mem_max_file, mem_current_file, cpu_usage_file, pid_current_file):
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
            with open(cpu_usage_file, 'w+') as f:
                f.write('0')
        except Exception as e:
            self._display.warning(
                u'Unable to reset CPU usage value in %s: %s' % (to_text(cpu_usage_file), to_text(e))
            )
            self.disabled = True
            return

        self._profiler_map = {
            'memory': partial(MemoryProf, mem_current_file, poll_interval=memory_poll_interval),
            'cpu': partial(CpuProf, cpu_usage_file, poll_interval=cpu_poll_interval),
            'pids': partial(PidsProf, pid_current_file, poll_interval=pid_poll_interval),
        }

        write_files = self.get_option('write_files')
        file_per_task = self.get_option('file_per_task')
        self._output_format = to_bytes(self.get_option('output_format'))
        output_dir = to_bytes(self.get_option('output_dir'), errors='surrogate_or_strict')
        try:
            output_dir %= to_bytes(datetime.datetime.now().isoformat())
        except TypeError:
            pass

        self._output_dir = output_dir

        file_name_format = to_bytes(self.get_option('file_name_format'))

        if write_files:
            if file_per_task:
                self._file_per_task = True
                if file_name_format == b'%(feature)s.%(ext)s':
                    file_name_format = b'%(counter)s-%(task_uuid)s-%(feature)s.%(ext)s'
            else:
                file_name_format = to_bytes(self.get_option('file_name_format'))

            self._file_name_format = file_name_format

            if not os.path.exists(output_dir):
                try:
                    os.mkdir(output_dir)
                except Exception as e:
                    self._display.warning(
                        u'Could not create the output directory at %s: %s' % (to_text(output_dir), to_text(e))
                    )
                    self.disabled = True
                    return

            if not self._file_per_task:
                self._open_files()

    def _profile(self, obj=None):
        prev_task = None
        results = dict.fromkeys(self._features)
        for dummy, f in self._files.items():
            if f is None:
                continue
            try:
                f.close()
            except Exception:
                pass

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
            if self._file_per_task:
                self._open_files(task_uuid=obj._uuid)

            for feature in self._features:
                self._profilers[feature] = self._profiler_map[feature](obj=obj, writer=self._writers[feature])
                self._profilers[feature].start()

            self._counter += 1

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._profile(task)

    def v2_playbook_on_stats(self, stats):
        self._profile()

        if not self._display_recap:
            return

        with open(self.mem_max_file) as f:
            max_results = int(f.read().strip()) / 1024 / 1024

        self._display.banner('CGROUP PERF RECAP')
        self._display.display('Memory Execution Maximum: %0.2fMB\n' % max_results)
        for name, data in self.task_results.items():
            if name == 'memory':
                continue
            try:
                self._display.display(
                    '%s Execution Maximum: %0.2f%s\n' % (name, max((t[1] for t in data)), self._units[name])
                )
            except Exception as e:
                self._display.display('%s profiling error: no results collected: %s\n' % (name, e))

        self._display.display('\n')

        for name, data in self.task_results.items():
            if data:
                self._display.display('%s:\n' % name)
            for task, value in data:
                self._display.display('%s (%s): %0.2f%s' % (task.get_name(), task._uuid, value, self._units[name]))
            self._display.display('\n')
