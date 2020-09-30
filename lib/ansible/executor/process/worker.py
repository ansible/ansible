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

import os
import sys
import time
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

from ansible.errors import AnsibleConnectionFailure, AnsibleError
from ansible.executor.task_executor import TaskExecutor
from ansible.executor.task_result import TaskResult
from ansible.module_utils._text import to_text
from ansible.plugins import loader as plugin_loader
from ansible.template import Templar
from ansible.utils.display import Display
from ansible.utils.multiprocessing import context as multiprocessing_context

__all__ = ['MaybeWorker', 'WorkerProcess']


display = Display()


class WorkerShortCircuit(StopIteration):
    def __init__(self, task_result):
        self.task_result = task_result


def skip_worker(host, task):
    # FIXME skip_worker_when(host, task)
    # FIXME skip_worker_include_tasks(host, task)
    # FIXME skip_worker_include_role(host, task)
    pass


def skip_worker_include_role(host, task):
    # FIXME this check is still left in TaskExecutor._execute to account for loops
    if task.action == 'include_role':
        raise WorkerShortCircuit(
            TaskResult(
                host=host.name,
                task=task._uuid,
                return_data={
                    'include_args': task.args.copy(),
                }
            )
        )


class MaybeWorker:
    '''This class encapsulates a task worker creation, possibly skipping
    creating the worker entirely and sending a skipped TaskResult directly
    to the results queue. It is somewhat an inter step (as a part of POC
    for moving some of the logic pre-fork) between having only one process
    model (forking) and having process/worker model abstraction, and ability
    to short-circuit worker creation in addition.
    '''

    def __init__(self, tqm):
        self._tqm = tqm
        self._workers = tqm._workers
        self._variable_manager = tqm.get_variable_manager()
        self._loader = tqm.get_loader()
        self._final_q = tqm._final_q
        self._cur_worker = 0

    def queue_task(self, host, task, task_vars, play_context):
        try:
            if not task.loop and not task.loop_with:
                # FIXME remove code from TaskExecutor._execute() that is being moved into skip_worker
                #       but keep/move it into TaskExecutor._run_loop() to account for loops
                skip_worker(host, task)
            else:
                # FIXME move TaskExecutor._get_loop_items here? need to pass item to TE if non-empty
                # FIXME if the cond is trivial and independent on loop vars, can we short-circuit?
                # FIXME process loop here pre-fork if the task is include?
                #       1. process when per item
                #       2. process loop vars per item
                #       3. create a result per item
                #       4. send result per time
                #       5. send ALL results
                pass
        except WorkerShortCircuit as short_circuit:
            display.debug("skipping creating a worker for %s/%s" % (host, task))
            display.debug("sending task result for task %s" % task._uuid)
            self._tqm.send_callback('v2_runner_on_start', host, task)
            self._final_q.send_task_result(
                host.name,
                task._uuid,
                short_circuit.task_result,
                task_fields=task.dump_attrs(),
            )
            display.debug("done sending task result for task %s" % task._uuid)
        else:
            # create a templar and template things we need later for the queuing process
            templar = Templar(loader=self._loader, variables=task_vars)

            # FIXME the worker creation below should be abstracted further to
            # account for additional processing models

            # TODO: Is the below TODO still relevant after pre-fork changes?
            # TODO: remove play_context as this does not take delegation into account, task itself should hold values
            #  for connection/shell/become/terminal plugin options to finalize.
            #  Kept for now for backwards compatibility and a few functions that are still exclusive to it.
            # TODO: Decide if the first TODO about the above TODO is too meta.

            # We might throw AnsibleError here, but we let it propagate up.

            # apply the given task's information to the connection info,
            # which may override some fields already set by the play or
            # the options specified on the command line
            play_context = play_context.set_task_and_variable_override(
                task=task,
                variables=task_vars,
                templar=templar)

            # play_context validation
            # fields set from the play/task may be based on variables, so we have to
            # do the same kind of post validation step on it here before we use it.
            play_context.post_validate(templar=templar)

            # now that the play context is finalized, if the remote_addr is not set
            # default to using the host's address field as the remote address
            if not play_context.remote_addr:
                play_context.remote_addr = host.address

            # We also add "magic" variables back into the variables dict to make sure
            # a certain subset of variables exist.
            play_context.update_vars(task_vars)

            # FIXME task validation/templating

            try:
                throttle = int(templar.template(task.throttle))
            except Exception as e:
                raise AnsibleError("Failed to convert the throttle value to an integer.", obj=task._ds, orig_exc=e)

            # Determine the "rewind point" of the worker list. This means we start
            # iterating over the list of workers until the end of the list is found.
            # Normally, that is simply the length of the workers list (as determined
            # by the forks or serial setting), however a task/block/play may "throttle"
            # that limit down.
            rewind_point = len(self._workers)
            # FIXME re-enable throttling, need to pass ALLOW_BASE_THROTTLING from the strategy
            #if throttle > 0 and self.ALLOW_BASE_THROTTLING:
            #    if task.run_once:
            #        display.debug("Ignoring 'throttle' as 'run_once' is also set for '%s'" % task.get_name())
            #    else:
            #        if throttle <= rewind_point:
            #            display.debug("task: %s, throttle: %d" % (task.get_name(), throttle))
            #            rewind_point = throttle

            queued = False
            starting_worker = self._cur_worker
            while not queued:
                if self._cur_worker >= rewind_point:
                    self._cur_worker = 0

                worker_prc = self._workers[self._cur_worker]
                if worker_prc is None or not worker_prc.is_alive():
                    worker_prc = WorkerProcess(self._final_q, task_vars, host, task, play_context, self._loader, self._variable_manager, plugin_loader)
                    self._workers[self._cur_worker] = worker_prc
                    self._tqm.send_callback('v2_runner_on_start', host, task)
                    worker_prc.start()
                    display.debug("worker is %d (out of %d available)" % (self._cur_worker + 1, len(self._workers)))
                    queued = True

                self._cur_worker += 1

                if self._cur_worker >= rewind_point:
                    self._cur_worker = 0

                if self._cur_worker == starting_worker:
                    time.sleep(0.0001)


