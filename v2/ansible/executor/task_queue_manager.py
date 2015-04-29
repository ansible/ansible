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

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.executor.connection_info import ConnectionInformation
from ansible.executor.play_iterator import PlayIterator
from ansible.executor.process.worker import WorkerProcess
from ansible.executor.process.result import ResultProcess
from ansible.executor.stats import AggregateStats
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

    def __init__(self, inventory, variable_manager, loader, display, options, passwords, stdout_callback=None):

        self._inventory        = inventory
        self._variable_manager = variable_manager
        self._loader           = loader
        self._display          = display
        self._options          = options
        self._stats            = AggregateStats()
        self.passwords         = passwords

        # a special flag to help us exit cleanly
        self._terminated = False

        # this dictionary is used to keep track of notified handlers
        self._notified_handlers = dict()

        # dictionaries to keep track of failed/unreachable hosts
        self._failed_hosts      = dict()
        self._unreachable_hosts = dict()

        self._final_q = multiprocessing.Queue()

        # load callback plugins
        self._callback_plugins = self._load_callbacks(stdout_callback)

        # create the pool of worker threads, based on the number of forks specified
        try:
            fileno = sys.stdin.fileno()
        except ValueError:
            fileno = None

        self._workers = []
        for i in range(self._options.forks):
            main_q = multiprocessing.Queue()
            rslt_q = multiprocessing.Queue()

            prc = WorkerProcess(self, main_q, rslt_q, loader)
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
            for handler in handler_block.block:
                handler_list.append(handler)

        # then initalize it with the handler names from the handler list
        for handler in handler_list:
            self._notified_handlers[handler.get_name()] = []

    def _load_callbacks(self, stdout_callback):
        '''
        Loads all available callbacks, with the exception of those which
        utilize the CALLBACK_TYPE option. When CALLBACK_TYPE is set to 'stdout',
        only one such callback plugin will be loaded.
        '''

        loaded_plugins = []

        stdout_callback_loaded = False
        if stdout_callback is None:
            stdout_callback = C.DEFAULT_STDOUT_CALLBACK

        if stdout_callback not in callback_loader:
            raise AnsibleError("Invalid callback for stdout specified: %s" % stdout_callback)

        for callback_plugin in callback_loader.all(class_only=True):
            if hasattr(callback_plugin, 'CALLBACK_VERSION') and callback_plugin.CALLBACK_VERSION >= 2.0:
                # we only allow one callback of type 'stdout' to be loaded, so check
                # the name of the current plugin and type to see if we need to skip
                # loading this callback plugin
                callback_type = getattr(callback_plugin, 'CALLBACK_TYPE', None)
                (callback_name, _) = os.path.splitext(os.path.basename(callback_plugin._original_path))
                if callback_type == 'stdout':
                    if callback_name != stdout_callback or stdout_callback_loaded:
                        continue
                    stdout_callback_loaded = True

                loaded_plugins.append(callback_plugin(self._display))
            else:
                loaded_plugins.append(callback_plugin())

        return loaded_plugins

    def run(self, play):
        '''
        Iterates over the roles/tasks in a play, using the given (or default)
        strategy for queueing tasks. The default is the linear strategy, which
        operates like classic Ansible by keeping all hosts in lock-step with
        a given task (meaning no hosts move on to the next task until all hosts
        are done with the current task).
        '''

        all_vars = self._variable_manager.get_vars(loader=self._loader, play=play)

        new_play = play.copy()
        new_play.post_validate(all_vars, fail_on_undefined=False)

        connection_info = ConnectionInformation(new_play, self._options, self.passwords)
        for callback_plugin in self._callback_plugins:
            if hasattr(callback_plugin, 'set_connection_info'):
                callback_plugin.set_connection_info(connection_info)

        self.send_callback('v2_playbook_on_play_start', new_play)

        # initialize the shared dictionary containing the notified handlers
        self._initialize_notified_handlers(new_play.handlers)

        # load the specified strategy (or the default linear one)
        strategy = strategy_loader.get(new_play.strategy, self)
        if strategy is None:
            raise AnsibleError("Invalid play strategy specified: %s" % new_play.strategy, obj=play._ds)

        # build the iterator
        iterator = PlayIterator(inventory=self._inventory, play=new_play, connection_info=connection_info, all_vars=all_vars)

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

    def get_variable_manager(self):
        return self._variable_manager

    def get_loader(self):
        return self._loader

    def get_notified_handlers(self):
        return self._notified_handlers

    def get_workers(self):
        return self._workers[:]

    def terminate(self):
        self._terminated = True

    def send_callback(self, method_name, *args, **kwargs):
        for callback_plugin in self._callback_plugins:
            # a plugin that set self.disabled to True will not be called
            # see osx_say.py example for such a plugin
            if getattr(callback_plugin, 'disabled', False):
                continue
            methods = [
                getattr(callback_plugin, method_name, None),
                getattr(callback_plugin, 'on_any', None)
            ]
            for method in methods:
                if method is not None:
                    method(*args, **kwargs)

