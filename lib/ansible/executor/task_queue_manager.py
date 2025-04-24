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

import dataclasses
import os
import sys
import tempfile
import threading
import time
import typing as t
import multiprocessing.queues

from ansible import constants as C
from ansible import context
from ansible.errors import AnsibleError, ExitCode, AnsibleCallbackError
from ansible._internal._errors._handler import ErrorHandler
from ansible.executor.play_iterator import PlayIterator
from ansible.executor.stats import AggregateStats
from ansible.executor.task_result import _RawTaskResult, _WireTaskResult
from ansible.inventory.data import InventoryData
from ansible.module_utils.six import string_types
from ansible.module_utils.common.text.converters import to_native
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play_context import PlayContext
from ansible.playbook.task import Task
from ansible.plugins.loader import callback_loader, strategy_loader, module_loader
from ansible.plugins.callback import CallbackBase
from ansible._internal._templating._engine import TemplateEngine
from ansible.vars.hostvars import HostVars
from ansible.vars.manager import VariableManager
from ansible.utils.display import Display
from ansible.utils.lock import lock_decorator
from ansible.utils.multiprocessing import context as multiprocessing_context

if t.TYPE_CHECKING:
    from ansible.executor.process.worker import WorkerProcess

__all__ = ['TaskQueueManager']

STDIN_FILENO = 0
STDOUT_FILENO = 1
STDERR_FILENO = 2

display = Display()

_T = t.TypeVar('_T')


@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class CallbackSend:
    method_name: str
    wire_task_result: _WireTaskResult


class DisplaySend:
    def __init__(self, method, *args, **kwargs):
        self.method = method
        self.args = args
        self.kwargs = kwargs


@dataclasses.dataclass
class PromptSend:
    worker_id: int
    prompt: str
    private: bool = True
    seconds: int = None
    interrupt_input: t.Iterable[bytes] = None
    complete_input: t.Iterable[bytes] = None


class FinalQueue(multiprocessing.queues.SimpleQueue):
    def __init__(self, *args, **kwargs):
        kwargs['ctx'] = multiprocessing_context
        super().__init__(*args, **kwargs)

    def send_callback(self, method_name: str, task_result: _RawTaskResult) -> None:
        self.put(CallbackSend(method_name=method_name, wire_task_result=task_result.as_wire_task_result()))

    def send_task_result(self, task_result: _RawTaskResult) -> None:
        self.put(task_result.as_wire_task_result())

    def send_display(self, method, *args, **kwargs):
        self.put(
            DisplaySend(method, *args, **kwargs),
        )

    def send_prompt(self, **kwargs):
        self.put(
            PromptSend(**kwargs),
        )


class AnsibleEndPlay(Exception):
    def __init__(self, result):
        self.result = result


