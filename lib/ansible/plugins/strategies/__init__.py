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
from six import iteritems, text_type

import time

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.executor.task_result import TaskResult
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.playbook.handler import Handler
from ansible.playbook.helpers import load_list_of_blocks
from ansible.playbook.included_file import IncludedFile
from ansible.playbook.role import hash_params
from ansible.plugins import _basedirs, action_loader, connection_loader, filter_loader, lookup_loader, module_loader
from ansible.template import Templar

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

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
        self.basedirs = _basedirs[:]
        self.action_loader = action_loader
        self.connection_loader = connection_loader
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
        self._step              = getattr(tqm._options, 'step', False)
        self._diff              = getattr(tqm._options, 'diff', False)
        self._display           = display

        # internal counters
        self._pending_results   = 0
        self._cur_worker        = 0

        # this dictionary is used to keep track of hosts that have
        # outstanding tasks still in queue
        self._blocked_hosts     = dict()

    def run(self, iterator, play_context, result=True):
        # save the failed/unreachable hosts, as the run_handlers()
        # method will clear that information during its execution
        failed_hosts      = self._tqm._failed_hosts.keys()
        unreachable_hosts = self._tqm._unreachable_hosts.keys()

        self._display.debug("running handlers")
        result &= self.run_handlers(iterator, play_context)

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

    def add_tqm_variables(self, vars, play):
        '''
        Base class method to add extra variables/information to the list of task
        vars sent through the executor engine regarding the task queue manager state.
        '''

        new_vars = vars.copy()
        new_vars['ansible_current_hosts'] = self.get_hosts_remaining(play)
        new_vars['ansible_failed_hosts'] = self.get_failed_hosts(play)
        return new_vars

    def _queue_task(self, host, task, task_vars, play_context):
        ''' handles queueing the task up to be sent to a worker '''

        self._display.debug("entering _queue_task() for %s/%s" % (host, task))

        # and then queue the new task
        self._display.debug("%s - putting task (%s) in queue" % (host, task))
        try:
            self._display.debug("worker is %d (out of %d available)" % (self._cur_worker+1, len(self._workers)))

            (worker_prc, main_q, rslt_q) = self._workers[self._cur_worker]
            self._cur_worker += 1
            if self._cur_worker >= len(self._workers):
                self._cur_worker = 0

            # create a dummy object with plugin loaders set as an easier
            # way to share them with the forked processes
            shared_loader_obj = SharedPluginLoaderObj()

            main_q.put((host, task, self._loader.get_basedir(), task_vars, play_context, shared_loader_obj), block=False)
            self._pending_results += 1
        except (EOFError, IOError, AssertionError) as e:
            # most likely an abort
            self._display.debug("got an error while queuing: %s" % e)
            return
        self._display.debug("exiting _queue_task() for %s/%s" % (host, task))

    def _process_pending_results(self, iterator):
        '''
        Reads results off the final queue and takes appropriate action
        based on the result (executing callbacks, updating state, etc.).
        '''

        ret_results = []

        while not self._final_q.empty() and not self._tqm._terminated:
            try:
                result = self._final_q.get(block=False)
                self._display.debug("got result from result worker: %s" % ([text_type(x) for x in result],))

                # all host status messages contain 2 entries: (msg, task_result)
                if result[0] in ('host_task_ok', 'host_task_failed', 'host_task_skipped', 'host_unreachable'):
                    task_result = result[1]
                    host = task_result._host
                    task = task_result._task
                    if result[0] == 'host_task_failed' or task_result.is_failed():
                        if not task.ignore_errors:
                            self._display.debug("marking %s as failed" % host.name)
                            iterator.mark_host_failed(host)
                            self._tqm._failed_hosts[host.name] = True
                            self._tqm._stats.increment('failures', host.name)
                        else:
                            self._tqm._stats.increment('ok', host.name)
                        self._tqm.send_callback('v2_runner_on_failed', task_result, ignore_errors=task.ignore_errors)
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

                        if self._diff and 'diff' in task_result._result:
                            self._tqm.send_callback('v2_on_file_diff', task_result)

                    self._pending_results -= 1
                    if host.name in self._blocked_hosts:
                        del self._blocked_hosts[host.name]

                    # If this is a role task, mark the parent role as being run (if
                    # the task was ok or failed, but not skipped or unreachable)
                    if task_result._task._role is not None and result[0] in ('host_task_ok', 'host_task_failed'):
                        # lookup the role in the ROLE_CACHE to make sure we're dealing
                        # with the correct object and mark it as executed
                        for (entry, role_obj) in iteritems(iterator._play.ROLE_CACHE[task_result._task._role._role_name]):
                            if role_obj._uuid == task_result._task._role._uuid:
                                role_obj._had_task_run[host.name] = True

                    ret_results.append(task_result)

                elif result[0] == 'add_host':
                    task_result = result[1]
                    new_host_info = task_result.get('add_host', dict())

                    self._add_host(new_host_info)

                elif result[0] == 'add_group':
                    task        = result[1]
                    self._add_group(task, iterator)

                elif result[0] == 'notify_handler':
                    task_result  = result[1]
                    handler_name = result[2]

                    original_task = iterator.get_original_task(task_result._host, task_result._task)
                    if handler_name not in self._notified_handlers:
                        self._notified_handlers[handler_name] = []

                    if task_result._host not in self._notified_handlers[handler_name]:
                        self._notified_handlers[handler_name].append(task_result._host)

                elif result[0] == 'register_host_var':
                    # essentially the same as 'set_host_var' below, however we
                    # never follow the delegate_to value for registered vars
                    host      = result[1]
                    var_name  = result[2]
                    var_value = result[3]
                    self._variable_manager.set_host_variable(host, var_name, var_value)

                elif result[0] in ('set_host_var', 'set_host_facts'):
                    host = result[1]
                    task = result[2]
                    item = result[3]

                    if task.delegate_to is not None:
                        task_vars = self._variable_manager.get_vars(loader=self._loader, play=iterator._play, host=host, task=task)
                        task_vars = self.add_tqm_variables(task_vars, play=iterator._play)
                        if item is not None:
                            task_vars['item'] = item
                        templar = Templar(loader=self._loader, variables=task_vars)
                        host_name = templar.template(task.delegate_to)
                        target_host = self._inventory.get_host(host_name)
                        if target_host is None:
                            target_host = Host(name=host_name)
                    else:
                        target_host = host

                    if result[0] == 'set_host_var':
                        var_name  = result[4]
                        var_value = result[5]
                        self._variable_manager.set_host_variable(target_host, var_name, var_value)
                    elif result[0] == 'set_host_facts':
                        facts = result[4]
                        self._variable_manager.set_host_facts(target_host, facts)

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

        self._display.debug("waiting for pending results...")
        while self._pending_results > 0 and not self._tqm._terminated:
            results = self._process_pending_results(iterator)
            ret_results.extend(results)
            time.sleep(0.01)
        self._display.debug("no more pending results, returning what we have")

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
            new_host = Host(name=host_name)
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

    def _add_group(self, task, iterator):
        '''
        Helper function to add a group (if it does not exist), and to assign the
        specified host to that group.
        '''

        # the host here is from the executor side, which means it was a
        # serialized/cloned copy and we'll need to look up the proper
        # host object from the master inventory
        groups = {}
        changed = False

        for host in self._inventory.get_hosts():
            original_task = iterator.get_original_task(host, task)
            all_vars = self._variable_manager.get_vars(loader=self._loader, play=iterator._play, host=host, task=original_task)
            templar = Templar(loader=self._loader, variables=all_vars)
            group_name = templar.template(original_task.args.get('key'))
            if task.evaluate_conditional(templar=templar, all_vars=all_vars):
                if group_name not in groups:
                    groups[group_name] = []
                groups[group_name].append(host)

        for group_name, hosts in iteritems(groups):
            new_group = self._inventory.get_group(group_name)
            if not new_group:
                # create the new group and add it to inventory
                new_group = Group(name=group_name)
                self._inventory.add_group(new_group)

                # and add the group to the proper hierarchy
                allgroup = self._inventory.get_group('all')
                allgroup.add_child_group(new_group)
                changed = True
            for host in hosts:
                if group_name not in host.get_groups():
                    new_group.add_host(host)
                    changed = True

        return changed

    def _load_included_file(self, included_file, iterator, is_handler=False):
        '''
        Loads an included YAML file of tasks, applying the optional set of variables.
        '''

        try:
            data = self._loader.load_from_file(included_file._filename)
            if data is None:
                return []
        except AnsibleError as e:
            for host in included_file._hosts:
                tr = TaskResult(host=host, task=included_file._task, return_data=dict(failed=True, reason=str(e)))
                iterator.mark_host_failed(host)
                self._tqm._failed_hosts[host.name] = True
                self._tqm._stats.increment('failures', host.name)
                self._tqm.send_callback('v2_runner_on_failed', tr)
            return []

        if not isinstance(data, list):
            raise AnsibleParserError("included task files must contain a list of tasks", obj=included_file._task._ds)

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
            # first make a copy of the including task, so that each has a unique copy to modify
            # FIXME: not sure if this is the best way to fix this, as we might be losing
            #        information in the copy. Previously we assigned the include params to
            #        the block variables directly, which caused other problems, so we may
            #        need to figure out a third option if this also presents problems.
            b._task_include = b._task_include.copy(exclude_block=True)
            # then we create a temporary set of vars to ensure the variable reference is unique
            temp_vars = b._task_include.vars.copy()
            temp_vars.update(included_file._args.copy())
            b._task_include.vars = temp_vars

        return block_list

    def run_handlers(self, iterator, play_context):
        '''
        Runs handlers on those hosts which have been notified.
        '''

        result = True

        for handler_block in iterator._play.handlers:
            # FIXME: handlers need to support the rescue/always portions of blocks too,
            #        but this may take some work in the iterator and gets tricky when
            #        we consider the ability of meta tasks to flush handlers
            for handler in handler_block.block:
                handler_name = handler.get_name()
                if handler_name in self._notified_handlers and len(self._notified_handlers[handler_name]):
                    # FIXME: need to use iterator.get_failed_hosts() instead?
                    #if not len(self.get_hosts_remaining(iterator._play)):
                    #    self._tqm.send_callback('v2_playbook_on_no_hosts_remaining')
                    #    result = False
                    #    break
                    self._tqm.send_callback('v2_playbook_on_handler_task_start', handler)
                    host_results = []
                    for host in self._notified_handlers[handler_name]:
                        if not handler.has_triggered(host) and (host.name not in self._tqm._failed_hosts or play_context.force_handlers):
                            task_vars = self._variable_manager.get_vars(loader=self._loader, play=iterator._play, host=host, task=handler)
                            task_vars = self.add_tqm_variables(task_vars, play=iterator._play)
                            self._queue_task(host, handler, task_vars, play_context)
                            #handler.flag_for_host(host)
                        results = self._process_pending_results(iterator)
                        host_results.extend(results)
                    results = self._wait_on_pending_results(iterator)
                    host_results.extend(results)

                    # wipe the notification list
                    self._notified_handlers[handler_name] = []

                    try:
                        included_files = IncludedFile.process_include_results(
                            host_results,
                            self._tqm,
                            iterator=iterator,
                            loader=self._loader,
                            variable_manager=self._variable_manager
                        )
                    except AnsibleError as e:
                        return False

                    if len(included_files) > 0:
                        for included_file in included_files:
                            try:
                                new_blocks = self._load_included_file(included_file, iterator=iterator, is_handler=True)
                                # for every task in each block brought in by the include, add the list
                                # of hosts which included the file to the notified_handlers dict
                                for block in new_blocks:
                                    for task in block.block:
                                        if task.name in self._notified_handlers:
                                            for host in included_file._hosts:
                                                if host.name not in self._notified_handlers[task.name]:
                                                    self._notified_handlers[task.name].append(host)
                                        else:
                                            self._notified_handlers[task.name] = included_file._hosts[:]
                                    # and add the new blocks to the list of handler blocks
                                    handler_block.block.extend(block.block)
                                #iterator._play.handlers.extend(new_blocks)
                            except AnsibleError as e:
                                for host in included_file._hosts:
                                    iterator.mark_host_failed(host)
                                    self._tqm._failed_hosts[host.name] = True
                                self._display.warning(str(e))
                                continue
            self._display.debug("done running handlers, result is: %s" % result)
        return result

    def _take_step(self, task, host=None):

        ret=False
        if host:
            msg = u'Perform task: %s on %s (y/n/c): ' % (task, host)
        else:
            msg = u'Perform task: %s (y/n/c): ' % task
        resp = self._display.prompt(msg)

        if resp.lower() in ['y','yes']:
            self._display.debug("User ran task")
            ret = True
        elif resp.lower() in ['c', 'continue']:
            self._display.debug("User ran task and cancled step mode")
            self._step = False
            ret = True
        else:
            self._display.debug("User skipped task")

        self._display.banner(msg)

        return ret

    def _execute_meta(self, task, play_context, iterator):

        # meta tasks store their args in the _raw_params field of args,
        # since they do not use k=v pairs, so get that
        meta_action = task.args.get('_raw_params')

        if meta_action == 'noop':
            # FIXME: issue a callback for the noop here?
            pass
        elif meta_action == 'flush_handlers':
            self.run_handlers(iterator, play_context)
        elif meta_action == 'refresh_inventory':
            self._inventory.refresh_inventory()
        #elif meta_action == 'reset_connection':
        #    connection_info.connection.close()
        else:
            raise AnsibleError("invalid meta action requested: %s" % meta_action, obj=task._ds)
