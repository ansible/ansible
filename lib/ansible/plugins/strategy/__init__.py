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

import cmd
import functools
import os
import pprint
import queue
import sys
import threading
import time
import typing as t
import collections.abc as _c

from collections import deque


from ansible import constants as C
from ansible import context
from ansible.errors import AnsibleError, AnsibleFileNotFound, AnsibleParserError, AnsibleTemplateError
from ansible.executor.play_iterator import IteratingStates, PlayIterator
from ansible.executor.process.worker import WorkerProcess
from ansible.executor.task_result import _RawTaskResult, _WireTaskResult
from ansible.executor.task_queue_manager import CallbackSend, DisplaySend, PromptSend, TaskQueueManager
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.playbook.handler import Handler
from ansible.playbook.helpers import load_list_of_blocks
from ansible.playbook.included_file import IncludedFile
from ansible.playbook.task import Task
from ansible.playbook.task_include import TaskInclude
from ansible.plugins import loader as plugin_loader
from ansible._internal._templating._engine import TemplateEngine
from ansible.utils.display import Display
from ansible.utils.fqcn import add_internal_fqcns
from ansible.utils.sentinel import Sentinel
from ansible.utils.vars import combine_vars
from ansible.vars.clean import strip_internal_keys, module_response_deepcopy

if t.TYPE_CHECKING:
    from ansible.playbook.role_include import IncludeRole

display = Display()

__all__ = ['StrategyBase']

# This list can be an exact match, or start of string bound
# does not accept regex
ALWAYS_DELEGATE_FACT_PREFIXES = frozenset((
    'discovered_interpreter_',
))


class StrategySentinel:
    pass


_sentinel = StrategySentinel()

if t.TYPE_CHECKING:
    from ansible.inventory.host import Host


def _get_item_vars(result, task):
    item_vars = {}
    if task.loop or task.loop_with:
        loop_var = result.get('ansible_loop_var', 'item')
        index_var = result.get('ansible_index_var')
        if loop_var in result:
            item_vars[loop_var] = result[loop_var]
        if index_var and index_var in result:
            item_vars[index_var] = result[index_var]
        if '_ansible_item_label' in result:
            item_vars['_ansible_item_label'] = result['_ansible_item_label']
        if 'ansible_loop' in result:
            item_vars['ansible_loop'] = result['ansible_loop']
    return item_vars


def results_thread_main(strategy: StrategyBase) -> None:
    value: object

    while True:
        try:
            result = strategy._final_q.get()
            if isinstance(result, StrategySentinel):
                break
            elif isinstance(result, DisplaySend):
                dmethod = getattr(display, result.method)
                dmethod(*result.args, **result.kwargs)
            elif isinstance(result, CallbackSend):
                task_result = strategy._convert_wire_task_result_to_raw(result.wire_task_result)
                strategy._tqm.send_callback(result.method_name, task_result)
            elif isinstance(result, _WireTaskResult):
                result = strategy._convert_wire_task_result_to_raw(result)
                with strategy._results_lock:
                    strategy._results.append(result)
            elif isinstance(result, PromptSend):
                try:
                    value = display.prompt_until(
                        result.prompt,
                        private=result.private,
                        seconds=result.seconds,
                        complete_input=result.complete_input,
                        interrupt_input=result.interrupt_input,
                    )
                except AnsibleError as e:
                    value = e
                except BaseException as e:
                    # relay unexpected errors so bugs in display are reported and don't cause workers to hang
                    try:
                        raise AnsibleError(f"{e}") from e
                    except AnsibleError as e:
                        value = e
                strategy._workers[result.worker_id].worker_queue.put(value)
            else:
                display.warning('Received an invalid object (%s) in the result queue: %r' % (type(result), result))
        except (OSError, EOFError):
            break
        except queue.Empty:
            pass


def debug_closure(func):
    """Closure to wrap ``StrategyBase._process_pending_results`` and invoke the task debugger"""
    @functools.wraps(func)
    def inner(self, iterator: PlayIterator, one_pass: bool = False, max_passes: int | None = None) -> list[_RawTaskResult]:
        status_to_stats_map = (
            ('is_failed', 'failures'),
            ('is_unreachable', 'dark'),
            ('is_changed', 'changed'),
            ('is_skipped', 'skipped'),
        )

        # We don't know the host yet, copy the previous states, for lookup after we process new results
        prev_host_states = iterator.host_states.copy()

        results: list[_RawTaskResult] = func(self, iterator, one_pass=one_pass, max_passes=max_passes)
        _processed_results: list[_RawTaskResult] = []

        for result in results:
            task = result.task
            host = result.host
            _queued_task_args = self._queued_task_cache.pop((host.name, task._uuid), None)
            task_vars = _queued_task_args['task_vars']
            play_context = _queued_task_args['play_context']
            # Try to grab the previous host state, if it doesn't exist use get_host_state to generate an empty state
            try:
                prev_host_state = prev_host_states[host.name]
            except KeyError:
                prev_host_state = iterator.get_host_state(host)

            while result.needs_debugger(globally_enabled=self.debugger_active):
                next_action = NextAction()
                dbg = Debugger(task, host, task_vars, play_context, result, next_action)
                dbg.cmdloop()

                if next_action.result == NextAction.REDO:
                    # rollback host state
                    self._tqm.clear_failed_hosts()
                    if task.run_once and iterator._play.strategy in add_internal_fqcns(('linear',)) and result.is_failed():
                        for host_name, state in prev_host_states.items():
                            if host_name == host.name:
                                continue
                            iterator.set_state_for_host(host_name, state)
                            iterator._play._removed_hosts.remove(host_name)
                    iterator.set_state_for_host(host.name, prev_host_state)
                    for method, what in status_to_stats_map:
                        if getattr(result, method)():
                            self._tqm._stats.decrement(what, host.name)
                    self._tqm._stats.decrement('ok', host.name)

                    # redo
                    self._queue_task(host, task, task_vars, play_context)

                    _processed_results.extend(debug_closure(func)(self, iterator, one_pass))
                    break
                elif next_action.result == NextAction.CONTINUE:
                    _processed_results.append(result)
                    break
                elif next_action.result == NextAction.EXIT:
                    # Matches KeyboardInterrupt from bin/ansible
                    sys.exit(99)
            else:
                _processed_results.append(result)

        return _processed_results
    return inner


