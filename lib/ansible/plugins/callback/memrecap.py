# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
    callback: memrecap
    callback_type: aggregate
    requirements:
      - whitelist in configuration
      - memory_profiler (python library)
    short_description: Profiles maximum memory usage of tasks and full execution
    version_added: "2.6"
    description:
        - This is an ansible callback plugin that profiles maximum memory usage of ansible and individual tasks, and displays a recap at the end
'''

import os
import subprocess
import threading

from ansible.plugins.callback import CallbackBase

try:
    import memory_profiler as mp
    HAS_MEMORY_PROFILER = True
except ImportError:
    HAS_MEMORY_PROFILER = False


class MemProf(threading.Thread):
    """Python thread for recording memory usage"""
    def __init__(self, proc, obj=None):
        threading.Thread.__init__(self)
        self.obj = obj
        self.proc = proc
        self.results = None

    def run(self):
        self.results = mp.memory_usage(proc=self.proc, interval=0.001,
                                       include_children=True,
                                       multiprocess=False)


class FakePopen(subprocess.Popen):
    """Creates a fake Popen object that satisifies the needs of memory_profiler, allowing us to terminate profiling on demand"""
    def __init__(self, pid):
        self.pid = pid
        self.running = True

    def poll(self):
        if self.running:
            return None
        return True


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'memrecap'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display)
        if not HAS_MEMORY_PROFILER:
            self._display.warning('The required "memory_profiler" python module is not installed, disabling the "memrecap" callback plugin')
            self.disabled = True
        else:
            self._pid = os.getpid()

            self._proc = FakePopen(self._pid)
            self._task_proc = FakePopen(self._pid)

            self._task_memprof = None
            self._memprof = MemProf(self._proc)
            self._memprof.start()

        self.task_results = []

    def _profile_memory(self, obj=None):
        self._task_proc.running = False
        prev_task = None
        results = None
        try:
            while self._task_memprof.results is None:
                continue
            results = self._task_memprof.results
            prev_task = self._task_memprof.obj
        except AttributeError:
            pass

        if obj is not None:
            self._task_proc.running = True
            self._task_memprof = MemProf(self._task_proc, obj=obj)
            self._task_memprof.start()

        if results is not None:
            self.task_results.append((prev_task, max(results)))

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._profile_memory(task)

    def v2_playbook_on_stats(self, stats):
        self._profile_memory()
        self._proc.running = False

        self._display.banner('MEMORY RECAP')
        while self._memprof.results is None:
            continue
        self._display.display('Execution Maximum: %0.2fMB\n\n' % max(self._memprof.results))

        for task, memory in self.task_results:
            self._display.display('%s: %0.2fMB' % (task.get_name(), memory))
