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

from six.moves import queue as Queue
import time

from ansible.errors import *
from ansible.executor.task_result import TaskResult
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.playbook.handler import Handler
from ansible.playbook.helpers import load_list_of_blocks
from ansible.playbook.role import ROLE_CACHE, hash_params
from ansible.plugins import filter_loader, lookup_loader, module_loader
from ansible.utils.debug import debug


__all__ = ['StrategyBase']

# FIXME: this should probably be in the plugins/__init__.py, with
#        a smarter mechanism to set all of the attributes based on
#        the loaders created there
class SharedPluginLoaderObj:
    '''
    A simple object to make pass the various plugin loaders to
    the forked processes over the queue easier
    '''
    def __init__(self):
        self.filter_loader = filter_loader
        self.lookup_loader = lookup_loader
        self.module_loader = module_loader

class StrategyBase:

    '''
    This is the base class for strategy plugins, which contains some common
    code useful to all strategies like running handlers, cleanup actions, etc.
    '''

    def __init__(self, tqm):
        self._tqm               = tqm
        self._inventory         = tqm.get_inventory()
        self._workers           = tqm.get_workers()
        self._notified_handlers = tqm.get_notified_handlers()
        self._variable_manager  = tqm.get_variable_manager()
        self._loader            = tqm.get_loader()
        self._final_q           = tqm._final_q

        # internal counters
        self._pending_results   = 0
        self._cur_worker        = 0

        # this dictionary is used to keep track of hosts that have
        # outstanding tasks still in queue
        self._blocked_hosts     = dict()

    def run(self, iterator, connection_info, result=True):
        # save the failed/unreachable hosts, as the run_handlers()
        # method will clear that information during its execution
        failed_hosts      = self._tqm._failed_hosts.keys()
        unreachable_hosts = self._tqm._unreachable_hosts.keys()

        debug("running handlers")
        result &= self.run_handlers(iterator, connection_info)

        # now update with the hosts (if any) that failed or were
        # unreachable during the handler execution phase
        failed_hosts      = set(failed_hosts).union(self._tqm._failed_hosts.keys())
        unreachable_hosts = set(unreachable_hosts).union(self._tqm._unreachable_hosts.keys())

        # send the stats callback
        self._tqm.send_callback('v2_playbook_on_stats', self._tqm._stats)

        if len(unreachable_hosts) > 0:
            return 3
        elif len(failed_hosts) > 0:
            return 2
        elif not result:
            return 1
        else:
            return 0

    def get_hosts_remaining(self, play):
        return [host for host in self._inventory.get_hosts(play.hosts) if host.name not in self._tqm._failed_hosts and host.name not in self._tqm._unreachable_hosts]

    def get_failed_hosts(self, play):
        return [host for host in self._inventory.get_hosts(play.hosts) if host.name in self._tqm._failed_hosts]

    def _queue_task(self, host, task, task_vars, connection_info):
        ''' handles queueing the task up to be sent to a worker '''

        debug("entering _queue_task() for %s/%s" % (host, task))

        # and then queue the new task
        debug("%s - putting task (%s) in queue" % (host, task))
        try:
            debug("worker is %d (out of %d available)" % (self._cur_worker+1, len(self._workers)))

            (worker_prc, main_q, rslt_q) = self._workers[self._cur_worker]
            self._cur_worker += 1
            if self._cur_worker >= len(self._workers):
                self._cur_worker = 0

            # create a dummy object with plugin loaders set as an easier
            # way to share them with the forked processes
            shared_loader_obj = SharedPluginLoaderObj()

            main_q.put((host, task, self._loader.get_basedir(), task_vars, connection_info, shared_loader_obj), block=False)
            self._pending_results += 1
        except (EOFError, IOError, AssertionError) as e:
            # most likely an abort
            debug("got an error while queuing: %s" % e)
            return
        debug("exiting _queue_task() for %s/%s" % (host, task))

    def _process_pending_results(self, iterator):
        '''
        Reads results off the final queue and takes appropriate action
        based on the result (executing callbacks, updating state, etc.).
        '''

        ret_results = []

        while not self._final_q.empty() and not self._tqm._terminated:
            try:
                result = self._final_q.get(block=False)
                debug("got result from result worker: %s" % (result,))

                # all host status messages contain 2 entries: (msg, task_result)
                if result[0] in ('host_task_ok', 'host_task_failed', 'host_task_skipped', 'host_unreachable'):
                    task_result = result[1]
                    host = task_result._host
                    task = task_result._task
                    if result[0] == 'host_task_failed' or task_result.is_failed():
                        if not task.ignore_errors:
                            debug("marking %s as failed" % host.name)
                            iterator.mark_host_failed(host)
                            self._tqm._failed_hosts[host.name] = True
                        self._tqm._stats.increment('failures', host.name)
                        self._tqm.send_callback('v2_runner_on_failed', task_result)
                    elif result[0] == 'host_unreachable':
                        self._tqm._unreachable_hosts[host.name] = True
                        self._tqm._stats.increment('dark', host.name)
                        self._tqm.send_callback('v2_runner_on_unreachable', task_result)
                    elif result[0] == 'host_task_skipped':
                        self._tqm._stats.increment('skipped', host.name)
                        self._tqm.send_callback('v2_runner_on_skipped', task_result)
                    elif result[0] == 'host_task_ok':
                        self._tqm._stats.increment('ok', host.name)
                        if 'changed' in task_result._result and task_result._result['changed']:
                            self._tqm._stats.increment('changed', host.name)
                        self._tqm.send_callback('v2_runner_on_ok', task_result)

                    self._pending_results -= 1
                    if host.name in self._blocked_hosts:
                        del self._blocked_hosts[host.name]

                    # If this is a role task, mark the parent role as being run (if
                    # the task was ok or failed, but not skipped or unreachable)
                    if task_result._task._role is not None and result[0] in ('host_task_ok', 'host_task_failed'):
                        # lookup the role in the ROLE_CACHE to make sure we're dealing
                        # with the correct object and mark it as executed
                        for (entry, role_obj) in ROLE_CACHE[task_result._task._role._role_name].iteritems():
                            hashed_entry = hash_params(task_result._task._role._role_params)
                            if entry == hashed_entry :
                                role_obj._had_task_run = True

                    ret_results.append(task_result)

                elif result[0] == 'add_host':
                    task_result = result[1]
                    new_host_info = task_result.get('add_host', dict())
                    
                    self._add_host(new_host_info)

                elif result[0] == 'add_group':
                    host        = result[1]
                    task_result = result[2]
                    group_name  = task_result.get('add_group')

                    self._add_group(host, group_name)

                elif result[0] == 'notify_handler':
                    host         = result[1]
                    handler_name = result[2]

                    if handler_name not in self._notified_handlers:
                        self._notified_handlers[handler_name] = []

                    if host not in self._notified_handlers[handler_name]:
                        self._notified_handlers[handler_name].append(host)

                elif result[0] == 'set_host_var':
                    host      = result[1]
                    var_name  = result[2]
                    var_value = result[3]
                    self._variable_manager.set_host_variable(host, var_name, var_value)

                elif result[0] == 'set_host_facts':
                    host  = result[1]
                    facts = result[2]
                    self._variable_manager.set_host_facts(host, facts)

                else:
                    raise AnsibleError("unknown result message received: %s" % result[0])
            except Queue.Empty:
                pass

        return ret_results

    def _wait_on_pending_results(self, iterator):
        '''
        Wait for the shared counter to drop to zero, using a short sleep
        between checks to ensure we don't spin lock
        '''

        ret_results = []

        while self._pending_results > 0 and not self._tqm._terminated:
            debug("waiting for pending results (%d left)" % self._pending_results)
            results = self._process_pending_results(iterator)
            ret_results.extend(results)
            time.sleep(0.01)

        return ret_results

    def _add_host(self, host_info):
        '''
        Helper function to add a new host to inventory based on a task result.
        '''

        host_name = host_info.get('host_name')

        # Check if host in cache, add if not
        if host_name in self._inventory._hosts_cache:
            new_host = self._inventory._hosts_cache[host_name]
        else:
            new_host = Host(host_name)
            self._inventory._hosts_cache[host_name] = new_host

            allgroup = self._inventory.get_group('all')
            allgroup.add_host(new_host)

        # Set/update the vars for this host
        # FIXME: probably should have a set vars method for the host?
        new_vars = host_info.get('host_vars', dict())
        new_host.vars.update(new_vars)

        new_groups = host_info.get('groups', [])
        for group_name in new_groups:
            if not self._inventory.get_group(group_name):
                new_group = Group(group_name)
                self._inventory.add_group(new_group)
                new_group.vars = self._inventory.get_group_variables(group_name)
            else:
                new_group = self._inventory.get_group(group_name)

            new_group.add_host(new_host)

            # add this host to the group cache
            if self._inventory._groups_list is not None:
                if group_name in self._inventory._groups_list:
                    if new_host.name not in self._inventory._groups_list[group_name]:
                        self._inventory._groups_list[group_name].append(new_host.name)

        # clear pattern caching completely since it's unpredictable what
        # patterns may have referenced the group
        # FIXME: is this still required?
        self._inventory.clear_pattern_cache()

    def _add_group(self, host, group_name):
        '''
        Helper function to add a group (if it does not exist), and to assign the
        specified host to that group.
        '''

        new_group = self._inventory.get_group(group_name)
        if not new_group:
            # create the new group and add it to inventory
            new_group = Group(group_name)
            self._inventory.add_group(new_group)

            # and add the group to the proper hierarchy
            allgroup = self._inventory.get_group('all')
            allgroup.add_child_group(new_group)

        # the host here is from the executor side, which means it was a
        # serialized/cloned copy and we'll need to look up the proper
        # host object from the master inventory
        actual_host = self._inventory.get_host(host.name)

        # and add the host to the group
        new_group.add_host(actual_host)

    def _load_included_file(self, included_file, iterator):
        '''
        Loads an included YAML file of tasks, applying the optional set of variables.
        '''

        try:
            data = self._loader.load_from_file(included_file._filename)
        except AnsibleError, e:
            for host in included_file._hosts:
                tr = TaskResult(host=host, task=included_file._task, return_data=dict(failed=True, reason=str(e)))
                iterator.mark_host_failed(host)
                self._tqm._failed_hosts[host.name] = True
                self._tqm._stats.increment('failures', host.name)
                self._tqm.send_callback('v2_runner_on_failed', tr)
            return []

        if not isinstance(data, list):
            raise AnsibleParserError("included task files must contain a list of tasks", obj=included_file._task._ds)

        is_handler = isinstance(included_file._task, Handler)
        block_list = load_list_of_blocks(
            data,
            play=included_file._task._block._play,
            parent_block=included_file._task._block,
            task_include=included_file._task,
            role=included_file._task._role,
            use_handlers=is_handler,
            loader=self._loader
        )

        # set the vars for this task from those specified as params to the include
        for b in block_list:
            b.vars = included_file._args.copy()

        return block_list

    def run_handlers(self, iterator, connection_info):
        '''
        Runs handlers on those hosts which have been notified.
        '''

        result = True

        # FIXME: getting the handlers from the iterators play should be
        #        a method on the iterator, which may also filter the list
        #        of handlers based on the notified list

        for handler_block in iterator._play.handlers:
            # FIXME: handlers need to support the rescue/always portions of blocks too,
            #        but this may take some work in the iterator and gets tricky when
            #        we consider the ability of meta tasks to flush handlers
            for handler in handler_block.block:
                handler_name = handler.get_name()
                if handler_name in self._notified_handlers and len(self._notified_handlers[handler_name]):
                    if not len(self.get_hosts_remaining(iterator._play)):
                        self._tqm.send_callback('v2_playbook_on_no_hosts_remaining')
                        result = False
                        break
                    self._tqm.send_callback('v2_playbook_on_handler_task_start', handler)
                    for host in self._notified_handlers[handler_name]:
                        if not handler.has_triggered(host):
                            task_vars = self._variable_manager.get_vars(loader=self._loader, play=iterator._play, host=host, task=handler)
                            self._queue_task(host, handler, task_vars, connection_info)
                            handler.flag_for_host(host)
                        self._process_pending_results(iterator)
                    self._wait_on_pending_results(iterator)
                    # wipe the notification list
                    self._notified_handlers[handler_name] = []
            debug("done running handlers, result is: %s" % result)
        return result