class StrategyBase:

    """
    This is the base class for strategy plugins, which contains some common
    code useful to all strategies like running handlers, cleanup actions, etc.
    """

    # by default, strategies should support throttling but we allow individual
    # strategies to disable this and either forego supporting it or managing
    # the throttling internally (as `free` does)
    ALLOW_BASE_THROTTLING = True

    def __init__(self, tqm: TaskQueueManager) -> None:
        self._tqm = tqm
        self._inventory = tqm.get_inventory()
        self._workers = tqm._workers
        self._variable_manager = tqm.get_variable_manager()
        self._loader = tqm.get_loader()
        self._final_q = tqm._final_q
        self._step = context.CLIARGS.get('step', False)
        self._diff = context.CLIARGS.get('diff', False)

        # the task cache is a dictionary of tuples of (host.name, task._uuid)
        # used to find the original task object of in-flight tasks and to store
        # the task args/vars and play context info used to queue the task.
        self._queued_task_cache: dict[tuple[str, str], dict[str, t.Any]] = {}

        # Backwards compat: self._display isn't really needed, just import the global display and use that.
        self._display = display

        # internal counters
        self._pending_results = 0
        self._cur_worker = 0

        # this dictionary is used to keep track of hosts that have
        # outstanding tasks still in queue
        self._blocked_hosts: dict[str, bool] = dict()

        self._results: deque[_RawTaskResult] = deque()
        self._results_lock = threading.Condition(threading.Lock())

        # create the result processing thread for reading results in the background
        self._results_thread = threading.Thread(target=results_thread_main, args=(self,))
        self._results_thread.daemon = True
        self._results_thread.start()

        # holds the list of active (persistent) connections to be shutdown at
        # play completion
        self._active_connections: dict[Host, str] = dict()

        # Caches for get_host calls, to avoid calling excessively
        # These values should be set at the top of the ``run`` method of each
        # strategy plugin. Use ``_set_hosts_cache`` to set these values
        self._hosts_cache: list[str] = []
        self._hosts_cache_all: list[str] = []

        self.debugger_active = C.ENABLE_TASK_DEBUGGER

    def _set_hosts_cache(self, play, refresh=True):
        """Responsible for setting _hosts_cache and _hosts_cache_all

        See comment in ``__init__`` for the purpose of these caches
        """
        if not refresh and all((self._hosts_cache, self._hosts_cache_all)):
            return

        if not play.finalized and TemplateEngine().is_template(play.hosts):
            _pattern = 'all'
        else:
            _pattern = play.hosts or 'all'
        self._hosts_cache_all = [h.name for h in self._inventory.get_hosts(pattern=_pattern, ignore_restrictions=True)]
        self._hosts_cache = [h.name for h in self._inventory.get_hosts(play.hosts, order=play.order)]

    def cleanup(self):
        # close active persistent connections
        for sock in self._active_connections.values():
            try:
                conn = Connection(sock)
                conn.reset()
            except ConnectionError as e:
                # most likely socket is already closed
                display.debug("got an error while closing persistent connection: %s" % e)
        self._final_q.put(_sentinel)
        self._results_thread.join()

    def run(self, iterator, play_context, result=0):
        # execute one more pass through the iterator without peeking, to
        # make sure that all of the hosts are advanced to their final task.
        # This should be safe, as everything should be IteratingStates.COMPLETE by
        # this point, though the strategy may not advance the hosts itself.

        for host in self._hosts_cache:
            if host not in self._tqm._unreachable_hosts:
                try:
                    iterator.get_next_task_for_host(self._inventory.hosts[host])
                except KeyError:
                    iterator.get_next_task_for_host(self._inventory.get_host(host))

        # return the appropriate code, depending on the status hosts after the run
        if not isinstance(result, bool) and result != self._tqm.RUN_OK:
            return result
        elif len(self._tqm._unreachable_hosts.keys()) > 0:
            return self._tqm.RUN_UNREACHABLE_HOSTS
        elif len(iterator.get_failed_hosts()) > 0:
            return self._tqm.RUN_FAILED_HOSTS
        else:
            return self._tqm.RUN_OK

    def get_hosts_remaining(self, play):
        self._set_hosts_cache(play, refresh=False)
        ignore = set(self._tqm._failed_hosts).union(self._tqm._unreachable_hosts)
        return [host for host in self._hosts_cache if host not in ignore]

    def get_failed_hosts(self, play):
        self._set_hosts_cache(play, refresh=False)
        return [host for host in self._hosts_cache if host in self._tqm._failed_hosts]

    def add_tqm_variables(self, vars, play):
        """
        Base class method to add extra variables/information to the list of task
        vars sent through the executor engine regarding the task queue manager state.
        """
        vars['ansible_current_hosts'] = self.get_hosts_remaining(play)
        vars['ansible_failed_hosts'] = self.get_failed_hosts(play)

    def _queue_task(self, host, task, task_vars, play_context):
        """ handles queueing the task up to be sent to a worker """

        display.debug("entering _queue_task() for %s/%s" % (host.name, task.action))

        # create a templar and template things we need later for the queuing process
        templar = TemplateEngine(loader=self._loader, variables=task_vars)

        try:
            throttle = int(templar.template(task.throttle))
        except Exception as ex:
            raise AnsibleError("Failed to convert the throttle value to an integer.", obj=task.throttle) from ex

        # and then queue the new task
        try:
            # Determine the "rewind point" of the worker list. This means we start
            # iterating over the list of workers until the end of the list is found.
            # Normally, that is simply the length of the workers list (as determined
            # by the forks or serial setting), however a task/block/play may "throttle"
            # that limit down.
            rewind_point = len(self._workers)
            if throttle > 0 and self.ALLOW_BASE_THROTTLING:
                if task.run_once:
                    display.debug("Ignoring 'throttle' as 'run_once' is also set for '%s'" % task.get_name())
                else:
                    if throttle <= rewind_point:
                        display.debug("task: %s, throttle: %d" % (task.get_name(), throttle))
                        rewind_point = throttle

            queued = False
            starting_worker = self._cur_worker
            while True:
                if self._cur_worker >= rewind_point:
                    self._cur_worker = 0

                worker_prc = self._workers[self._cur_worker]
                if worker_prc is None or not worker_prc.is_alive():
                    if worker_prc:
                        worker_prc.close()
                    self._queued_task_cache[(host.name, task._uuid)] = {
                        'host': host,
                        'task': task,
                        'task_vars': task_vars,
                        'play_context': play_context
                    }

                    # Pass WorkerProcess its strategy worker number so it can send an identifier along with intra-task requests
                    worker_prc = WorkerProcess(
                        final_q=self._final_q,
                        task_vars=task_vars,
                        host=host,
                        task=task,
                        play_context=play_context,
                        loader=self._loader,
                        variable_manager=self._variable_manager,
                        shared_loader_obj=plugin_loader.get_plugin_loader_namespace(),
                        worker_id=self._cur_worker,
                        cliargs=context.CLIARGS,
                    )
                    self._workers[self._cur_worker] = worker_prc
                    self._tqm.send_callback('v2_runner_on_start', host, task)
                    worker_prc.start()
                    display.debug("worker is %d (out of %d available)" % (self._cur_worker + 1, len(self._workers)))
                    queued = True

                self._cur_worker += 1

                if self._cur_worker >= rewind_point:
                    self._cur_worker = 0

                if queued:
                    break
                elif self._cur_worker == starting_worker:
                    time.sleep(0.0001)

            self._pending_results += 1
        except (EOFError, OSError, AssertionError) as ex:
            # most likely an abort
            display.debug(f"got an error while queuing: {ex}")
            return
        display.debug("exiting _queue_task() for %s/%s" % (host.name, task.action))

    def get_task_hosts(self, iterator, task_host, task):
        if task.run_once:
            host_list = [host for host in self._hosts_cache if host not in self._tqm._unreachable_hosts]
        else:
            host_list = [task_host.name]
        return host_list

    def get_delegated_hosts(self, result, task):
        host_name = result.get('_ansible_delegated_vars', {}).get('ansible_delegated_host', None)
        return [host_name or task.delegate_to]

    def _set_always_delegated_facts(self, result, task):
        """Sets host facts for ``delegate_to`` hosts for facts that should
        always be delegated

        This operation mutates ``result`` to remove the always delegated facts

        See ``ALWAYS_DELEGATE_FACT_PREFIXES``
        """
        if task.delegate_to is None:
            return

        facts = result['ansible_facts']
        always_keys = set()
        _add = always_keys.add
        for fact_key in facts:
            for always_key in ALWAYS_DELEGATE_FACT_PREFIXES:
                if fact_key.startswith(always_key):
                    _add(fact_key)
        if always_keys:
            _pop = facts.pop
            always_facts = {
                'ansible_facts': dict((k, _pop(k)) for k in list(facts) if k in always_keys)
            }
            host_list = self.get_delegated_hosts(result, task)
            _set_host_facts = self._variable_manager.set_host_facts
            for target_host in host_list:
                _set_host_facts(target_host, always_facts)

    def _convert_wire_task_result_to_raw(self, wire_task_result: _WireTaskResult) -> _RawTaskResult:
        """Return a `_RawTaskResult` created from a `_WireTaskResult`."""
        host = self._inventory.get_host(wire_task_result.host_name)
        queue_cache_entry = (host.name, wire_task_result.task_uuid)

        try:
            found_task = self._queued_task_cache[queue_cache_entry]['task']
        except KeyError:
            # This should only happen due to an implicit task created by the
            # TaskExecutor, restrict this behavior to the explicit use case
            # of an implicit async_status task
            if wire_task_result.task_fields.get('action') != 'async_status':
                raise

            task = Task()
        else:
            task = found_task.copy(exclude_parent=True, exclude_tasks=True)
            task._parent = found_task._parent

        task.from_attrs(wire_task_result.task_fields)

        return _RawTaskResult(
            host=host,
            task=task,
            return_data=wire_task_result.return_data,
            task_fields=wire_task_result.task_fields,
        )

    def search_handlers_by_notification(self, notification: str, iterator: PlayIterator) -> t.Generator[Handler, None, None]:
        handlers = [h for b in reversed(iterator._play.handlers) for h in b.block]
        # iterate in reversed order since last handler loaded with the same name wins
        for handler in handlers:
            if not handler.name:
                continue

            if not handler.cached_name:
                def variables_factory() -> dict[str, t.Any]:
                    return self._variable_manager.get_vars(
                        play=iterator._play,
                        task=handler,
                        _hosts=self._hosts_cache,
                        _hosts_all=self._hosts_cache_all
                    )

                templar = TemplateEngine(variables_factory=variables_factory)

                try:
                    handler.name = templar.template(handler.name)
                except AnsibleTemplateError as e:
                    # We skip this handler due to the fact that it may be using
                    # a variable in the name that was conditionally included via
                    # set_fact or some other method, and we don't want to error
                    # out unnecessarily
                    if not handler.listen:
                        display.warning(
                            "Handler '%s' is unusable because it has no listen topics and "
                            "the name could not be templated (host-specific variables are "
                            "not supported in handler names). The error: %s" % (handler.name, to_text(e))
                        )
                    continue

                handler.cached_name = True

            # first we check with the full result of get_name(), which may
            # include the role name (if the handler is from a role). If that
            # is not found, we resort to the simple name field, which doesn't
            # have anything extra added to it.
            if notification in {
                handler.name,
                handler.get_name(include_role_fqcn=False),
                handler.get_name(include_role_fqcn=True),
            }:
                yield handler
                break

        seen = set()
        for handler in handlers:
            if notification in handler.listen:
                if handler.name and handler.name in seen:
                    continue
                seen.add(handler.name)
                yield handler

    @debug_closure
    def _process_pending_results(self, iterator: PlayIterator, one_pass: bool = False, max_passes: int | None = None) -> list[_RawTaskResult]:
        """
        Reads results off the final queue and takes appropriate action
        based on the result (executing callbacks, updating state, etc.).
        """
        ret_results = []
        cur_pass = 0
        while True:
            try:
                self._results_lock.acquire()
                task_result = self._results.popleft()
            except IndexError:
                break
            finally:
                self._results_lock.release()

            original_host = task_result.host
            original_task: Task = task_result.task

            # all host status messages contain 2 entries: (msg, task_result)
            role_ran = False
            if task_result.is_failed():
                role_ran = True
                ignore_errors = original_task.ignore_errors
                if not ignore_errors:
                    # save the current state before failing it for later inspection
                    state_when_failed = iterator.get_state_for_host(original_host.name)
                    display.debug("marking %s as failed" % original_host.name)
                    if original_task.run_once:
                        # if we're using run_once, we have to fail every host here
                        for h in self._inventory.get_hosts(iterator._play.hosts):
                            if h.name not in self._tqm._unreachable_hosts:
                                iterator.mark_host_failed(h)
                    else:
                        iterator.mark_host_failed(original_host)

                    state, dummy = iterator.get_next_task_for_host(original_host, peek=True)

                    if iterator.is_failed(original_host) and state and state.run_state == IteratingStates.COMPLETE:
                        self._tqm._failed_hosts[original_host.name] = True

                    # if we're iterating on the rescue portion of a block then
                    # we save the failed task in a special var for use
                    # within the rescue/always
                    if iterator.is_any_block_rescuing(state_when_failed):
                        self._tqm._stats.increment('rescued', original_host.name)
                        iterator._play._removed_hosts.remove(original_host.name)
                        self._variable_manager.set_nonpersistent_facts(
                            original_host.name,
                            dict(
                                ansible_failed_task=original_task.dump_attrs(),
                                ansible_failed_result=task_result._return_data,
                            ),
                        )
                    else:
                        self._tqm._stats.increment('failures', original_host.name)
                else:
                    self._tqm._stats.increment('ok', original_host.name)
                    self._tqm._stats.increment('ignored', original_host.name)
                    if task_result.is_changed():
                        self._tqm._stats.increment('changed', original_host.name)
                self._tqm.send_callback('v2_runner_on_failed', task_result, ignore_errors=ignore_errors)
            elif task_result.is_unreachable():
                ignore_unreachable = original_task.ignore_unreachable
                if not ignore_unreachable:
                    self._tqm._unreachable_hosts[original_host.name] = True
                    iterator._play._removed_hosts.append(original_host.name)
                    self._tqm._stats.increment('dark', original_host.name)
                else:
                    self._tqm._stats.increment('ok', original_host.name)
                    self._tqm._stats.increment('ignored', original_host.name)
                self._tqm.send_callback('v2_runner_on_unreachable', task_result)
            elif task_result.is_skipped():
                self._tqm._stats.increment('skipped', original_host.name)
                self._tqm.send_callback('v2_runner_on_skipped', task_result)
            else:
                role_ran = True

                if original_task.loop:
                    # this task had a loop, and has more than one result, so
                    # loop over all of them instead of a single result
                    result_items = task_result._loop_results
                else:
                    result_items = [task_result._return_data]

                for result_item in result_items:
                    if '_ansible_notify' in result_item and task_result.is_changed():
                        # only ensure that notified handlers exist, if so save the notifications for when
                        # handlers are actually flushed so the last defined handlers are executed,
                        # otherwise depending on the setting either error or warn
                        host_state = iterator.get_state_for_host(original_host.name)
                        for notification in result_item['_ansible_notify']:
                            handler: type[Sentinel] | Handler = Sentinel
                            for handler in self.search_handlers_by_notification(notification, iterator):
                                if host_state.run_state == IteratingStates.HANDLERS:
                                    # we're currently iterating handlers, so we need to expand this now
                                    if handler.notify_host(original_host):
                                        # NOTE even with notifications deduplicated this can still happen in case of handlers being
                                        # notified multiple times using different names, like role name or fqcn
                                        self._tqm.send_callback('v2_playbook_on_notify', handler, original_host)
                                else:
                                    iterator.add_notification(original_host.name, notification)
                                    display.vv(f"Notification for handler {notification} has been saved.")
                                    break
                            if handler is Sentinel:
                                msg = (
                                    f"The requested handler '{notification}' was not found in either the main handlers"
                                    " list nor in the listening handlers list"
                                )
                                if C.ERROR_ON_MISSING_HANDLER:
                                    raise AnsibleError(msg)
                                else:
                                    display.warning(msg)

                    if 'add_host' in result_item:
                        # this task added a new host (add_host module)
                        new_host_info = result_item.get('add_host', dict())
                        self._inventory.add_dynamic_host(new_host_info, result_item)
                        # ensure host is available for subsequent plays
                        if result_item.get('changed') and new_host_info['host_name'] not in self._hosts_cache_all:
                            self._hosts_cache_all.append(new_host_info['host_name'])

                    elif 'add_group' in result_item:
                        # this task added a new group (group_by module)
                        self._inventory.add_dynamic_group(original_host, result_item)

                    if 'add_host' in result_item or 'add_group' in result_item:
                        item_vars = _get_item_vars(result_item, original_task)
                        found_task_vars = self._queued_task_cache.get((original_host.name, task_result.task._uuid))['task_vars']
                        if item_vars:
                            all_task_vars = combine_vars(found_task_vars, item_vars)
                        else:
                            all_task_vars = found_task_vars
                        all_task_vars[original_task.register] = result_item

                        if original_task.changed_when:
                            result_item['changed'] = original_task._resolve_conditional(original_task.changed_when, all_task_vars)

                        if original_task.failed_when:
                            result_item['failed_when_result'] = result_item['failed'] = (
                                original_task._resolve_conditional(original_task.failed_when, all_task_vars))

                        if original_task.loop or original_task.loop_with:
                            new_item_result = _RawTaskResult(
                                task_result.host,
                                task_result.task,
                                result_item,
                                task_result.task_fields,
                            )
                            self._tqm.send_callback('v2_runner_item_on_ok', new_item_result)
                            if result_item.get('changed', False):
                                task_result._return_data['changed'] = True
                            if result_item.get('failed', False):
                                task_result._return_data['failed'] = True

                    if 'ansible_facts' in result_item and original_task.action not in C._ACTION_DEBUG:
                        # if delegated fact and we are delegating facts, we need to change target host for them
                        if original_task.delegate_to is not None and original_task.delegate_facts:
                            host_list = self.get_delegated_hosts(result_item, original_task)
                        else:
                            # Set facts that should always be on the delegated hosts
                            self._set_always_delegated_facts(result_item, original_task)

                            host_list = self.get_task_hosts(iterator, original_host, original_task)

                        if original_task.action in C._ACTION_INCLUDE_VARS:
                            for (var_name, var_value) in result_item['ansible_facts'].items():
                                # find the host we're actually referring too here, which may
                                # be a host that is not really in inventory at all
                                for target_host in host_list:
                                    self._variable_manager.set_host_variable(target_host, var_name, var_value)
                        else:
                            cacheable = result_item.pop('_ansible_facts_cacheable', False)
                            for target_host in host_list:
                                # so set_fact is a misnomer but 'cacheable = true' was meant to create an 'actual fact'
                                # to avoid issues with precedence and confusion with set_fact normal operation,
                                # we set BOTH fact and nonpersistent_facts (aka hostvar)
                                # when fact is retrieved from cache in subsequent operations it will have the lower precedence,
                                # but for playbook setting it the 'higher' precedence is kept
                                is_set_fact = original_task.action in C._ACTION_SET_FACT
                                if not is_set_fact or cacheable:
                                    self._variable_manager.set_host_facts(target_host, result_item['ansible_facts'].copy())
                                if is_set_fact:
                                    self._variable_manager.set_nonpersistent_facts(target_host, result_item['ansible_facts'].copy())

                    if 'ansible_stats' in result_item and 'data' in result_item['ansible_stats'] and result_item['ansible_stats']['data']:

                        if 'per_host' not in result_item['ansible_stats'] or result_item['ansible_stats']['per_host']:
                            host_list = self.get_task_hosts(iterator, original_host, original_task)
                        else:
                            host_list = [None]

                        data = result_item['ansible_stats']['data']
                        aggregate = 'aggregate' in result_item['ansible_stats'] and result_item['ansible_stats']['aggregate']
                        for myhost in host_list:
                            for k in data.keys():
                                if aggregate:
                                    self._tqm._stats.update_custom_stats(k, data[k], myhost)
                                else:
                                    self._tqm._stats.set_custom_stats(k, data[k], myhost)

                if 'diff' in task_result._return_data:
                    if self._diff or getattr(original_task, 'diff', False):
                        self._tqm.send_callback('v2_on_file_diff', task_result)

                if not isinstance(original_task, TaskInclude):
                    self._tqm._stats.increment('ok', original_host.name)
                    if task_result.is_changed():
                        self._tqm._stats.increment('changed', original_host.name)

                # finally, send the ok for this task
                self._tqm.send_callback('v2_runner_on_ok', task_result)

            # register final results
            if original_task.register:
                host_list = self.get_task_hosts(iterator, original_host, original_task)

                clean_copy = strip_internal_keys(module_response_deepcopy(task_result._return_data))
                if 'invocation' in clean_copy:
                    del clean_copy['invocation']

                for target_host in host_list:
                    self._variable_manager.set_nonpersistent_facts(target_host, {original_task.register: clean_copy})

            self._pending_results -= 1
            if original_host.name in self._blocked_hosts:
                del self._blocked_hosts[original_host.name]

            # If this is a role task, mark the parent role as being run (if
            # the task was ok or failed, but not skipped or unreachable)
            if original_task._role is not None and role_ran:  # TODO:  and original_task.action not in C._ACTION_INCLUDE_ROLE:?
                # lookup the role in the role cache to make sure we're dealing
                # with the correct object and mark it as executed
                role_obj = self._get_cached_role(original_task, iterator._play)
                role_obj._had_task_run[original_host.name] = True

            ret_results.append(task_result)

            if one_pass or max_passes is not None and (cur_pass + 1) >= max_passes:
                break

            cur_pass += 1

        return ret_results

    def _wait_on_pending_results(self, iterator):
        """
        Wait for the shared counter to drop to zero, using a short sleep
        between checks to ensure we don't spin lock
        """

        ret_results = []

        display.debug("waiting for pending results...")
        while self._pending_results > 0 and not self._tqm._terminated:

            if self._tqm.has_dead_workers():
                raise AnsibleError("A worker was found in a dead state")

            results = self._process_pending_results(iterator)
            ret_results.extend(results)
            if self._pending_results > 0:
                time.sleep(C.DEFAULT_INTERNAL_POLL_INTERVAL)

        display.debug("no more pending results, returning what we have")

        return ret_results

    def _copy_included_file(self, included_file: IncludedFile) -> TaskInclude | IncludeRole:
        """
        A proven safe and performant way to create a copy of an included file
        """
        ti_copy = included_file._task.copy(exclude_parent=True)
        ti_copy._parent = included_file._task._parent

        temp_vars = ti_copy.vars | included_file._vars

        ti_copy.vars = temp_vars

        return ti_copy

    def _load_included_file(self, included_file: IncludedFile, iterator, is_handler=False, handle_stats_and_callbacks=True):
        """
        Loads an included YAML file of tasks, applying the optional set of variables.

        Raises AnsibleError exception in case of a failure during including a file,
        in such case the caller is responsible for marking the host(s) as failed
        using PlayIterator.mark_host_failed().
        """
        if handle_stats_and_callbacks:
            display.deprecated(
                msg="Reporting play recap stats and running callbacks functionality for "
                    "``include_tasks`` in ``StrategyBase._load_included_file`` is deprecated. "
                    "See ``https://github.com/ansible/ansible/pull/79260`` for guidance on how to "
                    "move the reporting into specific strategy plugins to account for "
                    "``include_role`` tasks as well.",
                version="2.21",
            )
        display.debug("loading included file: %s" % included_file._filename)
        try:
            data = self._loader.load_from_file(included_file._filename, trusted_as_template=True)
            if data is None:
                return []
            elif not isinstance(data, list):
                raise AnsibleError("included task files must contain a list of tasks")

            ti_copy = self._copy_included_file(included_file)

            block_list = load_list_of_blocks(
                data,
                play=iterator._play,
                parent_block=ti_copy.build_parent_block(),
                role=included_file._task._role,
                use_handlers=is_handler,
                loader=self._loader,
                variable_manager=self._variable_manager,
            )
            if handle_stats_and_callbacks:
                for host in included_file._hosts:
                    self._tqm._stats.increment('ok', host.name)
        except AnsibleParserError:
            raise
        except AnsibleError as e:
            if isinstance(e, AnsibleFileNotFound):
                reason = "Could not find or access '%s' on the Ansible Controller." % to_text(e.file_name)
            else:
                reason = to_text(e)
            if handle_stats_and_callbacks:
                for tr in included_file._results:
                    tr._return_data['failed'] = True

                for host in included_file._hosts:
                    tr = _RawTaskResult(host=host, task=included_file._task, return_data=dict(failed=True, reason=reason), task_fields={})
                    self._tqm._stats.increment('failures', host.name)
                    self._tqm.send_callback('v2_runner_on_failed', tr)
            raise AnsibleError(reason) from e

        if handle_stats_and_callbacks:
            self._tqm.send_callback('v2_playbook_on_include', included_file)
        display.debug("done processing included file")
        return block_list

    def _take_step(self, task, host=None):

        ret = False
        msg = u'Perform task: %s ' % task
        if host:
            msg += u'on %s ' % host
        msg += u'(N)o/(y)es/(c)ontinue: '
        resp = display.prompt(msg)

        if resp.lower() in ['y', 'yes']:
            display.debug("User ran task")
            ret = True
        elif resp.lower() in ['c', 'continue']:
            display.debug("User ran task and canceled step mode")
            self._step = False
            ret = True
        else:
            display.debug("User skipped task")

        display.banner(msg)

        return ret

    def _cond_not_supported_warn(self, task_name):
        display.warning("%s task does not support when conditional" % task_name)

    def _execute_meta(self, task: Task, play_context, iterator, target_host: Host):
        task._resolved_action = 'ansible.builtin.meta'  # _post_validate_args is never called for meta actions, so resolved_action hasn't been set

        # meta tasks store their args in the _raw_params field of args,
        # since they do not use k=v pairs, so get that
        meta_action = task._get_meta()

        def _evaluate_conditional(conditional_host: Host) -> bool:
            if not task.when:
                return True

            return task._resolve_conditional(task.when, self._variable_manager.get_vars(
                play=iterator._play, host=conditional_host, task=task, _hosts=self._hosts_cache, _hosts_all=self._hosts_cache_all))

        skipped = False
        msg = meta_action
        skip_reason = '%s conditional evaluated to False' % meta_action
        if isinstance(task, Handler):
            self._tqm.send_callback('v2_playbook_on_handler_task_start', task)
        else:
            self._tqm.send_callback('v2_playbook_on_task_start', task, is_conditional=False)

        # These don't support "when" conditionals
        if meta_action in ('noop', 'refresh_inventory', 'reset_connection') and task.when:
            self._cond_not_supported_warn(meta_action)

        if meta_action == 'noop':
            msg = "noop"
        elif meta_action == 'flush_handlers':
            if _evaluate_conditional(target_host):
                host_state = iterator.get_state_for_host(target_host.name)
                # actually notify proper handlers based on all notifications up to this point
                for notification in list(host_state.handler_notifications):
                    for handler in self.search_handlers_by_notification(notification, iterator):
                        if handler.notify_host(target_host):
                            # NOTE even with notifications deduplicated this can still happen in case of handlers being
                            # notified multiple times using different names, like role name or fqcn
                            self._tqm.send_callback('v2_playbook_on_notify', handler, target_host)
                    iterator.clear_notification(target_host.name, notification)

                if host_state.run_state == IteratingStates.HANDLERS:
                    raise AnsibleError('flush_handlers cannot be used as a handler')
                if target_host.name not in self._tqm._unreachable_hosts:
                    host_state.pre_flushing_run_state = host_state.run_state
                    host_state.run_state = IteratingStates.HANDLERS
                msg = "triggered running handlers for %s" % target_host.name
            else:
                skipped = True
                skip_reason += ', not running handlers for %s' % target_host.name
        elif meta_action == 'refresh_inventory':
            self._inventory.refresh_inventory()
            self._set_hosts_cache(iterator._play)
            msg = "inventory successfully refreshed"
        elif meta_action == 'clear_facts':
            if _evaluate_conditional(target_host):
                for host in self._inventory.get_hosts(iterator._play.hosts):
                    hostname = host.get_name()
                    self._variable_manager.clear_facts(hostname)
                msg = "facts cleared"
            else:
                skipped = True
                skip_reason += ', not clearing facts and fact cache for %s' % target_host.name
        elif meta_action == 'clear_host_errors':
            if _evaluate_conditional(target_host):
                for host in self._inventory.get_hosts(iterator._play.hosts):
                    self._tqm._failed_hosts.pop(host.name, False)
                    self._tqm._unreachable_hosts.pop(host.name, False)
                    iterator.clear_host_errors(host)
                msg = "cleared host errors"
            else:
                skipped = True
                skip_reason += ', not clearing host error state for %s' % target_host.name
        elif meta_action == 'end_batch':
            if _evaluate_conditional(target_host):
                for host in self._inventory.get_hosts(iterator._play.hosts):
                    if host.name not in self._tqm._unreachable_hosts:
                        iterator.end_host(host.name)
                msg = "ending batch"
            else:
                skipped = True
                skip_reason += ', continuing current batch'
        elif meta_action == 'end_play':
            if _evaluate_conditional(target_host):
                for host in self._inventory.get_hosts(iterator._play.hosts):
                    if host.name not in self._tqm._unreachable_hosts:
                        iterator.end_host(host.name)
                        # end_play is used in PlaybookExecutor/TQM to indicate that
                        # the whole play is supposed to be ended as opposed to just a batch
                        iterator.end_play = True
                msg = "ending play"
            else:
                skipped = True
                skip_reason += ', continuing play'
        elif meta_action == 'end_host':
            if _evaluate_conditional(target_host):
                iterator.end_host(target_host.name)
                msg = "ending play for %s" % target_host.name
            else:
                skipped = True
                skip_reason += ", continuing execution for %s" % target_host.name
                # TODO: Nix msg here? Left for historical reasons, but skip_reason exists now.
                msg = "end_host conditional evaluated to false, continuing execution for %s" % target_host.name
        elif meta_action == 'role_complete':
            if task.implicit:
                role_obj = self._get_cached_role(task, iterator._play)
                if target_host.name in role_obj._had_task_run:
                    role_obj._completed[target_host.name] = True
                    msg = 'role_complete for %s' % target_host.name
        elif meta_action == 'end_role':
            if _evaluate_conditional(target_host):
                while True:
                    state, task = iterator.get_next_task_for_host(target_host, peek=True)
                    if task._get_meta() == "role_complete":
                        break
                    iterator.set_state_for_host(target_host.name, state)
                    display.debug("'%s' skipped because role has been ended via 'end_role'" % task)
                msg = 'ending role %s for %s' % (task._role.get_name(), target_host.name)
            else:
                skipped = True
                skip_reason += 'continuing role %s for %s' % (task._role.get_name(), target_host.name)
        elif meta_action == 'reset_connection':
            all_vars = self._variable_manager.get_vars(play=iterator._play, host=target_host, task=task,
                                                       _hosts=self._hosts_cache, _hosts_all=self._hosts_cache_all)
            templar = TemplateEngine(loader=self._loader, variables=all_vars)

            # apply the given task's information to the connection info,
            # which may override some fields already set by the play or
            # the options specified on the command line
            play_context = play_context.set_task_and_variable_override(task=task, variables=all_vars, templar=templar)

            # fields set from the play/task may be based on variables, so we have to
            # do the same kind of post validation step on it here before we use it.
            play_context.post_validate(templar=templar)

            # now that the play context is finalized, if the remote_addr is not set
            # default to using the host's address field as the remote address
            if not play_context.remote_addr:
                play_context.remote_addr = target_host.address

            # We also add "magic" variables back into the variables dict to make sure
            # a certain subset of variables exist. This 'mostly' works here cause meta
            # disregards the loop, but should not really use play_context at all
            play_context.update_vars(all_vars)

            if target_host in self._active_connections:
                connection = Connection(self._active_connections[target_host])
                del self._active_connections[target_host]
            else:
                connection = plugin_loader.connection_loader.get(play_context.connection, play_context, os.devnull)
                var_options = connection._resolve_option_variables(all_vars, templar)
                connection.set_options(task_keys=task.dump_attrs(), var_options=var_options)
                play_context.set_attributes_from_plugin(connection)

            if connection:
                try:
                    connection.reset()
                    msg = 'reset connection'
                except ConnectionError as e:
                    # most likely socket is already closed
                    display.debug("got an error while closing persistent connection: %s" % e)
            else:
                msg = 'no connection, nothing to reset'
        else:
            raise AnsibleError("invalid meta action requested: %s" % meta_action, obj=task._ds)

        result: dict[str, object] = {'msg': msg}
        if skipped:
            result['skipped'] = True
            result['skip_reason'] = skip_reason
        else:
            result['changed'] = False

        header = skip_reason if skipped else msg
        if task.implicit:
            display.debug(f"META: {header}")
        else:
            display.vv(f"META: {header}")

        res = _RawTaskResult(target_host, task, result, {})
        if skipped:
            self._tqm.send_callback('v2_runner_on_skipped', res)
        return [res]

    def _get_cached_role(self, task, play):
        return play._get_cached_role(task._role)

    def get_hosts_left(self, iterator):
        """ returns list of available hosts for this iterator by filtering out unreachables """

        hosts_left = []
        for host in self._hosts_cache:
            if host not in self._tqm._unreachable_hosts:
                try:
                    hosts_left.append(self._inventory.hosts[host])
                except KeyError:
                    hosts_left.append(self._inventory.get_host(host))
        return hosts_left

    def update_active_connections(self, results: _c.Iterable[_RawTaskResult]) -> None:
        """ updates the current active persistent connections """
        for r in results:
            if 'args' in r.task_fields:
                socket_path = r.task_fields['args'].get('_ansible_socket')
                if socket_path:
                    if r.host not in self._active_connections:
                        self._active_connections[r.host] = socket_path


