# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

DOCUMENTATION = '''
    process: forking
    short_description: Spawn workers using multiprocessing forks.
    description:
        - This process model creates workers using the Python multiprocessing library. Workers are created
          on-demand as jobs are queued up, up to the maximum number of forks allowed.
    author: ansible (@core)
    version_added: 2.8
    options: {}
'''

import multiprocessing
import os
import sys
import time
import threading
import traceback

from jinja2.exceptions import TemplateNotFound

HAS_PYCRYPTO_ATFORK = False
try:
    from Crypto.Random import atfork
    HAS_PYCRYPTO_ATFORK = True
except Exception:
    # We only need to call atfork if pycrypto is used because it will need to
    # reinitialize its RNG.  Since old paramiko could be using pycrypto, we
    # need to take charge of calling it.
    pass

from ansible.errors import AnsibleError, AnsibleConnectionFailure
from ansible.executor.task_executor import TaskExecutor
from ansible.executor.task_result import TaskResult
from ansible.module_utils._text import to_text
from ansible.module_utils.six.moves import queue as Queue
from ansible.plugins.process import ProcessModelBase, ResultsSentinel
from ansible.utils.display import Display


display = Display()


def results_thread_main(pm):
    while True:
        try:
            result = pm._worker_results_q.get()
            if isinstance(result, ResultsSentinel):
                break
            else:
                pm._final_q_lock.acquire()
                pm._final_q.append(result)
                pm._final_q_lock.release()
        except (IOError, EOFError, TypeError) as e:
            break
        except Queue.Empty:
            pass


__all__ = ['ProcessModel', ]


class ProcessModel(ProcessModelBase):
    def __init__(self, tqm):
        super(ProcessModel, self).__init__(tqm)

        # save a couple of things from the TQM we need for forking
        self._loader = tqm._loader
        self._variable_manager = tqm._variable_manager

        # create the worker results queue, which is where all workers
        # send their results. The results thread reads from this in the
        # background and copies the results to the final_q deque object
        try:
            self._worker_results_q = multiprocessing.Queue()
        except OSError as e:
            raise AnsibleError("Unable to use multiprocessing, this is normally caused by lack of access to /dev/shm: %s" % to_text(e))

        # create the result processing thread for reading results in the background
        self._results_thread = threading.Thread(target=results_thread_main, args=(self,))
        self._results_thread.daemon = True
        self._results_thread.start()

    def initialize_workers(self, num):
        self._terminated = False
        self._cur_worker = 0
        self._workers = [None for i in range(num)]

    def put_job(self, host, task, play_context, task_vars):
        try:
            queued = False
            starting_worker = self._cur_worker
            while True:
                worker_prc = self._workers[self._cur_worker]
                if worker_prc is None or not worker_prc.is_alive():
                    worker_prc = WorkerProcess(
                        self,
                        task_vars,
                        host,
                        task,
                        play_context,
                        self._loader,
                        self._variable_manager,
                        self._shared_loader_obj,
                    )
                    self._workers[self._cur_worker] = worker_prc
                    worker_prc.start()
                    self._tqm.send_callback('v2_runner_on_start', host, task)
                    display.debug("worker is %d (out of %d available)" % (self._cur_worker + 1, len(self._workers)))
                    queued = True
                self._cur_worker += 1
                if self._cur_worker >= len(self._workers):
                    self._cur_worker = 0
                if queued:
                    break
                elif self._cur_worker == starting_worker:
                    time.sleep(0.0001)

            return True
        except (EOFError, IOError, AssertionError) as e:
            # most likely an abort
            display.debug("got an error while queuing: %s" % e)
            return False

    def put_result(self, data):
        self._worker_results_q.put(data, block=False)

    def cleanup(self):
        for worker in self._workers:
            if worker and worker.is_alive():
                worker.terminate()
        self._worker_results_q.put(self._sentinel)
        self._worker_results_q.close()
        self.terminate()


