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

DOCUMENTATION = '''
    name: linear
    short_description: Executes tasks in a linear fashion
    description:
        - Task execution is in lockstep per host batch as defined by C(serial) (default all).
          Up to the fork limit of hosts will execute each task at the same time and then
          the next series of hosts until the batch is done, before going on to the next task.
    version_added: "2.0"
    notes:
     - This was the default Ansible behaviour before 'strategy plugins' were introduced in 2.0.
    author: Ansible Core Team
'''

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleAssertionError, AnsibleParserError
from ansible.module_utils.common.text.converters import to_text
from ansible.playbook.handler import Handler
from ansible.playbook.included_file import IncludedFile
from ansible.plugins.loader import action_loader
from ansible.plugins.strategy import StrategyBase
from ansible.template import Templar
from ansible.utils.display import Display

display = Display()


class StrategyModule(StrategyBase):

    def _get_next_task_lockstep(self, hosts, iterator):
        '''
        Returns a list of (host, task) tuples, where the task may
        be a noop task to keep the iterator in lock step across
        all hosts.
        '''
        state_task_per_host = {}
        for host in hosts:
            state, task = iterator.get_next_task_for_host(host, peek=True)
            if task is not None:
                state_task_per_host[host] = state, task

        if not state_task_per_host:
            return []

        task_uuids = {t._uuid for s, t in state_task_per_host.values()}
        _loop_cnt = 0
        while _loop_cnt <= 1:
            try:
                cur_task = iterator.all_tasks[iterator.cur_task]
            except IndexError:
                # pick up any tasks left after clear_host_errors
                iterator.cur_task = 0
                _loop_cnt += 1
            else:
                iterator.cur_task += 1
                if cur_task._uuid in task_uuids:
                    break
        else:
            # prevent infinite loop
            raise AnsibleAssertionError(
                'BUG: There seems to be a mismatch between tasks in PlayIterator and HostStates.'
            )

        host_tasks = []
        for host, (state, task) in state_task_per_host.items():
            if cur_task._uuid == task._uuid:
                iterator.set_state_for_host(host.name, state)
                host_tasks.append((host, task))

        if cur_task.action in C._ACTION_META and cur_task.args.get('_raw_params') == 'flush_handlers':
            iterator.all_tasks[iterator.cur_task:iterator.cur_task] = [h for b in iterator._play.handlers for h in b.block]

        return host_tasks

    def run(self, iterator, play_context):
        '''
        The linear strategy is simple - get the next task and queue
        it for all hosts, then wait for the queue to drain before
        moving on to the next task
        '''

        # iterate over each task, while there is one left to run
        result = self._tqm.RUN_OK
        work_to_do = True

        self._set_hosts_cache(iterator._play)

        while work_to_do and not self._tqm._terminated:

            try:
                display.debug("getting the remaining hosts for this loop")
                hosts_left = self.get_hosts_left(iterator)
                display.debug("done getting the remaining hosts for this loop")

                # queue up this task for each host in the inventory
                callback_sent = False
                work_to_do = False

                host_tasks = self._get_next_task_lockstep(hosts_left, iterator)

                # skip control
                skip_rest = False
                choose_step = True

                # flag set if task is set to any_errors_fatal
                any_errors_fatal = False

                results = []
                for (host, task) in host_tasks:
                    if self._tqm._terminated:
                        break

                    run_once = False
                    work_to_do = True

                    # check to see if this task should be skipped, due to it being a member of a
                    # role which has already run (and whether that role allows duplicate execution)
                    if not isinstance(task, Handler) and task._role:
                        role_obj = self._get_cached_role(task, iterator._play)
                        if role_obj.has_run(host) and task._role._metadata.allow_duplicates is False:
                            display.debug("'%s' skipped because role has already run" % task)
                            continue

                    display.debug("getting variables")
                    task_vars = self._variable_manager.get_vars(play=iterator._play, host=host, task=task,
                                                                _hosts=self._hosts_cache, _hosts_all=self._hosts_cache_all)
                    self.add_tqm_variables(task_vars, play=iterator._play)
                    templar = Templar(loader=self._loader, variables=task_vars)
                    display.debug("done getting variables")

                    # test to see if the task across all hosts points to an action plugin which
                    # sets BYPASS_HOST_LOOP to true, or if it has run_once enabled. If so, we
                    # will only send this task to the first host in the list.

                    task_action = templar.template(task.action)

                    try:
                        action = action_loader.get(task_action, class_only=True, collection_list=task.collections)
                    except KeyError:
                        # we don't care here, because the action may simply not have a
                        # corresponding action plugin
                        action = None

                    if task_action in C._ACTION_META:
                        # for the linear strategy, we run meta tasks just once and for
                        # all hosts currently being iterated over rather than one host
                        results.extend(self._execute_meta(task, play_context, iterator, host))
                        if task.args.get('_raw_params', None) not in ('noop', 'reset_connection', 'end_host', 'role_complete', 'flush_handlers', 'end_role'):
                            run_once = True
                        if (task.any_errors_fatal or run_once) and not task.ignore_errors:
                            any_errors_fatal = True
                    else:
                        # handle step if needed, skip meta actions as they are used internally
                        if self._step and choose_step:
                            if self._take_step(task):
                                choose_step = False
                            else:
                                skip_rest = True
                                break

                        run_once = action and getattr(action, 'BYPASS_HOST_LOOP', False) or templar.template(task.run_once)
                        try:
                            task.name = to_text(templar.template(task.name, fail_on_undefined=False), nonstring='empty')
                        except Exception as e:
                            display.debug(f"Failed to templalte task name ({task.name}), ignoring error and continuing: {e}")

                        if (task.any_errors_fatal or run_once) and not task.ignore_errors:
                            any_errors_fatal = True

                        if not callback_sent:
                            if isinstance(task, Handler):
                                self._tqm.send_callback('v2_playbook_on_handler_task_start', task)
                            else:
                                self._tqm.send_callback('v2_playbook_on_task_start', task, is_conditional=False)
                            callback_sent = True

                        self._blocked_hosts[host.get_name()] = True
                        self._queue_task(host, task, task_vars, play_context)
                        del task_vars

                    if isinstance(task, Handler):
                        if run_once:
                            task.clear_hosts()
                        else:
                            task.remove_host(host)

                    # if we're bypassing the host loop, break out now
                    if run_once:
                        break

                    results.extend(self._process_pending_results(iterator, max_passes=max(1, int(len(self._tqm._workers) * 0.1))))

                # go to next host/task group
                if skip_rest:
                    continue

                display.debug("done queuing things up, now waiting for results queue to drain")
                if self._pending_results > 0:
                    results.extend(self._wait_on_pending_results(iterator))

                self.update_active_connections(results)

                included_files = IncludedFile.process_include_results(
                    results,
                    iterator=iterator,
                    loader=self._loader,
                    variable_manager=self._variable_manager
                )

                if len(included_files) > 0:
                    display.debug("we have included files to process")

                    display.debug("generating all_blocks data")
                    all_blocks = dict((host, []) for host in hosts_left)
                    display.debug("done generating all_blocks data")
                    included_tasks = []
                    failed_includes_hosts = set()
                    for included_file in included_files:
                        display.debug("processing included file: %s" % included_file._filename)
                        is_handler = False
                        try:
                            if included_file._is_role:
                                new_ir = self._copy_included_file(included_file)

                                new_blocks, handler_blocks = new_ir.get_block_list(
                                    play=iterator._play,
                                    variable_manager=self._variable_manager,
                                    loader=self._loader,
                                )
                            else:
                                is_handler = isinstance(included_file._task, Handler)
                                new_blocks = self._load_included_file(
                                    included_file,
                                    iterator=iterator,
                                    is_handler=is_handler,
                                    handle_stats_and_callbacks=False,
                                )

                            # let PlayIterator know about any new handlers included via include_role or
                            # import_role within include_role/include_taks
                            iterator.handlers = [h for b in iterator._play.handlers for h in b.block]

                            display.debug("iterating over new_blocks loaded from include file")
                            for new_block in new_blocks:
                                if is_handler:
                                    for task in new_block.block:
                                        task.notified_hosts = included_file._hosts[:]
                                    final_block = new_block
                                else:
                                    task_vars = self._variable_manager.get_vars(
                                        play=iterator._play,
                                        task=new_block.get_first_parent_include(),
                                        _hosts=self._hosts_cache,
                                        _hosts_all=self._hosts_cache_all,
                                    )
                                    display.debug("filtering new block on tags")
                                    final_block = new_block.filter_tagged_tasks(task_vars)
                                    display.debug("done filtering new block on tags")

                                included_tasks.extend(final_block.get_tasks())

                                for host in hosts_left:
                                    if host in included_file._hosts:
                                        all_blocks[host].append(final_block)

                            display.debug("done iterating over new_blocks loaded from include file")
                        except AnsibleParserError:
                            raise
                        except AnsibleError as e:
                            display.error(to_text(e), wrap_text=False)
                            for r in included_file._results:
                                r._result['failed'] = True
                                r._result['reason'] = str(e)
                                self._tqm._stats.increment('failures', r._host.name)
                                self._tqm.send_callback('v2_runner_on_failed', r)
                                failed_includes_hosts.add(r._host)
                        else:
                            # since we skip incrementing the stats when the task result is
                            # first processed, we do so now for each host in the list
                            for host in included_file._hosts:
                                self._tqm._stats.increment('ok', host.name)
                            self._tqm.send_callback('v2_playbook_on_include', included_file)

                    for host in failed_includes_hosts:
                        self._tqm._failed_hosts[host.name] = True
                        iterator.mark_host_failed(host)

                    # finally go through all of the hosts and append the
                    # accumulated blocks to their list of tasks
                    display.debug("extending task lists for all hosts with included blocks")

                    for host in hosts_left:
                        iterator.add_tasks(host, all_blocks[host])

                    iterator.all_tasks[iterator.cur_task:iterator.cur_task] = included_tasks

                    display.debug("done extending task lists")
                    display.debug("done processing included files")

                display.debug("results queue empty")

                display.debug("checking for any_errors_fatal")
                failed_hosts = []
                unreachable_hosts = []
                for res in results:
                    if res.is_failed():
                        failed_hosts.append(res._host.name)
                    elif res.is_unreachable():
                        unreachable_hosts.append(res._host.name)

                if any_errors_fatal and (failed_hosts or unreachable_hosts):
                    for host in hosts_left:
                        if host.name not in failed_hosts:
                            self._tqm._failed_hosts[host.name] = True
                            iterator.mark_host_failed(host)
                display.debug("done checking for any_errors_fatal")

                display.debug("checking for max_fail_percentage")
                if iterator._play.max_fail_percentage is not None and len(results) > 0:
                    percentage = iterator._play.max_fail_percentage / 100.0

                    if (len(self._tqm._failed_hosts) / iterator.batch_size) > percentage:
                        for host in hosts_left:
                            # don't double-mark hosts, or the iterator will potentially
                            # fail them out of the rescue/always states
                            if host.name not in failed_hosts:
                                self._tqm._failed_hosts[host.name] = True
                                iterator.mark_host_failed(host)
                        self._tqm.send_callback('v2_playbook_on_no_hosts_remaining')
                        result |= self._tqm.RUN_FAILED_BREAK_PLAY
                    display.debug('(%s failed / %s total )> %s max fail' % (len(self._tqm._failed_hosts), iterator.batch_size, percentage))
                display.debug("done checking for max_fail_percentage")

                display.debug("checking to see if all hosts have failed and the running result is not ok")
                if result != self._tqm.RUN_OK and len(self._tqm._failed_hosts) >= len(hosts_left):
                    display.debug("^ not ok, so returning result now")
                    self._tqm.send_callback('v2_playbook_on_no_hosts_remaining')
                    return result
                display.debug("done checking to see if all hosts have failed")

            except (IOError, EOFError) as e:
                display.debug("got IOError/EOFError in task loop: %s" % e)
                # most likely an abort, return failed
                return self._tqm.RUN_UNKNOWN_ERROR

        # run the base class run() method, which executes the cleanup function
        # and runs any outstanding handlers which have been triggered

        return super(StrategyModule, self).run(iterator, play_context, result)
