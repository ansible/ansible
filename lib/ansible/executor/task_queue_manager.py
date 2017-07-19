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
import tempfile

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.executor.play_iterator import PlayIterator
from ansible.executor.stats import AggregateStats
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_text
from ansible.playbook.block import Block
from ansible.playbook.play_context import PlayContext
from ansible.plugins import callback_loader, strategy_loader, module_loader
from ansible.plugins.callback import CallbackBase
from ansible.template import Templar
from ansible.utils.helpers import pct_to_int
from ansible.vars.hostvars import HostVars
from ansible.vars.reserved import warn_if_reserved

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


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

    RUN_OK = 0
    RUN_ERROR = 1
    RUN_FAILED_HOSTS = 2
    RUN_UNREACHABLE_HOSTS = 4
    RUN_FAILED_BREAK_PLAY = 8
    RUN_UNKNOWN_ERROR = 255

    def __init__(self, inventory, variable_manager, loader, options, passwords, stdout_callback=None, run_additional_callbacks=True, run_tree=False):

        self._inventory = inventory
        self._variable_manager = variable_manager
        self._loader = loader
        self._options = options
        self._stats = AggregateStats()
        self.passwords = passwords
        self._stdout_callback = stdout_callback
        self._run_additional_callbacks = run_additional_callbacks
        self._run_tree = run_tree

        self._callbacks_loaded = False
        self._callback_plugins = []
        self._start_at_done = False

        # make sure any module paths (if specified) are added to the module_loader
        if isinstance(options.module_path, list):
            for path in options.module_path:
                if path is not None:
                    module_loader.add_directory(path)

        # a special flag to help us exit cleanly
        self._terminated = False

        # this dictionary is used to keep track of notified handlers
        self._notified_handlers = dict()
        self._listening_handlers = dict()

        # dictionaries to keep track of failed/unreachable hosts
        self._failed_hosts = dict()
        self._unreachable_hosts = dict()

        self._final_q = multiprocessing.Queue()

        # A temporary file (opened pre-fork) used by connection
        # plugins for inter-process locking.
        self._connection_lockfile = tempfile.TemporaryFile()

    def _initialize_processes(self, num):
        self._workers = []

        for i in range(num):
            rslt_q = multiprocessing.Queue()
            self._workers.append([None, rslt_q])

    def _initialize_notified_handlers(self, play):
        '''
        Clears and initializes the shared notified handlers dict with entries
        for each handler in the play, which is an empty array that will contain
        inventory hostnames for those hosts triggering the handler.
        '''

        # Zero the dictionary first by removing any entries there.
        # Proxied dicts don't support iteritems, so we have to use keys()
        self._notified_handlers.clear()
        self._listening_handlers.clear()

        def _process_block(b):
            temp_list = []
            for t in b.block:
                if isinstance(t, Block):
                    temp_list.extend(_process_block(t))
                else:
                    temp_list.append(t)
            return temp_list

        handler_list = []
        for handler_block in play.handlers:
            handler_list.extend(_process_block(handler_block))
        # then initialize it with the given handler list
        self.update_handler_list(handler_list)

    def update_handler_list(self, handler_list):
        for handler in handler_list:
            if handler._uuid not in self._notified_handlers:
                display.debug("Adding handler %s to notified list" % handler.name)
                self._notified_handlers[handler._uuid] = []
            if handler.listen:
                listeners = handler.listen
                if not isinstance(listeners, list):
                    listeners = [listeners]
                for listener in listeners:
                    if listener not in self._listening_handlers:
                        self._listening_handlers[listener] = []
                    display.debug("Adding handler %s to listening list" % handler.name)
                    self._listening_handlers[listener].append(handler._uuid)

    def load_callbacks(self):
        '''
        Loads all available callbacks, with the exception of those which
        utilize the CALLBACK_TYPE option. When CALLBACK_TYPE is set to 'stdout',
        only one such callback plugin will be loaded.
        '''

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
                stdout_callback_loaded = True
        else:
            raise AnsibleError("callback must be an instance of CallbackBase or the name of a callback plugin")

        for callback_plugin in callback_loader.all(class_only=True):
            if hasattr(callback_plugin, 'CALLBACK_VERSION') and callback_plugin.CALLBACK_VERSION >= 2.0:
                # we only allow one callback of type 'stdout' to be loaded, so check
                # the name of the current plugin and type to see if we need to skip
                # loading this callback plugin
                callback_type = getattr(callback_plugin, 'CALLBACK_TYPE', None)
                callback_needs_whitelist = getattr(callback_plugin, 'CALLBACK_NEEDS_WHITELIST', False)
                (callback_name, _) = os.path.splitext(os.path.basename(callback_plugin._original_path))
                if callback_type == 'stdout':
                    if callback_name != self._stdout_callback or stdout_callback_loaded:
                        continue
                    stdout_callback_loaded = True
                elif callback_name == 'tree' and self._run_tree:
                    pass
                elif not self._run_additional_callbacks or (callback_needs_whitelist and (
                        C.DEFAULT_CALLBACK_WHITELIST is None or callback_name not in C.DEFAULT_CALLBACK_WHITELIST)):
                    continue

            self._callback_plugins.append(callback_plugin())

        self._callbacks_loaded = True

    def run(self, play):
        '''
        Iterates over the roles/tasks in a play, using the given (or default)
        strategy for queueing tasks. The default is the linear strategy, which
        operates like classic Ansible by keeping all hosts in lock-step with
        a given task (meaning no hosts move on to the next task until all hosts
        are done with the current task).
        '''

        if not self._callbacks_loaded:
            self.load_callbacks()

        all_vars = self._variable_manager.get_vars(play=play)
        warn_if_reserved(all_vars)
        templar = Templar(loader=self._loader, variables=all_vars)

        new_play = play.copy()
        new_play.post_validate(templar)
        new_play.handlers = new_play.compile_roles_handlers() + new_play.handlers

        self.hostvars = HostVars(
            inventory=self._inventory,
            variable_manager=self._variable_manager,
            loader=self._loader,
        )

        # Fork # of forks, # of hosts or serial, whichever is lowest
        num_hosts = len(self._inventory.get_hosts(new_play.hosts, ignore_restrictions=True))

        max_serial = 0
        if new_play.serial:
            # the play has not been post_validated here, so we may need
            # to convert the scalar value to a list at this point
            serial_items = new_play.serial
            if not isinstance(serial_items, list):
                serial_items = [serial_items]
            max_serial = max([pct_to_int(x, num_hosts) for x in serial_items])

        contenders = [self._options.forks, max_serial, num_hosts]
        contenders = [v for v in contenders if v is not None and v > 0]
        self._initialize_processes(min(contenders))

        play_context = PlayContext(new_play, self._options, self.passwords, self._connection_lockfile.fileno())
        for callback_plugin in self._callback_plugins:
            if hasattr(callback_plugin, 'set_play_context'):
                callback_plugin.set_play_context(play_context)

        self.send_callback('v2_playbook_on_play_start', new_play)

        # initialize the shared dictionary containing the notified handlers
        self._initialize_notified_handlers(new_play)

        # load the specified strategy (or the default linear one)
        strategy = strategy_loader.get(new_play.strategy, self)
        if strategy is None:
            raise AnsibleError("Invalid play strategy specified: %s" % new_play.strategy, obj=play._ds)

        # build the iterator
        iterator = PlayIterator(
            inventory=self._inventory,
            play=new_play,
            play_context=play_context,
            variable_manager=self._variable_manager,
            all_vars=all_vars,
            start_at_done=self._start_at_done,
        )

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
        if getattr(self._options, 'start_at_task', None) is not None and play_context.start_at_task is None:
            self._start_at_done = True

        # and run the play using the strategy and cleanup on way out
        play_return = strategy.run(iterator, play_context)

        # now re-save the hosts that failed from the iterator to our internal list
        for host_name in iterator.get_failed_hosts():
            self._failed_hosts[host_name] = True

        strategy.cleanup()
        self._cleanup_processes()
        return play_return

    def cleanup(self):
        display.debug("RUNNING CLEANUP")
        self.terminate()
        self._final_q.close()
        self._cleanup_processes()

    def _cleanup_processes(self):
        if hasattr(self, '_workers'):
            for (worker_prc, rslt_q) in self._workers:
                rslt_q.close()
                if worker_prc and worker_prc.is_alive():
                    try:
                        worker_prc.terminate()
                    except AttributeError:
                        pass

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

    def has_dead_workers(self):

        # [<WorkerProcess(WorkerProcess-2, stopped[SIGKILL])>,
        # <WorkerProcess(WorkerProcess-2, stopped[SIGTERM])>

        defunct = False
        for (idx, x) in enumerate(self._workers):
            if hasattr(x[0], 'exitcode'):
                if x[0].exitcode in [-9, -11, -15]:
                    defunct = True
        return defunct

    def send_callback(self, method_name, *args, **kwargs):
        for callback_plugin in [self._stdout_callback] + self._callback_plugins:
            # a plugin that set self.disabled to True will not be called
            # see osx_say.py example for such a plugin
            if getattr(callback_plugin, 'disabled', False):
                continue

            # try to find v2 method, fallback to v1 method, ignore callback if no method found
            methods = []
            for possible in [method_name, 'v2_on_any']:
                gotit = getattr(callback_plugin, possible, None)
                if gotit is None:
                    gotit = getattr(callback_plugin, possible.replace('v2_', ''), None)
                if gotit is not None:
                    methods.append(gotit)

            for method in methods:
                try:
                    method(*args, **kwargs)
                except Exception as e:
                    # TODO: add config toggle to make this fatal or not?
                    display.warning(u"Failure using method (%s) in callback plugin (%s): %s" % (to_text(method_name), to_text(callback_plugin), to_text(e)))
                    from traceback import format_tb
                    from sys import exc_info
                    display.debug('Callback Exception: \n' + ' '.join(format_tb(exc_info()[2])))
