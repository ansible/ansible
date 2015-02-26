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

import multiprocessing
import os
import socket
import sys

from ansible.errors import AnsibleError
from ansible.executor.connection_info import ConnectionInformation
from ansible.executor.play_iterator import PlayIterator
from ansible.executor.process.worker import WorkerProcess
from ansible.executor.process.result import ResultProcess
from ansible.plugins import callback_loader, strategy_loader

from ansible.utils.debug import debug

__all__ = ['TaskQueueManager']

class TaskQueueManager:

    '''
    This class handles the multiprocessing requirements of Ansible by
    creating a pool of worker forks, a result handler fork, and a
    manager object with shared datastructures/queues for coordinating
    work between all processes.

    The queue manager is responsible for loading the play strategy plugin,
    which dispatches the Play's tasks to hosts.
    '''

    def __init__(self, inventory, callback, variable_manager, loader, options):

        self._inventory        = inventory
        self._variable_manager = variable_manager
        self._loader           = loader
        self._options          = options

        # a special flag to help us exit cleanly
        self._terminated = False

        # this dictionary is used to keep track of notified handlers
        self._notified_handlers = dict()

        # dictionaries to keep track of failed/unreachable hosts
        self._failed_hosts      = dict()
        self._unreachable_hosts = dict()

        self._final_q = multiprocessing.Queue()

        # FIXME: hard-coded the default callback plugin here, which
        #        should be configurable.
        self._callback = callback_loader.get(callback)

        # create the pool of worker threads, based on the number of forks specified
        try:
            fileno = sys.stdin.fileno()
        except ValueError:
            fileno = None

        self._workers = []
        for i in range(self._options.forks):
            # duplicate stdin, if possible
            new_stdin = None
            if fileno is not None:
                try:
                    new_stdin = os.fdopen(os.dup(fileno))
                except OSError, e:
                    # couldn't dupe stdin, most likely because it's
                    # not a valid file descriptor, so we just rely on
                    # using the one that was passed in
                    pass

            main_q = multiprocessing.Queue()
            rslt_q = multiprocessing.Queue()

            prc = WorkerProcess(self, main_q, rslt_q, loader, new_stdin)
            prc.start()

            self._workers.append((prc, main_q, rslt_q))

        self._result_prc = ResultProcess(self._final_q, self._workers)
        self._result_prc.start()

    def _initialize_notified_handlers(self, handlers):
        '''
        Clears and initializes the shared notified handlers dict with entries
        for each handler in the play, which is an empty array that will contain
        inventory hostnames for those hosts triggering the handler.
        '''

        # Zero the dictionary first by removing any entries there.
        # Proxied dicts don't support iteritems, so we have to use keys()
        for key in self._notified_handlers.keys():
            del self._notified_handlers[key]

        # FIXME: there is a block compile helper for this...
        handler_list = []
        for handler_block in handlers:
            handler_list.extend(handler_block.compile())

        # then initalize it with the handler names from the handler list
        for handler in handler_list:
            self._notified_handlers[handler.get_name()] = []

    def run(self, play):
        '''
        Iterates over the roles/tasks in a play, using the given (or default)
        strategy for queueing tasks. The default is the linear strategy, which
        operates like classic Ansible by keeping all hosts in lock-step with
        a given task (meaning no hosts move on to the next task until all hosts
        are done with the current task).
        '''

        connection_info = ConnectionInformation(play, self._options)
        self._callback.set_connection_info(connection_info)

        # run final validation on the play now, to make sure fields are templated
        # FIXME: is this even required? Everything is validated and merged at the
        #        task level, so else in the play needs to be templated
        #all_vars = self._vmw.get_vars(loader=self._dlw, play=play)
        #all_vars = self._vmw.get_vars(loader=self._loader, play=play)
        #play.post_validate(all_vars=all_vars)

        self._callback.playbook_on_play_start(play.name)

        # initialize the shared dictionary containing the notified handlers
        self._initialize_notified_handlers(play.handlers)

        # load the specified strategy (or the default linear one)
        strategy = strategy_loader.get(play.strategy, self)
        if strategy is None:
            raise AnsibleError("Invalid play strategy specified: %s" % play.strategy, obj=play._ds)

        # build the iterator
        iterator = PlayIterator(inventory=self._inventory, play=play)

        # and run the play using the strategy
        return strategy.run(iterator, connection_info)

    def cleanup(self):
        debug("RUNNING CLEANUP")

        self.terminate()

        self._final_q.close()
        self._result_prc.terminate()

        for (worker_prc, main_q, rslt_q) in self._workers:
            rslt_q.close()
            main_q.close()
            worker_prc.terminate()

    def get_inventory(self):
        return self._inventory

    def get_callback(self):
        return self._callback

    def get_variable_manager(self):
        return self._variable_manager

    def get_loader(self):
        return self._loader

    def get_server_pipe(self):
        return self._server_pipe

    def get_client_pipe(self):
        return self._client_pipe

    def get_pending_results(self):
        return self._pending_results

    def get_allow_processing(self):
        return self._allow_processing

    def get_notified_handlers(self):
        return self._notified_handlers

    def get_workers(self):
        return self._workers[:]

    def terminate(self):
        self._terminated = True
