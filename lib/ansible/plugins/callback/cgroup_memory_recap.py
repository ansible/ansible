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
'''

import time
import threading

from ansible.plugins.callback import CallbackBase


class MemProf(threading.Thread):
    """Python thread for recording memory usage"""
    def __init__(self, path, obj=None):
        threading.Thread.__init__(self)
        self.obj = obj
        self.path = path
        self.results = []
        self.running = True

    def run(self):
        while self.running:
            with open(self.path) as f:
                val = f.read()
            self.results.append(int(val.strip()) / 1024 / 1024)
            time.sleep(0.001)


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'cgroup_memory_recap'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display)

        self._task_memprof = None

        self.task_results = []

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self.cgroup_max_file = self.get_option('max_mem_file')
        self.cgroup_current_file = self.get_option('cur_mem_file')

        with open(self.cgroup_max_file, 'w+') as f:
            f.write('0')

    def _profile_memory(self, obj=None):
        prev_task = None
        results = None
        try:
            self._task_memprof.running = False
            results = self._task_memprof.results
            prev_task = self._task_memprof.obj
        except AttributeError:
            pass

        if obj is not None:
            self._task_memprof = MemProf(self.cgroup_current_file, obj=obj)
            self._task_memprof.start()

        if results is not None:
            self.task_results.append((prev_task, max(results)))

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._profile_memory(task)

    def v2_playbook_on_stats(self, stats):
        self._profile_memory()

        with open(self.cgroup_max_file) as f:
            max_results = int(f.read().strip()) / 1024 / 1024

        self._display.banner('CGROUP MEMORY RECAP')
        self._display.display('Execution Maximum: %0.2fMB\n\n' % max_results)

        for task, memory in self.task_results:
            self._display.display('%s (%s): %0.2fMB' % (task.get_name(), task._uuid, memory))
