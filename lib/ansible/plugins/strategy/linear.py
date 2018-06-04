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

DOCUMENTATION = '''
    strategy: linear
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

from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible.executor.play_iterator import PlayIterator
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_text
from ansible.playbook.block import Block
from ansible.playbook.included_file import IncludedFile
from ansible.playbook.task import Task
from ansible.plugins.loader import action_loader
from ansible.plugins.strategy import StrategyBase
from ansible.template import Templar


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class StrategyModule(StrategyBase):

    noop_task = None

    def _replace_with_noop(self, target):
        if self.noop_task is None:
            raise AnsibleAssertionError('strategy.linear.StrategyModule.noop_task is None, need Task()')

        result = []
        for el in target:
            if isinstance(el, Task):
                result.append(self.noop_task)
            elif isinstance(el, Block):
                result.append(self._create_noop_block_from(el, el._parent))
        return result

    def _create_noop_block_from(self, original_block, parent):
        noop_block = Block(parent_block=parent)
        noop_block.block = self._replace_with_noop(original_block.block)
        noop_block.always = self._replace_with_noop(original_block.always)
        noop_block.rescue = self._replace_with_noop(original_block.rescue)

        return noop_block

    def _prepare_and_create_noop_block_from(self, original_block, parent, iterator):
        self.noop_task = Task()
        self.noop_task.action = 'meta'
        self.noop_task.args['_raw_params'] = 'noop'
        self.noop_task.set_loader(iterator._play._loader)

        return self._create_noop_block_from(original_block, parent)

    def _get_next_task_lockstep(self, hosts, iterator):
        '''
        Returns a list of (host, task) tuples, where the task may
        be a noop task to keep the iterator in lock step across
        all hosts.
        '''

        noop_task = Task()
        noop_task.action = 'meta'
        noop_task.args['_raw_params'] = 'noop'
        noop_task.set_loader(iterator._play._loader)

        host_tasks = {}
        display.debug("building list of next tasks for hosts")
        for host in hosts:
            host_tasks[host.name] = iterator.get_next_task_for_host(host, peek=True)
        display.debug("done building task lists")

        num_setups = 0
        num_tasks = 0
        num_rescue = 0
        num_always = 0

        display.debug("counting tasks in each state of execution")
        host_tasks_to_run = [(host, state_task)
                             for host, state_task in iteritems(host_tasks)
                             if state_task and state_task[1]]

        if host_tasks_to_run:
            try:
                lowest_cur_block = min(
                    (s.cur_block for h, (s, t) in host_tasks_to_run
                     if s.run_state != PlayIterator.ITERATING_COMPLETE))
            except ValueError:
                lowest_cur_block = None
        else:
            # empty host_tasks_to_run will just run till the end of the function
            # without ever touching lowest_cur_block
            lowest_cur_block = None

        for (k, v) in host_tasks_to_run:
            (s, t) = v

            if s.cur_block > lowest_cur_block:
                # Not the current block, ignore it
                continue

            if s.run_state == PlayIterator.ITERATING_SETUP:
                num_setups += 1
            elif s.run_state == PlayIterator.ITERATING_TASKS:
                num_tasks += 1
            elif s.run_state == PlayIterator.ITERATING_RESCUE:
                num_rescue += 1
            elif s.run_state == PlayIterator.ITERATING_ALWAYS:
                num_always += 1
        display.debug("done counting tasks in each state of execution:\n\tnum_setups: %s\n\tnum_tasks: %s\n\tnum_rescue: %s\n\tnum_always: %s" % (num_setups,
                                                                                                                                                  num_tasks,
                                                                                                                                                  num_rescue,
                                                                                                                                                  num_always))

        def _advance_selected_hosts(hosts, cur_block, cur_state):
            '''
            This helper returns the task for all hosts in the requested
            state, otherwise they get a noop dummy task. This also advances
            the state of the host, since the given states are determined
            while using peek=True.
            '''
            # we return the values in the order they were originally
            # specified in the given hosts array
            rvals = []
            display.debug("starting to advance hosts")
            for host in hosts:
                host_state_task = host_tasks.get(host.name)
                if host_state_task is None:
                    continue
                (s, t) = host_state_task
                if t is None:
                    continue
                if s.run_state == cur_state and s.cur_block == cur_block:
                    new_t = iterator.get_next_task_for_host(host)
                    rvals.append((host, t))
                else:
                    rvals.append((host, noop_task))
            display.debug("done advancing hosts to next task")
            return rvals

        # if any hosts are in ITERATING_SETUP, return the setup task
        # while all other hosts get a noop
        if num_setups:
            display.debug("advancing hosts in ITERATING_SETUP")
            return _advance_selected_hosts(hosts, lowest_cur_block, PlayIterator.ITERATING_SETUP)

        # if any hosts are in ITERATING_TASKS, return the next normal
        # task for these hosts, while all other hosts get a noop
        if num_tasks:
            display.debug("advancing hosts in ITERATING_TASKS")
            return _advance_selected_hosts(hosts, lowest_cur_block, PlayIterator.ITERATING_TASKS)

        # if any hosts are in ITERATING_RESCUE, return the next rescue
        # task for these hosts, while all other hosts get a noop
        if num_rescue:
            display.debug("advancing hosts in ITERATING_RESCUE")
            return _advance_selected_hosts(hosts, lowest_cur_block, PlayIterator.ITERATING_RESCUE)

        # if any hosts are in ITERATING_ALWAYS, return the next always
        # task for these hosts, while all other hosts get a noop
        if num_always:
            display.debug("advancing hosts in ITERATING_ALWAYS")
            return _advance_selected_hosts(hosts, lowest_cur_block, PlayIterator.ITERATING_ALWAYS)

        # at this point, everything must be ITERATING_COMPLETE, so we
        # return None for all hosts in the list
        display.debug("all hosts are done, so returning None's for all hosts")
        return [(host, None) for host in hosts]

    def run(self, iterator, play_context):
        '''
        The linear strategy is simple - get the next task and queue
        it for all hosts, then wait for the queue to drain before
        moving on to the next task
        '''

        # iteratate over each task, while there is one left to run
        result = self._tqm.RUN_OK
        work_to_do = True
        while work_to_do and not self._tqm._terminated:

            try:
                display.debug("getting the remaining hosts for this loop")
                hosts_left = self.get_hosts_left(iterator)
                display.debug("done getting the remaining hosts for this loop")

                # queue up this task for each host in the inventory
                callback_sent = False
                work_to_do = False

                host_results = []
                host_tasks = self._get_next_task_lockstep(hosts_left, iterator)

                # skip control
                skip_rest = False
                choose_step = True

                # flag set if task is set to any_errors_fatal
                any_errors_fatal = False

                results = []
                for (host, task) in host_tasks:
                    if not task:
                        continue

                    if self._tqm._terminated:
                        break

                    run_once = False
                    work_to_do = True

                    # test to see if the task across all hosts points to an action plugin which
                    # sets BYPASS_HOST_LOOP to true, or if it has run_once enabled. If so, we
                    # will only send this task to the first host in the list.

                    try:
                        action = action_loader.get(task.action, class_only=True)
                    except KeyError:
                        # we don't care here, because the action may simply not have a
                        # corresponding action plugin
                        action = None

                    # check to see if this task should be skipped, due to it being a member of a
                    # role which has already run (and whether that role allows duplicate execution)
                    if task._role and task._role.has_run(host):
                        # If there is no metadata, the default behavior is to not allow duplicates,
                        # if there is metadata, check to see if the allow_duplicates flag was set to true
                        if task._role._metadata is None or task._role._metadata and not task._role._metadata.allow_duplicates:
                            display.debug("'%s' skipped because role has already run" % task)
                            continue

                    if task.action == 'meta':
                        # for the linear strategy, we run meta tasks just once and for
                        # all hosts currently being iterated over rather than one host
                        results.extend(self._execute_meta(task, play_context, iterator, host))
                        if task.args.get('_raw_params', None) not in ('noop', 'reset_connection'):
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

                        display.debug("getting variables")
                        task_vars = self._variable_manager.get_vars(play=iterator._play, host=host, task=task)
                        self.add_tqm_variables(task_vars, play=iterator._play)
                        templar = Templar(loader=self._loader, variables=task_vars)
                        display.debug("done getting variables")

                        run_once = templar.template(task.run_once) or action and getattr(action, 'BYPASS_HOST_LOOP', False)

                        if (task.any_errors_fatal or run_once) and not task.ignore_errors:
                            any_errors_fatal = True

                        if not callback_sent:
                            display.debug("sending task start callback, copying the task so we can template it temporarily")
                            saved_name = task.name
                            display.debug("done copying, going to template now")
                            try:
                                task.name = to_text(templar.template(task.name, fail_on_undefined=False), nonstring='empty')
                                display.debug("done templating")
                            except:
                                # just ignore any errors during task name templating,
                                # we don't care if it just shows the raw name
                                display.debug("templating failed for some reason")
                            display.debug("here goes the callback...")
                            self._tqm.send_callback('v2_playbook_on_task_start', task, is_conditional=False)
                            task.name = saved_name
                            callback_sent = True
                            display.debug("sending task start callback")

                        self._blocked_hosts[host.get_name()] = True
                        self._queue_task(host, task, task_vars, play_context)
                        del task_vars

                    # if we're bypassing the host loop, break out now
                    if run_once:
                        break

                    results += self._process_pending_results(iterator, max_passes=max(1, int(len(self._tqm._workers) * 0.1)))

                # go to next host/task group
                if skip_rest:
                    continue

                display.debug("done queuing things up, now waiting for results queue to drain")
                if self._pending_results > 0:
                    results += self._wait_on_pending_results(iterator)

                host_results.extend(results)

                self.update_active_connections(results)

                try:
                    included_files = IncludedFile.process_include_results(
                        host_results,
                        iterator=iterator,
                        loader=self._loader,
                        variable_manager=self._variable_manager
                    )
                except AnsibleError as e:
                    # this is a fatal error, so we abort here regardless of block state
                    return self._tqm.RUN_ERROR

                include_failure = False
                if len(included_files) > 0:
                    display.debug("we have included files to process")

                    display.debug("generating all_blocks data")
                    all_blocks = dict((host, []) for host in hosts_left)
                    display.debug("done generating all_blocks data")
                    for included_file in included_files:
                        display.debug("processing included file: %s" % included_file._filename)
                        # included hosts get the task list while those excluded get an equal-length
                        # list of noop tasks, to make sure that they continue running in lock-step
                        try:
                            if included_file._is_role:
                                new_ir = self._copy_included_file(included_file)

                                new_blocks, handler_blocks = new_ir.get_block_list(
                                    play=iterator._play,
                                    variable_manager=self._variable_manager,
                                    loader=self._loader,
                                )
                                self._tqm.update_handler_list([handler for handler_block in handler_blocks for handler in handler_block.block])
                            else:
                                new_blocks = self._load_included_file(included_file, iterator=iterator)

                            display.debug("iterating over new_blocks loaded from include file")
                            for new_block in new_blocks:
                                task_vars = self._variable_manager.get_vars(
                                    play=iterator._play,
                                    task=new_block._parent
                                )
                                display.debug("filtering new block on tags")
                                final_block = new_block.filter_tagged_tasks(play_context, task_vars)
                                display.debug("done filtering new block on tags")

                                noop_block = self._prepare_and_create_noop_block_from(final_block, task._parent, iterator)

                                for host in hosts_left:
                                    if host in included_file._hosts:
                                        all_blocks[host].append(final_block)
                                    else:
                                        all_blocks[host].append(noop_block)
                            display.debug("done iterating over new_blocks loaded from include file")

                        except AnsibleError as e:
                            for host in included_file._hosts:
                                self._tqm._failed_hosts[host.name] = True
                                iterator.mark_host_failed(host)
                            display.error(to_text(e), wrap_text=False)
                            include_failure = True
                            continue

                    # finally go through all of the hosts and append the
                    # accumulated blocks to their list of tasks
                    display.debug("extending task lists for all hosts with included blocks")

                    for host in hosts_left:
                        iterator.add_tasks(host, all_blocks[host])

                    display.debug("done extending task lists")
                    display.debug("done processing included files")

                display.debug("results queue empty")

                display.debug("checking for any_errors_fatal")
                failed_hosts = []
                unreachable_hosts = []
                for res in results:
                    # execute_meta() does not set 'failed' in the TaskResult
                    # so we skip checking it with the meta tasks and look just at the iterator
                    if (res.is_failed() or res._task.action == 'meta') and iterator.is_failed(res._host):
                        failed_hosts.append(res._host.name)
                    elif res.is_unreachable():
                        unreachable_hosts.append(res._host.name)

                # if any_errors_fatal and we had an error, mark all hosts as failed
                if any_errors_fatal and (len(failed_hosts) > 0 or len(unreachable_hosts) > 0):
                    dont_fail_states = frozenset([iterator.ITERATING_RESCUE, iterator.ITERATING_ALWAYS])
                    for host in hosts_left:
                        (s, _) = iterator.get_next_task_for_host(host, peek=True)
                        if s.run_state not in dont_fail_states or \
                           s.run_state == iterator.ITERATING_RESCUE and s.fail_state & iterator.FAILED_RESCUE != 0:
                            self._tqm._failed_hosts[host.name] = True
                            result |= self._tqm.RUN_FAILED_BREAK_PLAY
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
