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

from __future__ import annotations

import io
import os
import signal
import sys
import textwrap
import traceback
import types
import typing as t
from multiprocessing.queues import Queue

from ansible import context
from ansible._internal import _task
from ansible.errors import AnsibleConnectionFailure, AnsibleError
from ansible.executor.task_executor import TaskExecutor
from ansible.executor.task_queue_manager import FinalQueue, STDIN_FILENO, STDOUT_FILENO, STDERR_FILENO
from ansible.executor.task_result import _RawTaskResult
from ansible.inventory.host import Host
from ansible.module_utils.common.collections import is_sequence
from ansible.module_utils.common.text.converters import to_text
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.task import Task
from ansible.playbook.play_context import PlayContext
from ansible.plugins.loader import init_plugin_loader
from ansible.utils.context_objects import CLIArgs
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display
from ansible.utils.multiprocessing import context as multiprocessing_context
from ansible.vars.manager import VariableManager

from jinja2.exceptions import TemplateNotFound

__all__ = ['WorkerProcess']

display = Display()

current_worker = None


class WorkerQueue(Queue):
    """Queue that raises AnsibleError items on get()."""
    def get(self, *args, **kwargs):
        result = super(WorkerQueue, self).get(*args, **kwargs)
        if isinstance(result, AnsibleError):
            raise result
        return result


