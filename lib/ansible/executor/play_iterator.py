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

import fnmatch

from ansible import constants as C
from ansible.module_utils.six import iteritems
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.playbook.block import Block
from ansible.playbook.task import Task
from ansible.utils.display import Display


display = Display()


__all__ = ['PlayIterator']


class HostState:
    def __init__(self, blocks):
        self._blocks = blocks[:]

        self.cur_block = 0
        self.cur_regular_task = 0
        self.cur_rescue_task = 0
        self.cur_always_task = 0
        self.cur_dep_chain = None
        self.run_state = PlayIterator.ITERATING_SETUP
        self.fail_state = PlayIterator.FAILED_NONE
        self.pending_setup = False
        self.tasks_child_state = None
        self.rescue_child_state = None
        self.always_child_state = None
        self.did_rescue = False
        self.did_start_at_task = False

    def __repr__(self):
        return "HostState(%r)" % self._blocks

    def __str__(self):
        def _run_state_to_string(n):
            states = ["ITERATING_SETUP", "ITERATING_TASKS", "ITERATING_RESCUE", "ITERATING_ALWAYS", "ITERATING_COMPLETE"]
            try:
                return states[n]
            except IndexError:
                return "UNKNOWN STATE"

        def _failed_state_to_string(n):
            states = {1: "FAILED_SETUP", 2: "FAILED_TASKS", 4: "FAILED_RESCUE", 8: "FAILED_ALWAYS"}
            if n == 0:
                return "FAILED_NONE"
            else:
                ret = []
                for i in (1, 2, 4, 8):
                    if n & i:
                        ret.append(states[i])
                return "|".join(ret)

        return ("HOST STATE: block=%d, task=%d, rescue=%d, always=%d, run_state=%s, fail_state=%s, pending_setup=%s, tasks child state? (%s), "
                "rescue child state? (%s), always child state? (%s), did rescue? %s, did start at task? %s" % (
                    self.cur_block,
                    self.cur_regular_task,
                    self.cur_rescue_task,
                    self.cur_always_task,
                    _run_state_to_string(self.run_state),
                    _failed_state_to_string(self.fail_state),
                    self.pending_setup,
                    self.tasks_child_state,
                    self.rescue_child_state,
                    self.always_child_state,
                    self.did_rescue,
                    self.did_start_at_task,
                ))

    def __eq__(self, other):
        if not isinstance(other, HostState):
            return False

        for attr in ('_blocks', 'cur_block', 'cur_regular_task', 'cur_rescue_task', 'cur_always_task',
                     'run_state', 'fail_state', 'pending_setup', 'cur_dep_chain',
                     'tasks_child_state', 'rescue_child_state', 'always_child_state'):
            if getattr(self, attr) != getattr(other, attr):
                return False

        return True

    def get_current_block(self):
        return self._blocks[self.cur_block]

    def copy(self):
        new_state = HostState(self._blocks)
        new_state.cur_block = self.cur_block
        new_state.cur_regular_task = self.cur_regular_task
        new_state.cur_rescue_task = self.cur_rescue_task
        new_state.cur_always_task = self.cur_always_task
        new_state.run_state = self.run_state
        new_state.fail_state = self.fail_state
        new_state.pending_setup = self.pending_setup
        new_state.did_rescue = self.did_rescue
        new_state.did_start_at_task = self.did_start_at_task
        if self.cur_dep_chain is not None:
            new_state.cur_dep_chain = self.cur_dep_chain[:]
        if self.tasks_child_state is not None:
            new_state.tasks_child_state = self.tasks_child_state.copy()
        if self.rescue_child_state is not None:
            new_state.rescue_child_state = self.rescue_child_state.copy()
        if self.always_child_state is not None:
            new_state.always_child_state = self.always_child_state.copy()
        return new_state


