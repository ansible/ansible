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

import Queue
import time

from ansible.errors import *

from ansible.inventory.host import Host
from ansible.inventory.group import Group

from ansible.playbook.helpers import compile_block_list
from ansible.playbook.role import ROLE_CACHE, hash_params
from ansible.plugins import module_loader
from ansible.utils.debug import debug


__all__ = ['StrategyBase']


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
        self._callback          = tqm.get_callback()
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
        # save the counts on failed/unreachable hosts, as the cleanup/handler
        # methods will clear that information during their runs
        num_failed      = len(self._tqm._failed_hosts)
        num_unreachable = len(self._tqm._unreachable_hosts)

        debug("running the cleanup portion of the play")
        result &= self.cleanup(iterator, connection_info)
        debug("running handlers")
        result &= self.run_handlers(iterator, connection_info)

        if not result:
            if num_unreachable > 0:
                return 3
            elif num_failed > 0:
                return 2
            else:
                return 1
        else:
            return 0

    def get_hosts_remaining(self, play):
        return [host for host in self._inventory.get_hosts(play.hosts) if host.name not in self._tqm._failed_hosts and host.get_name() not in self._tqm._unreachable_hosts]

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

            self._pending_results += 1
            main_q.put((host, task, self._loader.get_basedir(), task_vars, connection_info, module_loader), block=False)
        except (EOFError, IOError, AssertionError), e:
            # most likely an abort
            debug("got an error while queuing: %s" % e)
            return
        debug("exiting _queue_task() for %s/%s" % (host, task))

    def _process_pending_results(self):
        '''
        Reads results off the final queue and takes appropriate action
        based on the result (executing callbacks, updating state, etc.).
        '''

        while not self._final_q.empty() and not self._tqm._terminated:
            try:
                result = self._final_q.get(block=False)
                debug("got result from result worker: %s" % (result,))

                # all host status messages contain 2 entries: (msg, task_result)
                if result[0] in ('host_task_ok', 'host_task_failed', 'host_task_skipped', 'host_unreachable'):
                    task_result = result[1]
                    host = task_result._host
                    task = task_result._task
                    if result[0] == 'host_task_failed':
                        if not task.ignore_errors:
                            debug("marking %s as failed" % host.get_name())
                            self._tqm._failed_hosts[host.get_name()] = True
                        self._callback.runner_on_failed(task, task_result)
                    elif result[0] == 'host_unreachable':
                        self._tqm._unreachable_hosts[host.get_name()] = True
                        self._callback.runner_on_unreachable(task, task_result)
                    elif result[0] == 'host_task_skipped':
                        self._callback.runner_on_skipped(task, task_result)
                    elif result[0] == 'host_task_ok':
                        self._callback.runner_on_ok(task, task_result)

                    self._pending_results -= 1
                    if host.name in self._blocked_hosts:
                        del self._blocked_hosts[host.name]

                    # If this is a role task, mark the parent role as being run (if
                    # the task was ok or failed, but not skipped or unreachable)
                    if task_result._task._role is not None and result[0] in ('host_task_ok', 'host_task_failed'):
                        # lookup the role in the ROLE_CACHE to make sure we're dealing
                        # with the correct object and mark it as executed
                        for (entry, role_obj) in ROLE_CACHE[task_result._task._role._role_name].iteritems():
                            #hashed_entry = frozenset(task_result._task._role._role_params.iteritems())
                            hashed_entry = hash_params(task_result._task._role._role_params)
                            if entry == hashed_entry :
                                role_obj._had_task_run = True

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

    def _wait_on_pending_results(self):
        '''
        Wait for the shared counter to drop to zero, using a short sleep
        between checks to ensure we don't spin lock
        '''

        while self._pending_results > 0 and not self._tqm._terminated:
            debug("waiting for pending results (%d left)" % self._pending_results)
            self._process_pending_results()
            if self._tqm._terminated:
                break
            time.sleep(0.01)

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

    def cleanup(self, iterator, connection_info):
        '''
        Iterates through failed hosts and runs any outstanding rescue/always blocks
        and handlers which may still need to be run after a failure.
        '''

        debug("in cleanup")
        result = True

        debug("getting failed hosts")
        failed_hosts = self.get_failed_hosts(iterator._play)
        if len(failed_hosts) == 0:
            debug("there are no failed hosts")
            return result

        debug("marking hosts failed in the iterator")
        # mark the host as failed in the iterator so it will take
        # any required rescue paths which may be outstanding
        for host in failed_hosts:
            iterator.mark_host_failed(host)

        debug("clearing the failed hosts list")
        # clear the failed hosts dictionary now while also
        for entry in self._tqm._failed_hosts.keys():
            del self._tqm._failed_hosts[entry]

        work_to_do = True
        while work_to_do:
            work_to_do = False
            for host in failed_hosts:
                host_name = host.get_name()

                if host_name in self._tqm._failed_hosts:
                    iterator.mark_host_failed(host)
                    del self._tqm._failed_hosts[host_name]

                if host_name not in self._tqm._unreachable_hosts and iterator.get_next_task_for_host(host, peek=True):
                    work_to_do = True
                    # check to see if this host is blocked (still executing a previous task)
                    if not host_name in self._blocked_hosts:
                        # pop the task, mark the host blocked, and queue it
                        self._blocked_hosts[host_name] = True
                        task = iterator.get_next_task_for_host(host)
                        task_vars = self._variable_manager.get_vars(loader=self._loader, play=iterator._play, host=host, task=task)
                        self._callback.playbook_on_cleanup_task_start(task.get_name())
                        self._queue_task(host, task, task_vars, connection_info)

            self._process_pending_results()

        # no more work, wait until the queue is drained
        self._wait_on_pending_results()

        return result

    def run_handlers(self, iterator, connection_info):
        '''
        Runs handlers on those hosts which have been notified.
        '''

        result = True

        # FIXME: getting the handlers from the iterators play should be
        #        a method on the iterator, which may also filter the list
        #        of handlers based on the notified list
        handlers = compile_block_list(iterator._play.handlers)

        debug("handlers are: %s" % handlers)
        for handler in handlers:
            handler_name = handler.get_name()

            if handler_name in self._notified_handlers and len(self._notified_handlers[handler_name]):
                if not len(self.get_hosts_remaining()):
                    self._callback.playbook_on_no_hosts_remaining()
                    result = False
                    break

                self._callback.playbook_on_handler_task_start(handler_name)
                for host in self._notified_handlers[handler_name]:
                    if not handler.has_triggered(host):
                        task_vars = self._variable_manager.get_vars(loader=self._loader, play=iterator._play, host=host, task=handler)
                        self._queue_task(host, handler, task_vars, connection_info)
                        handler.flag_for_host(host)

                    self._process_pending_results()

                self._wait_on_pending_results()

                # wipe the notification list
                self._notified_handlers[handler_name] = []

        debug("done running handlers, result is: %s" % result)
        return result
