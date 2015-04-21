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

from ansible.errors import AnsibleError
from ansible.executor.play_iterator import PlayIterator
from ansible.playbook.block import Block
from ansible.playbook.task import Task
from ansible.plugins import action_loader
from ansible.plugins.strategies import StrategyBase
from ansible.utils.debug import debug

class StrategyModule(StrategyBase):

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
        for host in hosts:
            host_tasks[host.name] = iterator.get_next_task_for_host(host, peek=True)

        num_setups = 0
        num_tasks  = 0
        num_rescue = 0
        num_always = 0

        lowest_cur_block = len(iterator._blocks)

        for (k, v) in host_tasks.iteritems():
            if v is None:
                continue

            (s, t) = v
            if s.cur_block < lowest_cur_block and s.run_state != PlayIterator.ITERATING_COMPLETE:
                lowest_cur_block = s.cur_block

            if s.run_state == PlayIterator.ITERATING_SETUP:
                num_setups += 1
            elif s.run_state == PlayIterator.ITERATING_TASKS:
                num_tasks += 1
            elif s.run_state == PlayIterator.ITERATING_RESCUE:
                num_rescue += 1
            elif s.run_state == PlayIterator.ITERATING_ALWAYS:
                num_always += 1

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
            for host in hosts:
                (s, t) = host_tasks[host.name]
                if s.run_state == cur_state and s.cur_block == cur_block:
                    new_t = iterator.get_next_task_for_host(host)
                    #if new_t != t:
                    #    raise AnsibleError("iterator error, wtf?")
                    rvals.append((host, t))
                else:
                    rvals.append((host, noop_task))
            return rvals

        # if any hosts are in ITERATING_SETUP, return the setup task
        # while all other hosts get a noop
        if num_setups:
            return _advance_selected_hosts(hosts, lowest_cur_block, PlayIterator.ITERATING_SETUP)

        # if any hosts are in ITERATING_TASKS, return the next normal
        # task for these hosts, while all other hosts get a noop
        if num_tasks:
            return _advance_selected_hosts(hosts, lowest_cur_block, PlayIterator.ITERATING_TASKS)

        # if any hosts are in ITERATING_RESCUE, return the next rescue
        # task for these hosts, while all other hosts get a noop
        if num_rescue:
            return _advance_selected_hosts(hosts, lowest_cur_block, PlayIterator.ITERATING_RESCUE)

        # if any hosts are in ITERATING_ALWAYS, return the next always
        # task for these hosts, while all other hosts get a noop
        if num_always:
            return _advance_selected_hosts(hosts, lowest_cur_block, PlayIterator.ITERATING_ALWAYS)

        # at this point, everything must be ITERATING_COMPLETE, so we
        # return None for all hosts in the list
        return [(host, None) for host in hosts]


    def run(self, iterator, connection_info):
        '''
        The linear strategy is simple - get the next task and queue
        it for all hosts, then wait for the queue to drain before
        moving on to the next task
        '''

        result = True

        # iteratate over each task, while there is one left to run
        work_to_do = True
        while work_to_do and not self._tqm._terminated:

            try:
                debug("getting the remaining hosts for this loop")
                self._tqm._failed_hosts = iterator.get_failed_hosts()
                hosts_left = self.get_hosts_remaining(iterator._play)
                debug("done getting the remaining hosts for this loop")
                if len(hosts_left) == 0:
                    debug("out of hosts to run on")
                    self._tqm.send_callback('v2_playbook_on_no_hosts_remaining')
                    result = False
                    break

                # queue up this task for each host in the inventory
                callback_sent = False
                work_to_do = False

                host_results = []
                host_tasks = self._get_next_task_lockstep(hosts_left, iterator)
                for (host, task) in host_tasks:
                    if not task:
                        continue

                    run_once = False
                    work_to_do = True

                    # test to see if the task across all hosts points to an action plugin which
                    # sets BYPASS_HOST_LOOP to true, or if it has run_once enabled. If so, we
                    # will only send this task to the first host in the list.

                    try:
                        action = action_loader.get(task.action, class_only=True)
                        if task.run_once or getattr(action, 'BYPASS_HOST_LOOP', False):
                            run_once = True
                    except KeyError:
                        # we don't care here, because the action may simply not have a
                        # corresponding action plugin
                        pass

                    debug("getting variables")
                    task_vars = self._variable_manager.get_vars(loader=self._loader, play=iterator._play, host=host, task=task)
                    debug("done getting variables")

                    # check to see if this task should be skipped, due to it being a member of a
                    # role which has already run (and whether that role allows duplicate execution)
                    if task._role and task._role.has_run():
                        # If there is no metadata, the default behavior is to not allow duplicates,
                        # if there is metadata, check to see if the allow_duplicates flag was set to true
                        if task._role._metadata is None or task._role._metadata and not task._role._metadata.allow_duplicates:
                            debug("'%s' skipped because role has already run" % task)
                            continue

                    if task.action == 'meta':
                        # meta tasks store their args in the _raw_params field of args,
                        # since they do not use k=v pairs, so get that
                        meta_action = task.args.get('_raw_params')
                        if meta_action == 'noop':
                            # FIXME: issue a callback for the noop here?
                            continue
                        elif meta_action == 'flush_handlers':
                            self.run_handlers(iterator, connection_info)
                        else:
                            raise AnsibleError("invalid meta action requested: %s" % meta_action, obj=task._ds)
                    else:
                        if not callback_sent:
                            self._tqm.send_callback('v2_playbook_on_task_start', task, is_conditional=False)
                            callback_sent = True

                        self._blocked_hosts[host.get_name()] = True
                        self._queue_task(host, task, task_vars, connection_info)

                    results = self._process_pending_results(iterator)
                    host_results.extend(results)

                    # if we're bypassing the host loop, break out now
                    if run_once:
                        break

                debug("done queuing things up, now waiting for results queue to drain")
                results = self._wait_on_pending_results(iterator)
                host_results.extend(results)

                # FIXME: this needs to be somewhere else
                class IncludedFile:
                    def __init__(self, filename, args, task):
                        self._filename = filename
                        self._args     = args
                        self._task     = task
                        self._hosts    = []
                    def add_host(self, host):
                        if host not in self._hosts:
                            self._hosts.append(host)
                    def __eq__(self, other):
                        return other._filename == self._filename and other._args == self._args
                    def __repr__(self):
                        return "%s (%s): %s" % (self._filename, self._args, self._hosts)

                # FIXME: this should also be moved to the base class in a method
                included_files = []
                for res in host_results:
                    if res._task.action == 'include':
                        if res._task.loop:
                            include_results = res._result['results']
                        else:
                            include_results = [ res._result ]

                        for include_result in include_results:
                            # if the task result was skipped or failed, continue
                            if 'skipped' in include_result and include_result['skipped'] or 'failed' in include_result:
                                continue

                            original_task = iterator.get_original_task(res._host, res._task)
                            if original_task and original_task._role:
                                include_file = self._loader.path_dwim_relative(original_task._role._role_path, 'tasks', include_result['include'])
                            else:
                                include_file = self._loader.path_dwim(res._task.args.get('_raw_params'))

                            include_variables = include_result.get('include_variables', dict())
                            if 'item' in include_result:
                                include_variables['item'] = include_result['item']

                            inc_file = IncludedFile(include_file, include_variables, original_task)

                            try:
                                pos = included_files.index(inc_file)
                                inc_file = included_files[pos]
                            except ValueError:
                                included_files.append(inc_file)

                            inc_file.add_host(res._host)

                # FIXME: should this be moved into the iterator class? Main downside would be
                #        that accessing the TQM's callback member would be more difficult, if
                #        we do want to send callbacks from here
                if len(included_files) > 0:
                    noop_task = Task()
                    noop_task.action = 'meta'
                    noop_task.args['_raw_params'] = 'noop'
                    noop_task.set_loader(iterator._play._loader)

                    all_blocks = dict((host, []) for host in hosts_left)
                    for included_file in included_files:
                        # included hosts get the task list while those excluded get an equal-length
                        # list of noop tasks, to make sure that they continue running in lock-step
                        try:
                            new_blocks = self._load_included_file(included_file)
                        except AnsibleError, e:
                            for host in included_file._hosts:
                                iterator.mark_host_failed(host)
                            # FIXME: callback here?
                            print(e)

                        for new_block in new_blocks:
                            noop_block = Block(parent_block=task._block)
                            noop_block.block  = [noop_task for t in new_block.block]
                            noop_block.always = [noop_task for t in new_block.always]
                            noop_block.rescue = [noop_task for t in new_block.rescue]
                            for host in hosts_left:
                                if host in included_file._hosts:
                                    all_blocks[host].append(new_block)
                                else:
                                    all_blocks[host].append(noop_block)

                    for host in hosts_left:
                        iterator.add_tasks(host, all_blocks[host])

                debug("results queue empty")
            except (IOError, EOFError), e:
                debug("got IOError/EOFError in task loop: %s" % e)
                # most likely an abort, return failed
                return 1

        # run the base class run() method, which executes the cleanup function
        # and runs any outstanding handlers which have been triggered

        return super(StrategyModule, self).run(iterator, connection_info, result)

