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
    callback: cgroup_memory_recap
    callback_type: aggregate
    requirements:
      - whitelist in configuration
      - cgroups
    short_description: Profiles maximum memory usage of tasks and full execution using cgroups
    version_added: "2.6"
    description:
        - This is an ansible callback plugin that profiles maximum memory usage of ansible and individual tasks, and displays a recap at the end using cgroups
    notes:
        - Requires ansible to be run from within a cgroup, such as with C(cgexec -g memory:ansible_profile ansible-playbook ...)
        - This cgroup should only be used by ansible to get accurate results
        - To create the cgroup, first use a command such as C(sudo cgcreate -a ec2-user:ec2-user -t ec2-user:ec2-user -g memory:ansible_profile)
    options:
      max_mem_file:
        required: True
        description: Path to cgroups C(memory.max_usage_in_bytes) file. Example C(/sys/fs/cgroup/memory/ansible_profile/memory.max_usage_in_bytes)
        env:
          - name: CGROUP_MAX_MEM_FILE
        ini:
          - section: callback_cgroupmemrecap
            key: max_mem_file
      cur_mem_file:
        required: True
        description: Path to C(memory.usage_in_bytes) file. Example C(/sys/fs/cgroup/memory/ansible_profile/memory.usage_in_bytes)
        env:
          - name: CGROUP_CUR_MEM_FILE
        ini:
          - section: callback_cgroupmemrecap
            key: cur_mem_file
      cgroup_control_group:
        env:
          - name: CGROUP_CONTROL_GROUP
      csv_file:
        description: Output path for CSV file containing recorded memory readings
        env:
            - name: CGROUP_CSV_FILE
        ini:
            - section: callback_cgroupmemrecap
              key: csv_file
'''

import csv
import time
import threading

from ansible.module_utils._text import to_bytes
from ansible.plugins.callback import CallbackBase


class MemProf(threading.Thread):
    """Python thread for recording memory usage"""
    def __init__(self, path, obj=None, csvwriter=None):
        threading.Thread.__init__(self)
        self.obj = obj
        self.path = path
        self.results = []
        self.running = True
        self.csvwriter = csvwriter

    def run(self):
        while self.running:
            with open(self.path) as f:
                val = f.read()
            self.results.append(int(val.strip()) / 1024 / 1024)
            if self.csvwriter:
                self.csvwriter.writerow([time.time(), self.obj.get_name(), val.strip()])
            time.sleep(0.001)


class CpuProf(threading.Thread):
    def __init__(self, path, obj=None):
        threading.Thread.__init__(self)
        self.obj = obj
        self.path = path
        self.results = []
        self.running = True

    def run(self):
        while self.running:
            with open(self.path) as f:
                start_time = time.time() * 1000**2
                start_usage = int(f.read().strip()) / 1000
            time.sleep(0.1)
            with open(self.path) as f:
                end_time = time.time() * 1000**2
                end_usage = int(f.read().strip()) / 1000
            self.results.append((end_usage - start_usage) / (end_time - start_time) * 100)


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'cgroup_memory_recap'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display)

        self._task_memprof = None
        self._task_cpuprof = None

        self.task_results = {
            'memory': [],
            'cpu': [],
        }

        self._csv_file = None
        self._csv_writer = None

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        #self.mem_max_file = self.get_option('max_mem_file')
        #self.mem_current_file = self.get_option('cur_mem_file')

        self.control_group = to_bytes(self.get_option('cgroup_control_group'))
        self.mem_max_file = b'/sys/fs/cgroup/memory/%s/memory.max_usage_in_bytes' % self.control_group
        self.mem_current_file = b'/sys/fs/cgroup/memory/%s/memory.usage_in_bytes' % self.control_group
        self.cpu_usage_file = b'/sys/fs/cgroup/cpuacct/%s/cpuacct.usage' % self.control_group

        for path in (self.mem_max_file, self.mem_current_file, self.cpu_usage_file):
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

        csv_file = self.get_option('csv_file')
        if csv_file:
            self._csv_file = open(csv_file, 'w+')
            self._csv_writer = csv.writer(self._csv_file)

    def _profile(self, obj=None):
        prev_task = None
        mem = None
        cpu = None
        try:
            self._task_memprof.running = False
            self._task_cpuprof.running = False
            mem = self._task_memprof.results
            cpu = self._task_cpuprof.results
            prev_task = self._task_memprof.obj
        except AttributeError:
            pass

        if obj is not None:
            self._task_memprof = MemProf(self.mem_current_file, obj=obj, csvwriter=self._csv_writer)
            self._task_memprof.start()
            self._task_cpuprof = CpuProf(self.cpu_usage_file, obj=obj)
            self._task_cpuprof.start()

        if mem is not None:
            try:
                self.task_results['memory'].append((prev_task, max(mem)))
            except ValueError:
                pass
        if cpu is not None:
            try:
                self.task_results['cpu'].append((prev_task, max(cpu)))
            except ValueError:
                pass

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._profile(task)

    def v2_playbook_on_stats(self, stats):
        self._profile()

        with open(self.mem_max_file) as f:
            max_results = int(f.read().strip()) / 1024 / 1024

        self._display.banner('CGROUP PERF RECAP')
        self._display.display('Memory Execution Maximum: %0.2fMB\n' % max_results)
        try:
            self._display.display('CPU Execution Maximum: %0.2f%%\n\n' % max((t[1] for t in self.task_results['cpu'])))
        except:
            self._display.display('CPU profiling error: no results collected\n\n')

        self._display.display('Memory:\n')
        for task, memory in self.task_results['memory']:
            self._display.display('%s (%s): %0.2fMB' % (task.get_name(), task._uuid, memory))

        if self.task_results['cpu']:
            self._display.display('CPU:\n')
        for task, cpu in self.task_results['cpu']:
            self._display.display('%s (%s): %0.2f%%' % (task.get_name(), task._uuid, cpu))

        if self._csv_file:
            try:
                self._csv_file.close()
            except Exception:
                pass
