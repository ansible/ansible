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
import tempfile
import threading
import time

from collections import namedtuple

from ansible import constants as C
from ansible import context
from ansible.errors import AnsibleError
from ansible.executor.play_iterator import PlayIterator
from ansible.executor.process.worker import WorkerProcess
from ansible.executor.process.result import ResultProcess
from ansible.executor.stats import AggregateStats
from ansible.executor.task_result import TaskResult
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_text, to_native
from ansible.module_utils.urls import ParseResultDottedDict as DottedDict
from ansible.playbook.base import post_validate
from ansible.playbook.block import Block
from ansible.playbook.play_context import PlayContext
from ansible.plugins import new_loader as plugin_loader
from ansible.plugins.new_loader import strategy_loader, module_loader
from ansible.template import Templar
from ansible.utils.helpers import pct_to_int
from ansible.utils.sentinel import Sentinel
from ansible.vars.hostvars import HostVars
from ansible.vars.reserved import warn_if_reserved
from ansible.utils.display import Display
from ansible.utils.multiprocessing import context as multiprocessing_context


__all__ = ['TaskQueueManager']

display = Display()

WorkerEntry = namedtuple('WorkerEntry', ['proc', 'queue', 'last_update'])


class TaskQueueManager:

    '''
    This class handles the multiprocessing requirements of Ansible by
    creating a pool of worker forks, a result handler fork, and a
    manager object with shared datastructures/queues for coordinating
    work between all processes.

    The queue manager is responsible for loading the play strategy plugin,
    which dispatches the Play's tasks to hosts.
    '''

    RUN_OK = 0
    RUN_ERROR = 1
    RUN_FAILED_HOSTS = 2
    RUN_UNREACHABLE_HOSTS = 4
    RUN_FAILED_BREAK_PLAY = 8
    RUN_UNKNOWN_ERROR = 255

    def __init__(self, inventory, variable_manager, loader, passwords, stdout_callback=None, run_additional_callbacks=True, run_tree=False, forks=None):

        self._inventory = inventory
        self._variable_manager = variable_manager
        self._loader = loader
        self._stats = AggregateStats()
        self.passwords = passwords
        self._stdout_callback = stdout_callback
        self._run_additional_callbacks = run_additional_callbacks
        self._run_tree = run_tree
        self._forks = forks or 5

        self._start_at_done = False

        self._hostvars = HostVars(
            inventory=self._inventory,
            variable_manager=self._variable_manager,
            loader=self._loader,
        )

        # make sure any module paths (if specified) are added to the module_loader
        if context.CLIARGS.get('module_path', False):
            for path in context.CLIARGS['module_path']:
                if path:
                    module_loader.add_directores(path)

        # a special flag to help us exit cleanly
        self._terminated = False

        # dictionaries to keep track of failed/unreachable hosts
        self._failed_hosts = dict()
        self._unreachable_hosts = dict()

        try:
            self._final_q = multiprocessing_context.Queue()
            self._results_q = multiprocessing_context.Queue()
        except OSError as e:
            raise AnsibleError("Unable to use multiprocessing, this is normally caused by lack of access to /dev/shm: %s" % to_native(e))

        # start the results process
        self._results_proc = ResultProcess(self._final_q, self._results_q, run_tree=self._run_tree)
        self._results_proc.start()

        # A temporary file (opened pre-fork) used by connection
        # plugins for inter-process locking.
        self._connection_lockfile = tempfile.TemporaryFile()

    def initialize_processes(self, num):
        # start the workers
        self._workers = []
        for i in range(num):
            in_q = multiprocessing_context.Queue()
            proc = WorkerProcess(
                in_q,
                self._final_q,
                self._hostvars,
                self._loader,
            )
            self._workers.append(WorkerEntry(proc, in_q, 0))
            proc.start()

    # for compatibility, in case someone was using this directly
    _initialize_processes = initialize_processes

    def run(self, play, play_vars):
        '''
        Iterates over the roles/tasks in a play, using the given (or default)
        strategy for queueing tasks. The default is the linear strategy, which
        operates like classic Ansible by keeping all hosts in lock-step with
        a given task (meaning no hosts move on to the next task until all hosts
        are done with the current task).
        '''

        new_play = play.copy()
        new_play.handlers = new_play.compile_roles_handlers() + new_play.handlers

        play_context = PlayContext(new_play, self.passwords, self._connection_lockfile.fileno())

        # FIXME: sending callbacks directly seems to have a problem
        serialized_play = DottedDict(new_play.dump_attrs())
        serialized_play.pop('tasks', None)
        serialized_play.pop('handlers', None)
        self.send_callback('v2_playbook_on_play_start', serialized_play)

        # build the iterator
        iterator = PlayIterator(
            inventory=self._inventory,
            play=new_play,
            play_context=play_context,
            variable_manager=self._variable_manager,
            all_vars=play_vars,
            start_at_done=self._start_at_done,
        )

        # load the specified strategy (or the default linear one)
        strategy = strategy_loader.get(new_play.strategy)(self)
        if strategy is None:
            raise AnsibleError("Invalid play strategy specified: %s" % new_play.strategy, obj=play._ds)

        # Because the TQM may survive multiple play runs, we start by marking
        # any hosts as failed in the iterator here which may have been marked
        # as failed in previous runs. Then we clear the internal list of failed
        # hosts so we know what failed this round.
        for host_name in self._failed_hosts.keys():
            host = self._inventory.get_host(host_name)
            iterator.mark_host_failed(host)

        self.clear_failed_hosts()

        # during initialization, the PlayContext will clear the start_at_task
        # field to signal that a matching task was found, so check that here
        # and remember it so we don't try to skip tasks on future plays
        if context.CLIARGS.get('start_at_task') is not None and play_context.start_at_task is None:
            self._start_at_done = True

        # and run the play using the strategy and cleanup on way out
        play_return = strategy.run(iterator, play_context)

        # now re-save the hosts that failed from the iterator to our internal list
        for host_name in iterator.get_failed_hosts():
            self._failed_hosts[host_name] = True

        strategy.cleanup()
        return play_return

    def send_callback(self, callback_name, *args, **kwargs):
        self._final_q.put((callback_name, ) + tuple(args), block=True)

    def cleanup(self):
        display.debug("RUNNING CLEANUP")
        self._cleanup_processes()
        display.debug("DONE CLEANING UP TQM")

    def _cleanup_processes(self):
        if hasattr(self, '_workers'):
            for w_entry in self._workers:
                w_entry.queue.put(Sentinel(), block=True)
                w_entry.proc.join()
                w_entry.queue.close()

    def clear_failed_hosts(self):
        self._failed_hosts = dict()

    def get_inventory(self):
        return self._inventory

    def get_variable_manager(self):
        return self._variable_manager

    def get_loader(self):
        return self._loader

    def get_workers(self):
        return self._workers[:]

    def terminate(self):
        self._terminated = True
        self._final_q.put(Sentinel(), block=True)
        self._results_proc.join()
        self._final_q.close()
        self._results_q.close()

    def has_dead_workers(self):

        # [<WorkerProcess(WorkerProcess-2, stopped[SIGKILL])>,
        # <WorkerProcess(WorkerProcess-2, stopped[SIGTERM])>

        defunct = False
        for w_entry in self._workers:
            try:
                defunct = defunct or w_entry.proc.exitcode
                if defunct:
                    break
            except AttributeError:
                pass
        return defunct
