# (c) 2018, Red Hat, Inc. <support@ansible.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys
import threading
import time
import traceback

from collections import deque
from jinja2.exceptions import TemplateNotFound

from ansible.errors import AnsibleConnectionFailure
from ansible.executor.process.model import ProcessModelBase, ResultsSentinel, keyboard_interrupt_event
from ansible.executor.task_executor import TaskExecutor
from ansible.executor.task_result import TaskResult
from ansible.module_utils._text import to_text

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

__all__ = ['ProcessModelThreading', ]


class ProcessModelThreading(ProcessModelBase):
    def __init__(self, tqm):
        super(ProcessModelThreading, self).__init__(tqm)

        self._job_queue = deque()
        self._job_queue_lock = threading.Lock()

    def initialize_workers(self, num):
        self._cur_worker = 0
        self._workers = []
        for i in range(num):
            w_thread = threading.Thread(target=run_worker, args=(self, self._shared_loader_obj))
            w_thread.start()
            w_lock = threading.Lock()
            self._workers.append([w_thread, w_lock])

    def get_job(self):
        data = None
        try:
            self._job_queue_lock.acquire()
            data = self._job_queue.pop()
        except:
            pass
        finally:
            self._job_queue_lock.release()
        return data

    def put_task(self, data):
        try:
            self._job_queue_lock.acquire()
            self._job_queue.appendleft(data)
        finally:
            self._job_queue_lock.release()

    def put_result(self, data):
        try:
            self._final_q_lock.acquire()
            self._final_q.appendleft(data)
        finally:
            self._final_q_lock.release()

    def cleanup(self):
        self.terminate()
        for (w_thread, w_lock) in self._workers:
            if w_thread and not w_thread.is_alive():
                w_thread.join()


def run_worker(pm, shared_loader_obj):
    '''
    The worker thread class, which uses TaskExecutor to run tasks
    read from a job queue and pushes results into a results queue
    for reading later.
    '''

    # import cProfile, pstats, StringIO
    # pr = cProfile.Profile()
    # pr.enable()

    display.debug("STARTING WORKER")
    while not pm._terminated:

        display.debug("WORKER TRYING TO GET A JOB")
        job = pm.get_job()
        if isinstance(job, ResultsSentinel) or keyboard_interrupt_event.is_set():
            break
        elif job is None:
            time.sleep(0.0001)
            continue

        display.debug("WORKER GOT A JOB")
        (host, task, play_context, task_vars) = job

        try:
            # execute the task and build a TaskResult from the result
            display.debug("running TaskExecutor() for %s/%s" % (host, task))
            executor_result = TaskExecutor(
                host,
                task,
                task_vars,
                play_context,
                sys.stdin,
                pm._tqm._loader,
                shared_loader_obj,
                pm,
            ).run()

            display.debug("done running TaskExecutor() for %s/%s" % (host, task))

            # put the result on the result queue
            display.debug("sending task result")
            pm.put_result(TaskResult(
                host.name,
                task._uuid,
                executor_result,
            ))
            display.debug("done task result")

        except AnsibleConnectionFailure:
            pm.put_result(TaskResult(
                host.name,
                task._uuid,
                dict(unreachable=True),
            ))

        except Exception as e:
            if not isinstance(e, (IOError, EOFError, KeyboardInterrupt, SystemExit)) or isinstance(e, TemplateNotFound):
                try:
                    pm.put_result(TaskResult(
                        host.name,
                        task._uuid,
                        dict(failed=True, exception=to_text(traceback.format_exc()), stdout=''),
                    ))
                except:
                    display.debug(u"WORKER EXCEPTION: %s" % to_text(e))
                    display.debug(u"WORKER TRACEBACK: %s" % to_text(traceback.format_exc()))

    # pr.disable()
    # s = StringIO.StringIO()
    # sortby = 'time'
    # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    # ps.print_stats()
    # with open('worker_%06d.stats' % os.getpid(), 'w') as f:
    #     f.write(s.getvalue())

    display.debug("WORKER PROCESS EXITING")