class PlayIterator:

    # the primary running states for the play iteration
    ITERATING_SETUP = 0
    ITERATING_TASKS = 1
    ITERATING_RESCUE = 2
    ITERATING_ALWAYS = 3
    ITERATING_COMPLETE = 4

    # the failure states for the play iteration, which are powers
    # of 2 as they may be or'ed together in certain circumstances
    FAILED_NONE = 0
    FAILED_SETUP = 1
    FAILED_TASKS = 2
    FAILED_RESCUE = 4
    FAILED_ALWAYS = 8

    def __init__(self, inventory, play, play_context, variable_manager, all_vars, start_at_done=False):
        self._play = play
        self._blocks = []
        self._variable_manager = variable_manager

        # Default options to gather
        gather_subset = self._play.gather_subset
        gather_timeout = self._play.gather_timeout
        fact_path = self._play.fact_path

        setup_block = Block(play=self._play)
        # Gathering facts with run_once would copy the facts from one host to
        # the others.
        setup_block.run_once = False
        setup_task = Task(block=setup_block)
        setup_task.action = 'gather_facts'
        setup_task.name = 'Gathering Facts'
        setup_task.args = {
            'gather_subset': gather_subset,
        }

        # Unless play is specifically tagged, gathering should 'always' run
        if not self._play.tags:
            setup_task.tags = ['always']

        if gather_timeout:
            setup_task.args['gather_timeout'] = gather_timeout
        if fact_path:
            setup_task.args['fact_path'] = fact_path
        setup_task.set_loader(self._play._loader)
        # short circuit fact gathering if the entire playbook is conditional
        if self._play._included_conditional is not None:
            setup_task.when = self._play._included_conditional[:]
        setup_block.block = [setup_task]

        setup_block = setup_block.filter_tagged_tasks(all_vars)
        self._blocks.append(setup_block)

        for block in self._play.compile():
            new_block = block.filter_tagged_tasks(all_vars)
            if new_block.has_tasks():
                self._blocks.append(new_block)

        self._host_states = {}
        start_at_matched = False
        batch = inventory.get_hosts(self._play.hosts, order=self._play.order)
        self.batch_size = len(batch)
        for host in batch:
            self._host_states[host.name] = HostState(blocks=self._blocks)
            # if we're looking to start at a specific task, iterate through
            # the tasks for this host until we find the specified task
            if play_context.start_at_task is not None and not start_at_done:
                while True:
                    (s, task) = self.get_next_task_for_host(host, peek=True)
                    if s.run_state == self.ITERATING_COMPLETE:
                        break
                    if task.name == play_context.start_at_task or (task.name and fnmatch.fnmatch(task.name, play_context.start_at_task)) or \
                       task.get_name() == play_context.start_at_task or fnmatch.fnmatch(task.get_name(), play_context.start_at_task):
                        start_at_matched = True
                        break
                    else:
                        self.get_next_task_for_host(host)

                # finally, reset the host's state to ITERATING_SETUP
                if start_at_matched:
                    self._host_states[host.name].did_start_at_task = True
                    self._host_states[host.name].run_state = self.ITERATING_SETUP

        if start_at_matched:
            # we have our match, so clear the start_at_task field on the
            # play context to flag that we've started at a task (and future
            # plays won't try to advance)
            play_context.start_at_task = None

    def get_host_state(self, host):
        # Since we're using the PlayIterator to carry forward failed hosts,
        # in the event that a previous host was not in the current inventory
        # we create a stub state for it now
        if host.name not in self._host_states:
            self._host_states[host.name] = HostState(blocks=[])

        return self._host_states[host.name].copy()

    def cache_block_tasks(self, block):
        # now a noop, we've changed the way we do caching and finding of
        # original task entries, but just in case any 3rd party strategies
        # are using this we're leaving it here for now
        return

    def get_next_task_for_host(self, host, peek=False):

        display.debug("getting the next task for host %s" % host.name)
        s = self.get_host_state(host)

        task = None
        if s.run_state == self.ITERATING_COMPLETE:
            display.debug("host %s is done iterating, returning" % host.name)
            return (s, None)

        (s, task) = self._get_next_task_from_state(s, host=host)

        if not peek:
            self._host_states[host.name] = s

        display.debug("done getting next task for host %s" % host.name)
        display.debug(" ^ task is: %s" % task)
        display.debug(" ^ state is: %s" % s)
        return (s, task)

    def _get_next_task_from_state(self, state, host):

        task = None

        # try and find the next task, given the current state.
        while True:
            # try to get the current block from the list of blocks, and
            # if we run past the end of the list we know we're done with
            # this block
            try:
                block = state._blocks[state.cur_block]
            except IndexError:
                state.run_state = self.ITERATING_COMPLETE
                return (state, None)

            if state.run_state == self.ITERATING_SETUP:
                # First, we check to see if we were pending setup. If not, this is
                # the first trip through ITERATING_SETUP, so we set the pending_setup
                # flag and try to determine if we do in fact want to gather facts for
                # the specified host.
                if not state.pending_setup:
                    state.pending_setup = True

                    # Gather facts if the default is 'smart' and we have not yet
                    # done it for this host; or if 'explicit' and the play sets
                    # gather_facts to True; or if 'implicit' and the play does
                    # NOT explicitly set gather_facts to False.

                    gathering = C.DEFAULT_GATHERING
                    implied = self._play.gather_facts is None or boolean(self._play.gather_facts, strict=False)

                    if (gathering == 'implicit' and implied) or \
                       (gathering == 'explicit' and boolean(self._play.gather_facts, strict=False)) or \
                       (gathering == 'smart' and implied and not (self._variable_manager._fact_cache.get(host.name, {}).get('_ansible_facts_gathered', False))):
                        # The setup block is always self._blocks[0], as we inject it
                        # during the play compilation in __init__ above.
                        setup_block = self._blocks[0]
                        if setup_block.has_tasks() and len(setup_block.block) > 0:
                            task = setup_block.block[0]
                else:
                    # This is the second trip through ITERATING_SETUP, so we clear
                    # the flag and move onto the next block in the list while setting
                    # the run state to ITERATING_TASKS
                    state.pending_setup = False

                    state.run_state = self.ITERATING_TASKS
                    if not state.did_start_at_task:
                        state.cur_block += 1
                        state.cur_regular_task = 0
                        state.cur_rescue_task = 0
                        state.cur_always_task = 0
                        state.tasks_child_state = None
                        state.rescue_child_state = None
                        state.always_child_state = None

            elif state.run_state == self.ITERATING_TASKS:
                # clear the pending setup flag, since we're past that and it didn't fail
                if state.pending_setup:
                    state.pending_setup = False

                # First, we check for a child task state that is not failed, and if we
                # have one recurse into it for the next task. If we're done with the child
                # state, we clear it and drop back to getting the next task from the list.
                if state.tasks_child_state:
                    (state.tasks_child_state, task) = self._get_next_task_from_state(state.tasks_child_state, host=host)
                    if self._check_failed_state(state.tasks_child_state):
                        # failed child state, so clear it and move into the rescue portion
                        state.tasks_child_state = None
                        self._set_failed_state(state)
                    else:
                        # get the next task recursively
                        if task is None or state.tasks_child_state.run_state == self.ITERATING_COMPLETE:
                            # we're done with the child state, so clear it and continue
                            # back to the top of the loop to get the next task
                            state.tasks_child_state = None
                            continue
                else:
                    # First here, we check to see if we've failed anywhere down the chain
                    # of states we have, and if so we move onto the rescue portion. Otherwise,
                    # we check to see if we've moved past the end of the list of tasks. If so,
                    # we move into the always portion of the block, otherwise we get the next
                    # task from the list.
                    if self._check_failed_state(state):
                        state.run_state = self.ITERATING_RESCUE
                    elif state.cur_regular_task >= len(block.block):
                        state.run_state = self.ITERATING_ALWAYS
                    else:
                        task = block.block[state.cur_regular_task]
                        # if the current task is actually a child block, create a child
                        # state for us to recurse into on the next pass
                        if isinstance(task, Block):
                            state.tasks_child_state = HostState(blocks=[task])
                            state.tasks_child_state.run_state = self.ITERATING_TASKS
                            # since we've created the child state, clear the task
                            # so we can pick up the child state on the next pass
                            task = None
                        state.cur_regular_task += 1

            elif state.run_state == self.ITERATING_RESCUE:
                # The process here is identical to ITERATING_TASKS, except instead
                # we move into the always portion of the block.
                if host.name in self._play._removed_hosts:
                    self._play._removed_hosts.remove(host.name)

                if state.rescue_child_state:
                    (state.rescue_child_state, task) = self._get_next_task_from_state(state.rescue_child_state, host=host)
                    if self._check_failed_state(state.rescue_child_state):
                        state.rescue_child_state = None
                        self._set_failed_state(state)
                    else:
                        if task is None or state.rescue_child_state.run_state == self.ITERATING_COMPLETE:
                            state.rescue_child_state = None
                            continue
                else:
                    if state.fail_state & self.FAILED_RESCUE == self.FAILED_RESCUE:
                        state.run_state = self.ITERATING_ALWAYS
                    elif state.cur_rescue_task >= len(block.rescue):
                        if len(block.rescue) > 0:
                            state.fail_state = self.FAILED_NONE
                        state.run_state = self.ITERATING_ALWAYS
                        state.did_rescue = True
                    else:
                        task = block.rescue[state.cur_rescue_task]
                        if isinstance(task, Block):
                            state.rescue_child_state = HostState(blocks=[task])
                            state.rescue_child_state.run_state = self.ITERATING_TASKS
                            task = None
                        state.cur_rescue_task += 1

            elif state.run_state == self.ITERATING_ALWAYS:
                # And again, the process here is identical to ITERATING_TASKS, except
                # instead we either move onto the next block in the list, or we set the
                # run state to ITERATING_COMPLETE in the event of any errors, or when we
                # have hit the end of the list of blocks.
                if state.always_child_state:
                    (state.always_child_state, task) = self._get_next_task_from_state(state.always_child_state, host=host)
                    if self._check_failed_state(state.always_child_state):
                        state.always_child_state = None
                        self._set_failed_state(state)
                    else:
                        if task is None or state.always_child_state.run_state == self.ITERATING_COMPLETE:
                            state.always_child_state = None
                            continue
                else:
                    if state.cur_always_task >= len(block.always):
                        if state.fail_state != self.FAILED_NONE:
                            state.run_state = self.ITERATING_COMPLETE
                        else:
                            state.cur_block += 1
                            state.cur_regular_task = 0
                            state.cur_rescue_task = 0
                            state.cur_always_task = 0
                            state.run_state = self.ITERATING_TASKS
                            state.tasks_child_state = None
                            state.rescue_child_state = None
                            state.always_child_state = None
                            state.did_rescue = False
                    else:
                        task = block.always[state.cur_always_task]
                        if isinstance(task, Block):
                            state.always_child_state = HostState(blocks=[task])
                            state.always_child_state.run_state = self.ITERATING_TASKS
                            task = None
                        state.cur_always_task += 1

            elif state.run_state == self.ITERATING_COMPLETE:
                return (state, None)

            # if something above set the task, break out of the loop now
            if task:
                break

        return (state, task)

    def _set_failed_state(self, state):
        if state.run_state == self.ITERATING_SETUP:
            state.fail_state |= self.FAILED_SETUP
            state.run_state = self.ITERATING_COMPLETE
        elif state.run_state == self.ITERATING_TASKS:
            if state.tasks_child_state is not None:
                state.tasks_child_state = self._set_failed_state(state.tasks_child_state)
            else:
                state.fail_state |= self.FAILED_TASKS
                if state._blocks[state.cur_block].rescue:
                    state.run_state = self.ITERATING_RESCUE
                elif state._blocks[state.cur_block].always:
                    state.run_state = self.ITERATING_ALWAYS
                else:
                    state.run_state = self.ITERATING_COMPLETE
        elif state.run_state == self.ITERATING_RESCUE:
            if state.rescue_child_state is not None:
                state.rescue_child_state = self._set_failed_state(state.rescue_child_state)
            else:
                state.fail_state |= self.FAILED_RESCUE
                if state._blocks[state.cur_block].always:
                    state.run_state = self.ITERATING_ALWAYS
                else:
                    state.run_state = self.ITERATING_COMPLETE
        elif state.run_state == self.ITERATING_ALWAYS:
            if state.always_child_state is not None:
                state.always_child_state = self._set_failed_state(state.always_child_state)
            else:
                state.fail_state |= self.FAILED_ALWAYS
                state.run_state = self.ITERATING_COMPLETE
        return state

    def mark_host_failed(self, host):
        s = self.get_host_state(host)
        display.debug("marking host %s failed, current state: %s" % (host, s))
        s = self._set_failed_state(s)
        display.debug("^ failed state is now: %s" % s)
        self._host_states[host.name] = s
        self._play._removed_hosts.append(host.name)

    def get_failed_hosts(self):
        return dict((host, True) for (host, state) in iteritems(self._host_states) if self._check_failed_state(state))

    def _check_failed_state(self, state):
        if state is None:
            return False
        elif state.run_state == self.ITERATING_RESCUE and self._check_failed_state(state.rescue_child_state):
            return True
        elif state.run_state == self.ITERATING_ALWAYS and self._check_failed_state(state.always_child_state):
            return True
        elif state.fail_state != self.FAILED_NONE:
            if state.run_state == self.ITERATING_RESCUE and state.fail_state & self.FAILED_RESCUE == 0:
                return False
            elif state.run_state == self.ITERATING_ALWAYS and state.fail_state & self.FAILED_ALWAYS == 0:
                return False
            else:
                return not (state.did_rescue and state.fail_state & self.FAILED_ALWAYS == 0)
        elif state.run_state == self.ITERATING_TASKS and self._check_failed_state(state.tasks_child_state):
            cur_block = state._blocks[state.cur_block]
            if len(cur_block.rescue) > 0 and state.fail_state & self.FAILED_RESCUE == 0:
                return False
            else:
                return True
        return False

    def is_failed(self, host):
        s = self.get_host_state(host)
        return self._check_failed_state(s)

    def get_active_state(self, state):
        '''
        Finds the active state, recursively if necessary when there are child states.
        '''
        if state.run_state == self.ITERATING_TASKS and state.tasks_child_state is not None:
            return self.get_active_state(state.tasks_child_state)
        elif state.run_state == self.ITERATING_RESCUE and state.rescue_child_state is not None:
            return self.get_active_state(state.rescue_child_state)
        elif state.run_state == self.ITERATING_ALWAYS and state.always_child_state is not None:
            return self.get_active_state(state.always_child_state)
        return state

    def is_any_block_rescuing(self, state):
        '''
        Given the current HostState state, determines if the current block, or any child blocks,
        are in rescue mode.
        '''
        if state.run_state == self.ITERATING_RESCUE:
            return True
        if state.tasks_child_state is not None:
            return self.is_any_block_rescuing(state.tasks_child_state)
        return False

    def get_original_task(self, host, task):
        # now a noop because we've changed the way we do caching
        return (None, None)

    def _insert_tasks_into_state(self, state, task_list):
        # if we've failed at all, or if the task list is empty, just return the current state
        if state.fail_state != self.FAILED_NONE and state.run_state not in (self.ITERATING_RESCUE, self.ITERATING_ALWAYS) or not task_list:
            return state

        if state.run_state == self.ITERATING_TASKS:
            if state.tasks_child_state:
                state.tasks_child_state = self._insert_tasks_into_state(state.tasks_child_state, task_list)
            else:
                target_block = state._blocks[state.cur_block].copy()
                before = target_block.block[:state.cur_regular_task]
                after = target_block.block[state.cur_regular_task:]
                target_block.block = before + task_list + after
                state._blocks[state.cur_block] = target_block
        elif state.run_state == self.ITERATING_RESCUE:
            if state.rescue_child_state:
                state.rescue_child_state = self._insert_tasks_into_state(state.rescue_child_state, task_list)
            else:
                target_block = state._blocks[state.cur_block].copy()
                before = target_block.rescue[:state.cur_rescue_task]
                after = target_block.rescue[state.cur_rescue_task:]
                target_block.rescue = before + task_list + after
                state._blocks[state.cur_block] = target_block
        elif state.run_state == self.ITERATING_ALWAYS:
            if state.always_child_state:
                state.always_child_state = self._insert_tasks_into_state(state.always_child_state, task_list)
            else:
                target_block = state._blocks[state.cur_block].copy()
                before = target_block.always[:state.cur_always_task]
                after = target_block.always[state.cur_always_task:]
                target_block.always = before + task_list + after
                state._blocks[state.cur_block] = target_block
        return state

    def add_tasks(self, host, task_list):
        self._host_states[host.name] = self._insert_tasks_into_state(self.get_host_state(host), task_list)