class TaskQueueManager:

    """
    This class handles the multiprocessing requirements of Ansible by
    creating a pool of worker forks, a result handler fork, and a
    manager object with shared datastructures/queues for coordinating
    work between all processes.

    The queue manager is responsible for loading the play strategy plugin,
    which dispatches the Play's tasks to hosts.
    """

    RUN_OK = ExitCode.SUCCESS
    RUN_ERROR = ExitCode.GENERIC_ERROR
    RUN_FAILED_HOSTS = ExitCode.HOST_FAILED
    RUN_UNREACHABLE_HOSTS = ExitCode.HOST_UNREACHABLE
    RUN_FAILED_BREAK_PLAY = 8  # never leaves PlaybookExecutor.run
    RUN_UNKNOWN_ERROR = 255  # never leaves PlaybookExecutor.run, intentionally includes the bit value for 8

    _callback_dispatch_error_handler = ErrorHandler.from_config('_CALLBACK_DISPATCH_ERROR_BEHAVIOR')

    def __init__(
        self,
        inventory: InventoryData,
        variable_manager: VariableManager,
        loader: DataLoader,
        passwords: dict[str, str | None],
        stdout_callback: str | None = None,
        run_additional_callbacks: bool = True,
        run_tree: bool = False,
        forks: int | None = None,
    ) -> None:
        self._inventory = inventory
        self._variable_manager = variable_manager
        self._loader = loader
        self._stats = AggregateStats()
        self.passwords = passwords
        self._stdout_callback: str | None | CallbackBase = stdout_callback
        self._run_additional_callbacks = run_additional_callbacks
        self._run_tree = run_tree
        self._forks = forks or 5

        self._callbacks_loaded = False
        self._callback_plugins: list[CallbackBase] = []
        self._start_at_done = False

        # make sure any module paths (if specified) are added to the module_loader
        if context.CLIARGS.get('module_path', False):
            for path in context.CLIARGS['module_path']:
                if path:
                    module_loader.add_directory(path)

        # a special flag to help us exit cleanly
        self._terminated = False

        # dictionaries to keep track of failed/unreachable hosts
        self._failed_hosts: dict[str, t.Literal[True]] = dict()
        self._unreachable_hosts: dict[str, t.Literal[True]] = dict()

        try:
            self._final_q = FinalQueue()
        except OSError as e:
            raise AnsibleError("Unable to use multiprocessing, this is normally caused by lack of access to /dev/shm: %s" % to_native(e))

        try:
            # Done in tqm, and not display, because this is only needed for commands that execute tasks
            for fd in (STDIN_FILENO, STDOUT_FILENO, STDERR_FILENO):
                os.set_inheritable(fd, False)
        except Exception as ex:
            self.warning(f"failed to set stdio as non inheritable: {ex}")

        self._callback_lock = threading.Lock()

        # A temporary file (opened pre-fork) used by connection
        # plugins for inter-process locking.
        self._connection_lockfile = tempfile.TemporaryFile()

    def _initialize_processes(self, num: int) -> None:
        self._workers: list[WorkerProcess | None] = [None] * num

    def load_callbacks(self):
        """
        Loads all available callbacks, with the exception of those which
        utilize the CALLBACK_TYPE option. When CALLBACK_TYPE is set to 'stdout',
        only one such callback plugin will be loaded.
        """

        if self._callbacks_loaded:
            return

        stdout_callback_loaded = False
        if self._stdout_callback is None:
            self._stdout_callback = C.DEFAULT_STDOUT_CALLBACK

        if isinstance(self._stdout_callback, CallbackBase):
            stdout_callback_loaded = True
        elif isinstance(self._stdout_callback, string_types):
            if self._stdout_callback not in callback_loader:
                raise AnsibleError("Invalid callback for stdout specified: %s" % self._stdout_callback)
            else:
                self._stdout_callback = callback_loader.get(self._stdout_callback)
                self._stdout_callback.set_options()
                stdout_callback_loaded = True
        else:
            raise AnsibleError("callback must be an instance of CallbackBase or the name of a callback plugin")

        # get all configured loadable callbacks (adjacent, builtin)
        callback_list = list(callback_loader.all(class_only=True))

        # add enabled callbacks that refer to collections, which might not appear in normal listing
        for c in C.CALLBACKS_ENABLED:
            # load all, as collection ones might be using short/redirected names and not a fqcn
            plugin = callback_loader.get(c, class_only=True)

            # TODO: check if this skip is redundant, loader should handle bad file/plugin cases already
            if plugin:
                # avoids incorrect and dupes possible due to collections
                if plugin not in callback_list:
                    callback_list.append(plugin)
            else:
                display.warning("Skipping callback plugin '%s', unable to load" % c)

        # for each callback in the list see if we should add it to 'active callbacks' used in the play
        for callback_plugin in callback_list:

            callback_type = getattr(callback_plugin, 'CALLBACK_TYPE', '')
            callback_needs_enabled = getattr(callback_plugin, 'CALLBACK_NEEDS_ENABLED', getattr(callback_plugin, 'CALLBACK_NEEDS_WHITELIST', False))

            # try to get collection world name first
            cnames = getattr(callback_plugin, '_redirected_names', [])
            if cnames:
                # store the name the plugin was loaded as, as that's what we'll need to compare to the configured callback list later
                callback_name = cnames[0]
            else:
                # fallback to 'old loader name'
                (callback_name, ext) = os.path.splitext(os.path.basename(callback_plugin._original_path))

            display.vvvvv("Attempting to use '%s' callback." % (callback_name))
            if callback_type == 'stdout':
                # we only allow one callback of type 'stdout' to be loaded,
                if callback_name != self._stdout_callback or stdout_callback_loaded:
                    display.vv("Skipping callback '%s', as we already have a stdout callback." % (callback_name))
                    continue
                stdout_callback_loaded = True
            elif callback_name == 'tree' and self._run_tree:
                # TODO: remove special case for tree, which is an adhoc cli option --tree
                pass
            elif not self._run_additional_callbacks or (callback_needs_enabled and (
                # only run if not adhoc, or adhoc was specifically configured to run + check enabled list
                    C.CALLBACKS_ENABLED is None or callback_name not in C.CALLBACKS_ENABLED)):
                # 2.x plugins shipped with ansible should require enabling, older or non shipped should load automatically
                continue

            try:
                callback_obj = callback_plugin()
                # avoid bad plugin not returning an object, only needed cause we do class_only load and bypass loader checks,
                # really a bug in the plugin itself which we ignore as callback errors are not supposed to be fatal.
                if callback_obj:
                    # skip initializing if we already did the work for the same plugin (even with diff names)
                    if callback_obj not in self._callback_plugins:
                        callback_obj.set_options()
                        self._callback_plugins.append(callback_obj)
                    else:
                        display.vv("Skipping callback '%s', already loaded as '%s'." % (callback_plugin, callback_name))
                else:
                    display.warning("Skipping callback '%s', as it does not create a valid plugin instance." % callback_name)
                    continue
            except Exception as e:
                display.warning("Skipping callback '%s', unable to load due to: %s" % (callback_name, to_native(e)))
                continue

        self._callbacks_loaded = True

    def run(self, play):
        """
        Iterates over the roles/tasks in a play, using the given (or default)
        strategy for queueing tasks. The default is the linear strategy, which
        operates like classic Ansible by keeping all hosts in lock-step with
        a given task (meaning no hosts move on to the next task until all hosts
        are done with the current task).
        """

        if not self._callbacks_loaded:
            self.load_callbacks()

        all_vars = self._variable_manager.get_vars(play=play)
        templar = TemplateEngine(loader=self._loader, variables=all_vars)

        new_play = play.copy()
        new_play.post_validate(templar)
        new_play.handlers = new_play.compile_roles_handlers() + new_play.handlers

        self.hostvars = HostVars(
            inventory=self._inventory,
            variable_manager=self._variable_manager,
            loader=self._loader,
        )

        play_context = PlayContext(new_play, self.passwords, self._connection_lockfile.fileno())
        if (self._stdout_callback and
                hasattr(self._stdout_callback, 'set_play_context')):
            self._stdout_callback.set_play_context(play_context)

        for callback_plugin in self._callback_plugins:
            if hasattr(callback_plugin, 'set_play_context'):
                callback_plugin.set_play_context(play_context)

        self.send_callback('v2_playbook_on_play_start', new_play)

        # build the iterator
        iterator = PlayIterator(
            inventory=self._inventory,
            play=new_play,
            play_context=play_context,
            variable_manager=self._variable_manager,
            all_vars=all_vars,
            start_at_done=self._start_at_done,
        )

        # adjust to # of workers to configured forks or size of batch, whatever is lower
        self._initialize_processes(min(self._forks, iterator.batch_size))

        # load the specified strategy (or the default linear one)
        strategy = strategy_loader.get(new_play.strategy, self)
        if strategy is None:
            raise AnsibleError("Invalid play strategy specified: %s" % new_play.strategy, obj=play._ds)

        # Because the TQM may survive multiple play runs, we start by marking
        # any hosts as failed in the iterator here which may have been marked
        # as failed in previous runs. Then we clear the internal list of failed
        # hosts so we know what failed this round.
        for host_name in self._failed_hosts.keys():
            host = self._inventory.get_host(host_name)
            iterator.mark_host_failed(host)
        for host_name in self._unreachable_hosts.keys():
            iterator._play._removed_hosts.append(host_name)

        self.clear_failed_hosts()

        # during initialization, the PlayContext will clear the start_at_task
        # field to signal that a matching task was found, so check that here
        # and remember it so we don't try to skip tasks on future plays
        if context.CLIARGS.get('start_at_task') is not None and play_context.start_at_task is None:
            self._start_at_done = True

        # and run the play using the strategy and cleanup on way out
        try:
            play_return = strategy.run(iterator, play_context)
        finally:
            strategy.cleanup()
            self._cleanup_processes()

        # now re-save the hosts that failed from the iterator to our internal list
        for host_name in iterator.get_failed_hosts():
            self._failed_hosts[host_name] = True

        if iterator.end_play:
            raise AnsibleEndPlay(play_return)

        return play_return

    def cleanup(self):
        display.debug("RUNNING CLEANUP")
        self.terminate()
        self._final_q.close()
        self._cleanup_processes()
        # We no longer flush on every write in ``Display.display``
        # just ensure we've flushed during cleanup
        sys.stdout.flush()
        sys.stderr.flush()

    def _cleanup_processes(self):
        if hasattr(self, '_workers'):
            for attempts_remaining in range(C.WORKER_SHUTDOWN_POLL_COUNT - 1, -1, -1):
                if not any(worker_prc and worker_prc.is_alive() for worker_prc in self._workers):
                    break

                if attempts_remaining:
                    time.sleep(C.WORKER_SHUTDOWN_POLL_DELAY)
                else:
                    display.warning('One or more worker processes are still running and will be terminated.')

            for worker_prc in self._workers:
                if worker_prc and worker_prc.is_alive():
                    try:
                        worker_prc.terminate()
                    except AttributeError:
                        pass

    def clear_failed_hosts(self) -> None:
        self._failed_hosts = dict()

    def get_inventory(self) -> InventoryData:
        return self._inventory

    def get_variable_manager(self) -> VariableManager:
        return self._variable_manager

    def get_loader(self) -> DataLoader:
        return self._loader

    def get_workers(self):
        return self._workers[:]

    def terminate(self) -> None:
        self._terminated = True

    def has_dead_workers(self) -> bool:

        # [<WorkerProcess(WorkerProcess-2, stopped[SIGKILL])>,
        # <WorkerProcess(WorkerProcess-2, stopped[SIGTERM])>

        defunct = False
        for x in self._workers:
            if getattr(x, 'exitcode', None):
                defunct = True
        return defunct

    @staticmethod
    def _first_arg_of_type(value_type: t.Type[_T], args: t.Sequence) -> _T | None:
        return next((arg for arg in args if isinstance(arg, value_type)), None)

    @lock_decorator(attr='_callback_lock')
    def send_callback(self, method_name, *args, **kwargs):
        # We always send events to stdout callback first, rest should follow config order
        for callback_plugin in [self._stdout_callback] + self._callback_plugins:
            # a plugin that set self.disabled to True will not be called
            # see osx_say.py example for such a plugin
            if callback_plugin.disabled:
                continue

            # a plugin can opt in to implicit tasks (such as meta). It does this
            # by declaring self.wants_implicit_tasks = True.
            if not callback_plugin.wants_implicit_tasks and (task_arg := self._first_arg_of_type(Task, args)) and task_arg.implicit:
                continue

            # try to find v2 method, fallback to v1 method, ignore callback if no method found
            methods = []

            for possible in [method_name, 'v2_on_any']:
                method = getattr(callback_plugin, possible, None)

                if method is None:
                    method = getattr(callback_plugin, possible.removeprefix('v2_'), None)

                    if method is not None:
                        display.deprecated(
                            msg='The v1 callback API is deprecated.',
                            version='2.23',
                            help_text='Use `v2_` prefixed callback methods instead.',
                        )

                if method is not None and not getattr(method, '_base_impl', False):  # don't bother dispatching to the base impls
                    if possible == 'v2_on_any':
                        display.deprecated(
                            msg='The `v2_on_any` callback method is deprecated.',
                            version='2.23',
                            help_text='Use event-specific callback methods instead.',
                        )

                    methods.append(method)

            for method in methods:
                # send clean copies
                new_args = []

                for arg in args:
                    # FIXME: add play/task cleaners
                    if isinstance(arg, _RawTaskResult):
                        copied_tr = arg.as_callback_task_result()
                        new_args.append(copied_tr)
                        # this state hack requires that no callback ever accepts > 1 TaskResult object
                        callback_plugin._current_task_result = copied_tr
                    else:
                        new_args.append(arg)

                with self._callback_dispatch_error_handler.handle(AnsibleCallbackError):
                    try:
                        method(*new_args, **kwargs)
                    except AssertionError:
                        # Using an `assert` in integration tests is useful.
                        # Production code should never use `assert` or raise `AssertionError`.
                        raise
                    except Exception as ex:
                        raise AnsibleCallbackError(f"Callback dispatch {method_name!r} failed for plugin {callback_plugin._load_name!r}.") from ex

            callback_plugin._current_task_result = None