class WorkerProcess(multiprocessing_context.Process):
    '''
    The worker thread class, which uses TaskExecutor to run tasks
    read from a job queue and pushes results into a results queue
    for reading later.
    '''

    def __init__(self, final_q, task_vars, host, task, play_context, loader, variable_manager, shared_loader_obj):

        super(WorkerProcess, self).__init__()
        # takes a task queue manager as the sole param:
        self._final_q = final_q
        self._task_vars = task_vars
        self._host = host
        self._task = task
        self._play_context = play_context
        self._loader = loader
        self._variable_manager = variable_manager
        self._shared_loader_obj = shared_loader_obj

        # NOTE: this works due to fork, if switching to threads this should change to per thread storage of temp files
        # clear var to ensure we only delete files for this child
        self._loader._tempfiles = set()

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
                self._final_q
            ).run()

            display.debug("done running TaskExecutor() for %s/%s [%s]" % (self._host, self._task, self._task._uuid))
            self._host.vars = dict()
            self._host.groups = []

            # put the result on the result queue
            display.debug("sending task result for task %s" % self._task._uuid)
            self._final_q.send_task_result(
                self._host.name,
                self._task._uuid,
                executor_result,
                task_fields=self._task.dump_attrs(),
            )
            display.debug("done sending task result for task %s" % self._task._uuid)

        except AnsibleConnectionFailure:
            self._host.vars = dict()
            self._host.groups = []
            self._final_q.send_task_result(
                self._host.name,
                self._task._uuid,
                dict(unreachable=True),
                task_fields=self._task.dump_attrs(),
            )

        except Exception as e:
            if not isinstance(e, (IOError, EOFError, KeyboardInterrupt, SystemExit)) or isinstance(e, TemplateNotFound):
                try:
                    self._host.vars = dict()
                    self._host.groups = []
                    self._final_q.send_task_result(
                        self._host.name,
                        self._task._uuid,
                        dict(failed=True, exception=to_text(traceback.format_exc()), stdout=''),
                        task_fields=self._task.dump_attrs(),
                    )
                except Exception:
                    display.debug(u"WORKER EXCEPTION: %s" % to_text(e))
                    display.debug(u"WORKER TRACEBACK: %s" % to_text(traceback.format_exc()))
                finally:
                    self._clean_up()

        display.debug("WORKER PROCESS EXITING")

        # pr.disable()
        # s = StringIO.StringIO()
        # sortby = 'time'
        # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        # ps.print_stats()
        # with open('worker_%06d.stats' % os.getpid(), 'w') as f:
        #     f.write(s.getvalue())

    def _clean_up(self):
        # NOTE: see note in init about forks
        # ensure we cleanup all temp files for this worker
        self._loader.cleanup_all_tmp_files()
