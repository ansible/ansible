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

from ansible.compat.six.moves import queue as Queue
from ansible.compat.six import iteritems, text_type, string_types

import json
import time
import zlib

from jinja2.exceptions import UndefinedError

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleParserError, AnsibleUndefinedVariable
from ansible.executor.play_iterator import PlayIterator
from ansible.executor.process.worker import WorkerProcess
from ansible.executor.task_result import TaskResult
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.playbook.helpers import load_list_of_blocks
from ansible.playbook.included_file import IncludedFile
from ansible.plugins import action_loader, connection_loader, filter_loader, lookup_loader, module_loader, test_loader
from ansible.template import Templar
from ansible.utils.unicode import to_unicode
from ansible.vars.unsafe_proxy import wrap_var
from ansible.vars import combine_vars

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

__all__ = ['StrategyBase']


# TODO: this should probably be in the plugins/__init__.py, with
#       a smarter mechanism to set all of the attributes based on
#       the loaders created there
class SharedPluginLoaderObj:
    '''
    A simple object to make pass the various plugin loaders to
    the forked processes over the queue easier
    '''
    def __init__(self):
        self.action_loader = action_loader
        self.connection_loader = connection_loader
        self.filter_loader = filter_loader
        self.test_loader   = test_loader
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
        # Backwards compat: self._display isn't really needed, just import the global display and use that.
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

        display.debug("running handlers")
        result &= self.run_handlers(iterator, play_context)

        # now update with the hosts (if any) that failed or were
        # unreachable during the handler execution phase
        failed_hosts      = set(failed_hosts).union(self._tqm._failed_hosts.keys())
        unreachable_hosts = set(unreachable_hosts).union(self._tqm._unreachable_hosts.keys())

        # return the appropriate code, depending on the status hosts after the run
        if len(unreachable_hosts) > 0:
            return 3
        elif len(failed_hosts) > 0:
            return 2
        elif not result:
            return 1
        else:
            return 0

    def get_hosts_remaining(self, play):
        return [host for host in self._inventory.get_hosts(play.hosts)
                if host.name not in self._tqm._failed_hosts and host.name not in self._tqm._unreachable_hosts]

    def get_failed_hosts(self, play):
        return [host for host in self._inventory.get_hosts(play.hosts) if host.name in self._tqm._failed_hosts]

    def add_tqm_variables(self, vars, play):
        '''
        Base class method to add extra variables/information to the list of task
        vars sent through the executor engine regarding the task queue manager state.
        '''
        vars['ansible_current_hosts'] = [h.name for h in self.get_hosts_remaining(play)]
        vars['ansible_failed_hosts'] = [h.name for h in self.get_failed_hosts(play)]

    def _queue_task(self, host, task, task_vars, play_context):
        ''' handles queueing the task up to be sent to a worker '''

        display.debug("entering _queue_task() for %s/%s" % (host, task))

        task_vars['hostvars'] = self._tqm.hostvars
        # and then queue the new task
        display.debug("%s - putting task (%s) in queue" % (host, task))
        try:
            display.debug("worker is %d (out of %d available)" % (self._cur_worker+1, len(self._workers)))

            # create a dummy object with plugin loaders set as an easier
            # way to share them with the forked processes
            shared_loader_obj = SharedPluginLoaderObj()

            queued = False
            while True:
                (worker_prc, rslt_q) = self._workers[self._cur_worker]
                if worker_prc is None or not worker_prc.is_alive():
                    worker_prc = WorkerProcess(rslt_q, task_vars, host, task, play_context, self._loader, self._variable_manager, shared_loader_obj)
                    self._workers[self._cur_worker][0] = worker_prc
                    worker_prc.start()
                    queued = True
                self._cur_worker += 1
                if self._cur_worker >= len(self._workers):
                    self._cur_worker = 0
                    time.sleep(0.0001)
                if queued:
                    break

            del task_vars
            self._pending_results += 1
        except (EOFError, IOError, AssertionError) as e:
            # most likely an abort
            display.debug("got an error while queuing: %s" % e)
            return
        display.debug("exiting _queue_task() for %s/%s" % (host, task))

    def _process_pending_results(self, iterator, one_pass=False):
        '''
        Reads results off the final queue and takes appropriate action
        based on the result (executing callbacks, updating state, etc.).
        '''

        ret_results = []

        while not self._final_q.empty() and not self._tqm._terminated:
            try:
                result = self._final_q.get()
                display.debug("got result from result worker: %s" % ([text_type(x) for x in result],))

                # helper method, used to find the original host from the one
                # returned in the result/message, which has been serialized and
                # thus had some information stripped from it to speed up the
                # serialization process
                def get_original_host(host):
                    if host.name in self._inventory._hosts_cache:
                       return self._inventory._hosts_cache[host.name]
                    else:
                       return self._inventory.get_host(host.name)

                # all host status messages contain 2 entries: (msg, task_result)
                if result[0] in ('host_task_ok', 'host_task_failed', 'host_task_skipped', 'host_unreachable'):
                    task_result = result[1]
                    host = get_original_host(task_result._host)
                    task = task_result._task
                    if result[0] == 'host_task_failed' or task_result.is_failed():
                        if not task.ignore_errors:
                            display.debug("marking %s as failed" % host.name)
                            if task.run_once:
                                # if we're using run_once, we have to fail every host here
                                [iterator.mark_host_failed(h) for h in self._inventory.get_hosts(iterator._play.hosts) if h.name not in self._tqm._unreachable_hosts]
                            else:
                                iterator.mark_host_failed(host)

                            # only add the host to the failed list officially if it has
                            # been failed by the iterator
                            if iterator.is_failed(host):
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
                        if task.action != 'include':
                            self._tqm._stats.increment('ok', host.name)
                            if 'changed' in task_result._result and task_result._result['changed']:
                                self._tqm._stats.increment('changed', host.name)
                            self._tqm.send_callback('v2_runner_on_ok', task_result)

                        if self._diff:
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
                    result_item = result[1]
                    new_host_info = result_item.get('add_host', dict())

                    self._add_host(new_host_info, iterator)

                elif result[0] == 'add_group':
                    host = get_original_host(result[1])
                    result_item = result[2]
                    self._add_group(host, result_item)

                elif result[0] == 'notify_handler':
                    task_result  = result[1]
                    handler_name = result[2]

                    original_host = get_original_host(task_result._host)
                    original_task = iterator.get_original_task(original_host, task_result._task)
                    if handler_name not in self._notified_handlers:
                        self._notified_handlers[handler_name] = []

                    if original_host not in self._notified_handlers[handler_name]:
                        self._notified_handlers[handler_name].append(original_host)
                        display.vv("NOTIFIED HANDLER %s" % (handler_name,))

                elif result[0] == 'register_host_var':
                    # essentially the same as 'set_host_var' below, however we
                    # never follow the delegate_to value for registered vars and
                    # the variable goes in the fact_cache
                    host      = get_original_host(result[1])
                    task      = result[2]
                    var_value = wrap_var(result[3])
                    var_name  = task.register

                    if task.run_once:
                        host_list = [host for host in self._inventory.get_hosts(iterator._play.hosts) if host.name not in self._tqm._unreachable_hosts]
                    else:
                        host_list = [host]

                    for target_host in host_list:
                        self._variable_manager.set_nonpersistent_facts(target_host, {var_name: var_value})

                elif result[0] in ('set_host_var', 'set_host_facts'):
                    host = get_original_host(result[1])
                    task = result[2]
                    item = result[3]

                    # find the host we're actually refering too here, which may
                    # be a host that is not really in inventory at all
                    if task.delegate_to is not None and task.delegate_facts:
                        task_vars = self._variable_manager.get_vars(loader=self._loader, play=iterator._play, host=host, task=task)
                        self.add_tqm_variables(task_vars, play=iterator._play)
                        if item is not None:
                            task_vars['item'] = item
                        templar = Templar(loader=self._loader, variables=task_vars)
                        host_name = templar.template(task.delegate_to)
                        actual_host = self._inventory.get_host(host_name)
                        if actual_host is None:
                            actual_host = Host(name=host_name)
                    else:
                        actual_host = host

                    if task.run_once:
                        host_list = [host for host in self._inventory.get_hosts(iterator._play.hosts) if host.name not in self._tqm._unreachable_hosts]
                    else:
                        host_list = [actual_host]

                    if result[0] == 'set_host_var':
                        var_name  = result[4]
                        var_value = result[5]
                        for target_host in host_list:
                            self._variable_manager.set_host_variable(target_host, var_name, var_value)
                    elif result[0] == 'set_host_facts':
                        facts = result[4]
                        for target_host in host_list:
                            if task.action == 'set_fact':
                                self._variable_manager.set_nonpersistent_facts(target_host, facts)
                            else:
                                self._variable_manager.set_host_facts(target_host, facts)
                elif result[0].startswith('v2_playbook_item') or result[0] == 'v2_playbook_retry':
                    self._tqm.send_callback(result[0], result[1])
                elif result[0] == 'v2_on_file_diff':
                    if self._diff:
                        self._tqm.send_callback('v2_on_file_diff', result[1])
                else:
                    raise AnsibleError("unknown result message received: %s" % result[0])

            except Queue.Empty:
                time.sleep(0.0001)

            if one_pass:
                break

        return ret_results

    def _wait_on_pending_results(self, iterator):
        '''
        Wait for the shared counter to drop to zero, using a short sleep
        between checks to ensure we don't spin lock
        '''

        ret_results = []

        display.debug("waiting for pending results...")
        while self._pending_results > 0 and not self._tqm._terminated:
            results = self._process_pending_results(iterator)
            ret_results.extend(results)
            time.sleep(0.0001)
        display.debug("no more pending results, returning what we have")

        return ret_results

    def _add_host(self, host_info, iterator):
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
        new_host.vars = combine_vars(new_host.vars, self._inventory.get_host_vars(new_host))
        new_host.vars = combine_vars(new_host.vars,  host_info.get('host_vars', dict()))

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
            if self._inventory.groups is not None:
                if group_name in self._inventory.groups:
                    if new_host not in self._inventory.get_group(group_name).hosts:
                        self._inventory.get_group(group_name).hosts.append(new_host.name)

        # clear pattern caching completely since it's unpredictable what
        # patterns may have referenced the group
        self._inventory.clear_pattern_cache()

        # also clear the hostvar cache entry for the given play, so that
        # the new hosts are available if hostvars are referenced
        self._variable_manager.invalidate_hostvars_cache(play=iterator._play)

    def _add_group(self, host, result_item):
        '''
        Helper function to add a group (if it does not exist), and to assign the
        specified host to that group.
        '''

        changed = False

        # the host here is from the executor side, which means it was a
        # serialized/cloned copy and we'll need to look up the proper
        # host object from the master inventory
        real_host = self._inventory.get_host(host.name)

        group_name = result_item.get('add_group')
        new_group = self._inventory.get_group(group_name)
        if not new_group:
            # create the new group and add it to inventory
            new_group = Group(name=group_name)
            self._inventory.add_group(new_group)
            new_group.vars = self._inventory.get_group_vars(new_group)

            # and add the group to the proper hierarchy
            allgroup = self._inventory.get_group('all')
            allgroup.add_child_group(new_group)
            changed = True

        if group_name not in host.get_groups():
            new_group.add_host(real_host)
            changed = True

        return changed

    def _load_included_file(self, included_file, iterator, is_handler=False):
        '''
        Loads an included YAML file of tasks, applying the optional set of variables.
        '''

        display.debug("loading included file: %s" % included_file._filename)
        try:
            data = self._loader.load_from_file(included_file._filename)
            if data is None:
                return []
            elif not isinstance(data, list):
                raise AnsibleError("included task files must contain a list of tasks")

            block_list = load_list_of_blocks(
                data,
                play=included_file._task._block._play,
                parent_block=None,
                task_include=included_file._task,
                role=included_file._task._role,
                use_handlers=is_handler,
                loader=self._loader
            )

            # since we skip incrementing the stats when the task result is
            # first processed, we do so now for each host in the list
            for host in included_file._hosts:
                self._tqm._stats.increment('ok', host.name)

        except AnsibleError as e:
            # mark all of the hosts including this file as failed, send callbacks,
            # and increment the stats for this host
            for host in included_file._hosts:
                tr = TaskResult(host=host, task=included_file._task, return_data=dict(failed=True, reason=to_unicode(e)))
                iterator.mark_host_failed(host)
                self._tqm._failed_hosts[host.name] = True
                self._tqm._stats.increment('failures', host.name)
                self._tqm.send_callback('v2_runner_on_failed', tr)
            return []

        # set the vars for this task from those specified as params to the include
        for b in block_list:
            # first make a copy of the including task, so that each has a unique copy to modify
            b._task_include = b._task_include.copy()
            # then we create a temporary set of vars to ensure the variable reference is unique
            temp_vars = b._task_include.vars.copy()
            temp_vars.update(included_file._args.copy())
            # pop tags out of the include args, if they were specified there, and assign
            # them to the include. If the include already had tags specified, we raise an
            # error so that users know not to specify them both ways
            tags = temp_vars.pop('tags', [])
            if isinstance(tags, string_types):
                tags = tags.split(',')
            if len(tags) > 0:
                if len(b._task_include.tags) > 0:
                    raise AnsibleParserError("Include tasks should not specify tags in more than one way (both via args and directly on the task). Mixing tag specify styles is prohibited for whole import hierarchy, not only for single import statement",
                            obj=included_file._task._ds)
                display.deprecated("You should not specify tags in the include parameters. All tags should be specified using the task-level option")
                b._task_include.tags = tags
            b._task_include.vars = temp_vars

        # finally, send the callback and return the list of blocks loaded
        self._tqm.send_callback('v2_playbook_on_include', included_file)
        display.debug("done processing included file")
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
                handler_vars = self._variable_manager.get_vars(loader=self._loader, play=iterator._play, task=handler)
                templar = Templar(loader=self._loader, variables=handler_vars)
                try:
                    # first we check with the full result of get_name(), which may
                    # include the role name (if the handler is from a role). If that
                    # is not found, we resort to the simple name field, which doesn't
                    # have anything extra added to it.
                    handler_name = templar.template(handler.name)
                    if handler_name not in self._notified_handlers:
                        handler_name = templar.template(handler.get_name())
                except (UndefinedError, AnsibleUndefinedVariable):
                    # We skip this handler due to the fact that it may be using
                    # a variable in the name that was conditionally included via
                    # set_fact or some other method, and we don't want to error
                    # out unnecessarily
                    continue

                if handler_name in self._notified_handlers and len(self._notified_handlers[handler_name]):
                    result = self._do_handler_run(handler, handler_name, iterator=iterator, play_context=play_context)
                    if not result:
                        break
        return result

    def _do_handler_run(self, handler, handler_name, iterator, play_context, notified_hosts=None):

        # FIXME: need to use iterator.get_failed_hosts() instead?
        #if not len(self.get_hosts_remaining(iterator._play)):
        #    self._tqm.send_callback('v2_playbook_on_no_hosts_remaining')
        #    result = False
        #    break
        saved_name = handler.name
        handler.name = handler_name
        self._tqm.send_callback('v2_playbook_on_handler_task_start', handler)
        handler.name = saved_name

        if notified_hosts is None:
            notified_hosts = self._notified_handlers[handler_name]

        run_once = False
        try:
            action = action_loader.get(handler.action, class_only=True)
            if handler.run_once or getattr(action, 'BYPASS_HOST_LOOP', False):
                run_once = True
        except KeyError:
            # we don't care here, because the action may simply not have a
            # corresponding action plugin
            pass

        host_results = []
        for host in notified_hosts:
            if not handler.has_triggered(host) and (host.name not in self._tqm._failed_hosts or play_context.force_handlers):
                task_vars = self._variable_manager.get_vars(loader=self._loader, play=iterator._play, host=host, task=handler)
                self.add_tqm_variables(task_vars, play=iterator._play)
                self._queue_task(host, handler, task_vars, play_context)
                if run_once:
                    break

        # collect the results from the handler run
        host_results = self._wait_on_pending_results(iterator)

        try:
            included_files = IncludedFile.process_include_results(
                host_results,
                self._tqm,
                iterator=iterator,
                inventory=self._inventory,
                loader=self._loader,
                variable_manager=self._variable_manager
            )
        except AnsibleError as e:
            return False

        result = True
        if len(included_files) > 0:
            for included_file in included_files:
                try:
                    new_blocks = self._load_included_file(included_file, iterator=iterator, is_handler=True)
                    # for every task in each block brought in by the include, add the list
                    # of hosts which included the file to the notified_handlers dict
                    for block in new_blocks:
                        iterator._play.handlers.append(block)
                        for task in block.block:
                            result = self._do_handler_run(
                                handler=task,
                                handler_name=None,
                                iterator=iterator,
                                play_context=play_context,
                                notified_hosts=included_file._hosts[:],
                            )
                            if not result:
                                break
                except AnsibleError as e:
                    for host in included_file._hosts:
                        iterator.mark_host_failed(host)
                        self._tqm._failed_hosts[host.name] = True
                    display.warning(str(e))
                    continue

        # wipe the notification list
        self._notified_handlers[handler_name] = []
        display.debug("done running handlers, result is: %s" % result)
        return result

    def _take_step(self, task, host=None):

        ret=False
        msg=u'Perform task: %s ' % task
        if host:
            msg += u'on %s ' % host
        msg += u'(N)o/(y)es/(c)ontinue: '
        resp = display.prompt(msg)

        if resp.lower() in ['y','yes']:
            display.debug("User ran task")
            ret = True
        elif resp.lower() in ['c', 'continue']:
            display.debug("User ran task and cancled step mode")
            self._step = False
            ret = True
        else:
            display.debug("User skipped task")

        display.banner(msg)

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
        elif meta_action == 'clear_host_errors':
            self._tqm._failed_hosts = dict()
            self._tqm._unreachable_hosts = dict()
            for host in iterator._host_states:
                iterator._host_states[host].fail_state = iterator.FAILED_NONE
        else:
            raise AnsibleError("invalid meta action requested: %s" % meta_action, obj=task._ds)