class WorkerProcess(multiprocessing_context.Process):  # type: ignore[name-defined]
    """
    The worker thread class, which uses TaskExecutor to run tasks
    read from a job queue and pushes results into a results queue
    for reading later.
    """

    def __init__(
            self,
            *,
            final_q: FinalQueue,
            task_vars: dict,
            host: Host,
            task: Task,
            play_context: PlayContext,
            loader: DataLoader,
            variable_manager: VariableManager,
            shared_loader_obj: types.SimpleNamespace,
            worker_id: int,
            cliargs: CLIArgs
    ) -> None:

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

        self.worker_queue = WorkerQueue(ctx=multiprocessing_context)
        self.worker_id = worker_id

        self._cliargs = cliargs

    def _term(self, signum, frame) -> None:
        """
        terminate the process group created by calling setsid when
        a terminate signal is received by the fork
        """
        os.killpg(self.pid, signum)

    def start(self) -> None:
        """
        multiprocessing.Process replaces the worker's stdin with a new file
        but we wish to preserve it if it is connected to a terminal.
        Therefore dup a copy prior to calling the real start(),
        ensuring the descriptor is preserved somewhere in the new child, and
        make sure it is closed in the parent when start() completes.
        """

        # FUTURE: this lock can be removed once a more generalized pre-fork thread pause is in place
        with display._lock:
            super(WorkerProcess, self).start()
        # Since setsid is called later, if the worker is termed
        # it won't term the new process group
        # register a handler to propagate the signal
        signal.signal(signal.SIGTERM, self._term)
        signal.signal(signal.SIGINT, self._term)

    def _hard_exit(self, e: str) -> t.NoReturn:
        """
        There is no safe exception to return to higher level code that does not
        risk an innocent try/except finding itself executing in the wrong
        process. All code executing above WorkerProcess.run() on the stack
        conceptually belongs to another program.
        """

        try:
            display.debug(u"WORKER HARD EXIT: %s" % to_text(e))
        except BaseException:
            # If the cause of the fault is IOError being generated by stdio,
            # attempting to log a debug message may trigger another IOError.
            # Try printing once then give up.
            pass

        os._exit(1)

    def _detach(self) -> None:
        """
        The intent here is to detach the child process from the inherited stdio fds,
        including /dev/tty. Children should use Display instead of direct interactions
        with stdio fds.
        """
        try:
            os.setsid()
            # Create new fds for stdin/stdout/stderr, but also capture python uses of sys.stdout/stderr
            for fds, mode in (
                    ((STDIN_FILENO,), os.O_RDWR | os.O_NONBLOCK),
                    ((STDOUT_FILENO, STDERR_FILENO), os.O_WRONLY),
            ):
                stdio = os.open(os.devnull, mode)
                for fd in fds:
                    os.dup2(stdio, fd)
                os.close(stdio)
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()
            sys.stdin = os.fdopen(STDIN_FILENO, 'r', closefd=False)
            # Close stdin so we don't get hanging workers
            # We use sys.stdin.close() for places where sys.stdin is used,
            # to give better errors, and to prevent fd 0 reuse
            sys.stdin.close()
        except Exception as e:
            display.debug(f'Could not detach from stdio: {traceback.format_exc()}')
            display.error(f'Could not detach from stdio: {e}')
            os._exit(1)

    def run(self) -> None:
        """
        Wrap _run() to ensure no possibility an errant exception can cause
        control to return to the StrategyBase task loop, or any other code
        higher in the stack.

        As multiprocessing in Python 2.x provides no protection, it is possible
        a try/except added in far-away code can cause a crashed child process
        to suddenly assume the role and prior state of its parent.
        """
        # Set the queue on Display so calls to Display.display are proxied over the queue
        display.set_queue(self._final_q)
        self._detach()
        try:
            with _task.TaskContext(self._task):
                return self._run()
        except BaseException:
            self._hard_exit(traceback.format_exc())

    def _run(self) -> None:
        """
        Called when the process is started.  Pushes the result onto the
        results queue. We also remove the host from the blocked hosts list, to
        signify that they are ready for their next task.
        """

        # import cProfile, pstats, StringIO
        # pr = cProfile.Profile()
        # pr.enable()

        global current_worker
        current_worker = self

        if multiprocessing_context.get_start_method() != 'fork':
            # This branch is unused currently, as we hardcode fork
            # TODO
            # * move into a setup func run in `run`, before `_detach`
            # * playbook relative content
            # * display verbosity
            # * ???
            context.CLIARGS = self._cliargs
            # Initialize plugin loader after parse, so that the init code can utilize parsed arguments
            cli_collections_path = context.CLIARGS.get('collections_path') or []
            if not is_sequence(cli_collections_path):
                # In some contexts ``collections_path`` is singular
                cli_collections_path = [cli_collections_path]
            init_plugin_loader(cli_collections_path)

        try:
            # execute the task and build a _RawTaskResult from the result
            display.debug("running TaskExecutor() for %s/%s" % (self._host, self._task))
            executor_result = TaskExecutor(
                self._host,
                self._task,
                self._task_vars,
                self._play_context,
                self._loader,
                self._shared_loader_obj,
                self._final_q,
                self._variable_manager,
            ).run()

            display.debug("done running TaskExecutor() for %s/%s [%s]" % (self._host, self._task, self._task._uuid))
            self._host.vars = dict()
            self._host.groups = []

            for name, stdio in (('stdout', sys.stdout), ('stderr', sys.stderr)):
                if data := stdio.getvalue():  # type: ignore[union-attr]
                    display.warning(
                        (
                            f'WorkerProcess for [{self._host}/{self._task}] errantly sent data directly to {name} instead of using Display:\n'
                            f'{textwrap.indent(data[:256], "    ")}\n'
                        ),
                        formatted=True
                    )

            # put the result on the result queue
            display.debug("sending task result for task %s" % self._task._uuid)
            try:
                self._final_q.send_task_result(_RawTaskResult(
                    host=self._host,
                    task=self._task,
                    return_data=executor_result,
                    task_fields=self._task.dump_attrs(),
                ))
            except Exception as ex:
                try:
                    raise AnsibleError("Task result omitted due to queue send failure.") from ex
                except Exception as ex_wrapper:
                    self._final_q.send_task_result(_RawTaskResult(
                        host=self._host,
                        task=self._task,
                        return_data=ActionBase.result_dict_from_exception(ex_wrapper),  # Overriding the task result, to represent the failure
                        task_fields={},  # The failure pickling may have been caused by the task attrs, omit for safety
                    ))

            display.debug("done sending task result for task %s" % self._task._uuid)

        except AnsibleConnectionFailure as ex:
            return_data = ActionBase.result_dict_from_exception(ex)
            return_data.pop('failed')
            return_data.update(unreachable=True)

            self._host.vars = dict()
            self._host.groups = []
            self._final_q.send_task_result(_RawTaskResult(
                host=self._host,
                task=self._task,
                return_data=return_data,
                task_fields=self._task.dump_attrs(),
            ))

        except Exception as ex:
            if not isinstance(ex, (IOError, EOFError, KeyboardInterrupt, SystemExit)) or isinstance(ex, TemplateNotFound):
                try:
                    self._host.vars = dict()
                    self._host.groups = []
                    self._final_q.send_task_result(_RawTaskResult(
                        host=self._host,
                        task=self._task,
                        return_data=ActionBase.result_dict_from_exception(ex),
                        task_fields=self._task.dump_attrs(),
                    ))
                except Exception:
                    display.debug(u"WORKER EXCEPTION: %s" % to_text(ex))
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

    def _clean_up(self) -> None:
        # NOTE: see note in init about forks
        # ensure we cleanup all temp files for this worker
        self._loader.cleanup_all_tmp_files()