class NextAction(object):
    """ The next action after an interpreter's exit. """
    REDO = 1
    CONTINUE = 2
    EXIT = 3

    def __init__(self, result=EXIT):
        self.result = result


class Debugger(cmd.Cmd):
    prompt_continuous = '> '  # multiple lines

    def __init__(self, task, host, task_vars, play_context, result, next_action):
        # cmd.Cmd is old-style class
        cmd.Cmd.__init__(self)

        self.prompt = '[%s] %s (debug)> ' % (host, task)
        self.intro = None
        self.scope = {}
        self.scope['task'] = task
        self.scope['task_vars'] = task_vars
        self.scope['host'] = host
        self.scope['play_context'] = play_context
        self.scope['result'] = result
        self.next_action = next_action

    def cmdloop(self):
        try:
            cmd.Cmd.cmdloop(self)
        except KeyboardInterrupt:
            pass

    do_h = cmd.Cmd.do_help

    def do_EOF(self, args):
        """Quit"""
        return self.do_quit(args)

    def do_quit(self, args):
        """Quit"""
        display.display('User interrupted execution')
        self.next_action.result = NextAction.EXIT
        return True

    do_q = do_quit

    def do_continue(self, args):
        """Continue to next result"""
        self.next_action.result = NextAction.CONTINUE
        return True

    do_c = do_continue

    def do_redo(self, args):
        """Schedule task for re-execution. The re-execution may not be the next result"""
        self.next_action.result = NextAction.REDO
        return True

    do_r = do_redo

    def do_update_task(self, args):
        """Recreate the task from ``task._ds``, and template with updated ``task_vars``"""
        templar = TemplateEngine(variables=self.scope['task_vars'])
        task = self.scope['task']
        task = task.load_data(task._ds)
        task.post_validate(templar)
        self.scope['task'] = task

    do_u = do_update_task

    def evaluate(self, args):
        try:
            return eval(args, globals(), self.scope)
        except Exception:
            t, v = sys.exc_info()[:2]
            if isinstance(t, str):
                exc_type_name = t
            else:
                exc_type_name = t.__name__
            display.display('***%s:%s' % (exc_type_name, repr(v)))
            raise

    def do_pprint(self, args):
        """Pretty Print"""
        try:
            result = self.evaluate(args)
            display.display(pprint.pformat(result))
        except Exception:
            pass

    do_p = do_pprint

    def execute(self, args):
        try:
            code = compile(args + '\n', '<stdin>', 'single')
            exec(code, globals(), self.scope)
        except Exception:
            t, v = sys.exc_info()[:2]
            if isinstance(t, str):
                exc_type_name = t
            else:
                exc_type_name = t.__name__
            display.display('***%s:%s' % (exc_type_name, repr(v)))
            raise

    def default(self, line):
        try:
            self.execute(line)
        except Exception:
            pass