class WorkerProcess(multiprocessing.Process):
    '''
    The worker thread class, which uses TaskExecutor to run tasks
    read from a job queue and pushes results into a results queue
    for reading later.
    '''

    def __init__(self, process_manager, task_vars, host, task, play_context, loader, variable_manager, shared_loader_obj):

        super(WorkerProcess, self).__init__()
        # takes a task queue manager as the sole param:
        self._process_manager = process_manager
        self._task_vars = task_vars
        self._host = host
        self._task = task
        self._play_context = play_context
        self._loader = loader
        self._variable_manager = variable_manager
        self._shared_loader_obj = shared_loader_obj

    def _save_stdin(self):
        self._new_stdin = os.devnull
        try:
            if sys.stdin.isatty() and sys.stdin.fileno() is not None:
                try:
                    self._new_stdin = os.fdopen(os.dup(sys.stdin.fileno()))
                except OSError:
                    # couldn't dupe stdin, most likely because it's
                    # not a valid file descriptor, so we just rely on
                    # using the one that was passed in
                    pass
        except (AttributeError, ValueError):
            # couldn't get stdin's fileno, so we just carry on
            pass

    def start(self):
        '''
        multiprocessing.Process replaces the worker's stdin with a new file
        opened on os.devnull, but we wish to preserve it if it is connected to
        a terminal. Therefore dup a copy prior to calling the real start(),
        ensuring the descriptor is preserved somewhere in the new child, and
        make sure it is closed in the parent when start() completes.
        '''

        self._save_stdin()
        try:
            return super(WorkerProcess, self).start()
        finally:
            if self._new_stdin != os.devnull:
                self._new_stdin.close()

    def _hard_exit(self, e):
        '''
        There is no safe exception to return to higher level code that does not
        risk an innocent try/except finding itself executing in the wrong
        process. All code executing above WorkerProcess.run() on the stack
        conceptually belongs to another program.
        '''

        try:
            display.debug(u"WORKER HARD EXIT: %s" % to_text(e))
        except BaseException:
            # If the cause of the fault is IOError being generated by stdio,
            # attempting to log a debug message may trigger another IOError.
            # Try printing once then give up.
            pass

        os._exit(1)

    def run(self):
        '''
        Wrap _run() to ensure no possibility an errant exception can cause
        control to return to the StrategyBase task loop, or any other code
        higher in the stack.

        As multiprocessing in Python 2.x provides no protection, it is possible
        a try/except added in far-away code can cause a crashed child process
        to suddenly assume the role and prior state of its parent.
        '''
        try:
            return self._run()
        except BaseException as e:
            self._hard_exit(e)

    def _run(self):
        '''
        Called when the process is started.  Pushes the result onto the
        results queue. We also remove the host from the blocked hosts list, to
        signify that they are ready for their next task.
        '''

        # import cProfile, pstats, StringIO
        # pr = cProfile.Profile()
        # pr.enable()

        if HAS_PYCRYPTO_ATFORK:
            atfork()

        try:
            # execute the task and build a TaskResult from the result
            display.debug("running TaskExecutor() for %s/%s" % (self._host, self._task))
            executor_result = TaskExecutor(
                self._host,
                self._task,
                self._task_vars,
                self._play_context,
                self._new_stdin,
                self._loader,
                self._shared_loader_obj,
                self._process_manager,
            ).run()

            display.debug("done running TaskExecutor() for %s/%s [%s]" % (self._host, self._task, self._task._uuid))
            self._host.vars = dict()
            self._host.groups = []
            task_result = TaskResult(
                self._host.name,
                self._task._uuid,
                executor_result,
                task_fields=self._task.dump_attrs(),
            )

            # put the result on the result queue
            display.debug("sending task result for task %s" % self._task._uuid)
            self._process_manager.put_result(task_result)
            display.debug("done sending task result for task %s" % self._task._uuid)

        except AnsibleConnectionFailure:
            self._host.vars = dict()
            self._host.groups = []
            task_result = TaskResult(
                self._host.name,
                self._task._uuid,
                dict(unreachable=True),
                task_fields=self._task.dump_attrs(),
            )
            self._process_manager.put_result(task_result)

        except Exception as e:
            if not isinstance(e, (IOError, EOFError, KeyboardInterrupt, SystemExit)) or isinstance(e, TemplateNotFound):
                try:
                    self._host.vars = dict()
                    self._host.groups = []
                    task_result = TaskResult(
                        self._host.name,
                        self._task._uuid,
                        dict(failed=True, exception=to_text(traceback.format_exc()), stdout=''),
                        task_fields=self._task.dump_attrs(),
                    )
                    self._process_manager.put_result(task_result)
                except Exception:
                    display.debug(u"WORKER EXCEPTION: %s" % to_text(e))
                    display.debug(u"WORKER TRACEBACK: %s" % to_text(traceback.format_exc()))

        display.debug("WORKER PROCESS EXITING")

        # pr.disable()
        # s = StringIO.StringIO()
        # sortby = 'time'
        # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        # ps.print_stats()
        # with open('worker_%06d.stats' % os.getpid(), 'w') as f:
        #     f.write(s.getvalue())
