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

from ansible.compat.six import iteritems

from ansible import constants as C

from ansible.errors import AnsibleError
from ansible.playbook.block import Block
from ansible.playbook.task import Task

from ansible.utils.boolean import boolean

__all__ = ['PlayIterator']

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class HostState:
    def __init__(self, blocks):
        self._blocks          = blocks[:]

        self.cur_block          = 0
        self.cur_regular_task   = 0
        self.cur_rescue_task    = 0
        self.cur_always_task    = 0
        self.cur_role           = None
        self.cur_dep_chain      = None
        self.run_state          = PlayIterator.ITERATING_SETUP
        self.fail_state         = PlayIterator.FAILED_NONE
        self.pending_setup      = False
        self.tasks_child_state  = None
        self.rescue_child_state = None
        self.always_child_state = None

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
            states = {1:"FAILED_SETUP", 2:"FAILED_TASKS", 4:"FAILED_RESCUE", 8:"FAILED_ALWAYS"}
            if n == 0:
                return "FAILED_NONE"
            else:
                ret = []
                for i in (1, 2, 4, 8):
                    if n & i:
                        ret.append(states[i])
                return "|".join(ret)

        return "HOST STATE: block=%d, task=%d, rescue=%d, always=%d, role=%s, run_state=%s, fail_state=%s, pending_setup=%s, tasks child state? %s, rescue child state? %s, always child state? %s" % (
            self.cur_block,
            self.cur_regular_task,
            self.cur_rescue_task,
            self.cur_always_task,
            self.cur_role,
            _run_state_to_string(self.run_state),
            _failed_state_to_string(self.fail_state),
            self.pending_setup,
            self.tasks_child_state,
            self.rescue_child_state,
            self.always_child_state,
        )

    def __eq__(self, other):
        if not isinstance(other, HostState):
            return False

        for attr in (
            '_blocks', 'cur_block', 'cur_regular_task', 'cur_rescue_task', 'cur_always_task',
            'cur_role', 'run_state', 'fail_state', 'pending_setup', 'cur_dep_chain',
            'tasks_child_state', 'rescue_child_state', 'always_child_state'
            ):
            if getattr(self, attr) != getattr(other, attr):
                return False

        return True

    def get_current_block(self):
        return self._blocks[self.cur_block]

    def copy(self):
        new_state = HostState(self._blocks)
        new_state.cur_block        = self.cur_block
        new_state.cur_regular_task = self.cur_regular_task
        new_state.cur_rescue_task  = self.cur_rescue_task
        new_state.cur_always_task  = self.cur_always_task
        new_state.cur_role         = self.cur_role
        new_state.run_state        = self.run_state
        new_state.fail_state       = self.fail_state
        new_state.pending_setup    = self.pending_setup
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
    ITERATING_SETUP    = 0
    ITERATING_TASKS    = 1
    ITERATING_RESCUE   = 2
    ITERATING_ALWAYS   = 3
    ITERATING_COMPLETE = 4

    # the failure states for the play iteration, which are powers
    # of 2 as they may be or'ed together in certain circumstances
    FAILED_NONE        = 0
    FAILED_SETUP       = 1
    FAILED_TASKS       = 2
    FAILED_RESCUE      = 4
    FAILED_ALWAYS      = 8

    def __init__(self, inventory, play, play_context, variable_manager, all_vars, start_at_done=False):
        self._play = play
        self._blocks = []

        setup_block = Block(play=self._play)
        setup_task = Task(block=setup_block)
        setup_task.action = 'setup'
        setup_task.tags   = ['always']
        setup_task.args   = {}
        setup_task.set_loader(self._play._loader)
        setup_block.block = [setup_task]

        setup_block = setup_block.filter_tagged_tasks(play_context, all_vars)
        self._blocks.append(setup_block)

        for block in self._play.compile():
            new_block = block.filter_tagged_tasks(play_context, all_vars)
            if new_block.has_tasks():
                self._blocks.append(new_block)

        self._host_states = {}
        start_at_matched = False
        for host in inventory.get_hosts(self._play.hosts):
            self._host_states[host.name] = HostState(blocks=self._blocks)
            # if the host's name is in the variable manager's fact cache, then set
            # its _gathered_facts flag to true for smart gathering tests later
            if host.name in variable_manager._fact_cache:
                host._gathered_facts = True
            # if we're looking to start at a specific task, iterate through
            # the tasks for this host until we find the specified task
            if play_context.start_at_task is not None and not start_at_done:
                while True:
                    (s, task) = self.get_next_task_for_host(host, peek=True)
                    if s.run_state == self.ITERATING_COMPLETE:
                        break
                    if task.name == play_context.start_at_task or fnmatch.fnmatch(task.name, play_context.start_at_task) or \
                       task.get_name() == play_context.start_at_task or fnmatch.fnmatch(task.get_name(), play_context.start_at_task):
                        start_at_matched = True
                        break
                    else:
                        self.get_next_task_for_host(host)

                # finally, reset the host's state to ITERATING_SETUP
                self._host_states[host.name].run_state = self.ITERATING_SETUP

        if start_at_matched:
            # we have our match, so clear the start_at_task field on the
            # play context to flag that we've started at a task (and future
            # plays won't try to advance)
            play_context.start_at_task = None

        # Extend the play handlers list to include the handlers defined in roles
        self._play.handlers.extend(play.compile_roles_handlers())

    def get_host_state(self, host):
        try:
            return self._host_states[host.name].copy()
        except KeyError:
            raise AnsibleError("invalid host (%s) specified for playbook iteration" % host)

    def get_next_task_for_host(self, host, peek=False):

        display.debug("getting the next task for host %s" % host.name)
        s = self.get_host_state(host)

        task = None
        if s.run_state == self.ITERATING_COMPLETE:
            display.debug("host %s is done iterating, returning" % host.name)
            return (s, None)

        old_s = s
        (s, task) = self._get_next_task_from_state(s, host=host, peek=peek)

        def _roles_are_different(ra, rb):
            if ra != rb:
                return True
            else:
                return old_s.cur_dep_chain != task._block.get_dep_chain()

        if task and task._role:
            # if we had a current role, mark that role as completed
            if s.cur_role and _roles_are_different(task._role, s.cur_role) and host.name in s.cur_role._had_task_run and not peek:
                s.cur_role._completed[host.name] = True
            s.cur_role = task._role
            s.cur_dep_chain = task._block.get_dep_chain()

        if not peek:
            self._host_states[host.name] = s

        display.debug("done getting next task for host %s" % host.name)
        display.debug(" ^ task is: %s" % task)
        display.debug(" ^ state is: %s" % s)
        return (s, task)


    def _get_next_task_from_state(self, state, host, peek):

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
                    implied = self._play.gather_facts is None or boolean(self._play.gather_facts)

                    if (gathering == 'implicit' and implied) or \
                       (gathering == 'explicit' and boolean(self._play.gather_facts)) or \
                       (gathering == 'smart' and implied and not host._gathered_facts):
                        # The setup block is always self._blocks[0], as we inject it
                        # during the play compilation in __init__ above.
                        setup_block = self._blocks[0]
                        if setup_block.has_tasks() and len(setup_block.block) > 0:
                            task = setup_block.block[0]
                        if not peek:
                            # mark the host as having gathered facts, because we're
                            # returning the setup task to be executed
                            host.set_gathered_facts(True)
                else:
                    # This is the second trip through ITERATING_SETUP, so we clear
                    # the flag and move onto the next block in the list while setting
                    # the run state to ITERATING_TASKS
                    state.pending_setup = False

                    state.cur_block += 1
                    state.cur_regular_task = 0
                    state.cur_rescue_task  = 0
                    state.cur_always_task  = 0
                    state.run_state = self.ITERATING_TASKS
                    state.child_state = None

            elif state.run_state == self.ITERATING_TASKS:
                # clear the pending setup flag, since we're past that and it didn't fail
                if state.pending_setup:
                    state.pending_setup = False

                # First, we check for a child task state that is not failed, and if we
                # have one recurse into it for the next task. If we're done with the child
                # state, we clear it and drop back to geting the next task from the list.
                if state.tasks_child_state:
                    if state.tasks_child_state.fail_state != self.FAILED_NONE:
                        # failed child state, so clear it and move into the rescue portion
                        state.tasks_child_state = None
                        state.fail_state |= self.FAILED_TASKS
                        state.run_state = self.ITERATING_RESCUE
                    else:
                        # get the next task recursively
                        (state.tasks_child_state, task) = self._get_next_task_from_state(state.tasks_child_state, host=host, peek=peek)
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
                        if isinstance(task, Block) or state.tasks_child_state is not None:
                            state.tasks_child_state = HostState(blocks=[task])
                            state.tasks_child_state.run_state = self.ITERATING_TASKS
                            state.tasks_child_state.cur_role = state.cur_role
                            # since we've created the child state, clear the task
                            # so we can pick up the child state on the next pass
                            task = None
                        state.cur_regular_task += 1

            elif state.run_state == self.ITERATING_RESCUE:
                # The process here is identical to ITERATING_TASKS, except instead
                # we move into the always portion of the block.
                if state.rescue_child_state:
                    if state.rescue_child_state.fail_state != self.FAILED_NONE:
                        state.rescue_child_state = None
                        state.fail_state |= self.FAILED_RESCUE
                        state.run_state = self.ITERATING_ALWAYS
                    else:
                        (state.rescue_child_state, task) = self._get_next_task_from_state(state.rescue_child_state, host=host, peek=peek)
                        if task is None:
                            state.rescue_child_state = None
                            continue
                else:
                    if state.fail_state & self.FAILED_RESCUE == self.FAILED_RESCUE:
                        state.run_state = self.ITERATING_ALWAYS
                    elif state.cur_rescue_task >= len(block.rescue):
                        if len(block.rescue) > 0:
                            state.fail_state = self.FAILED_NONE
                        state.run_state = self.ITERATING_ALWAYS
                    else:
                        task = block.rescue[state.cur_rescue_task]
                        if isinstance(task, Block) or state.rescue_child_state is not None:
                            state.rescue_child_state = HostState(blocks=[task])
                            state.rescue_child_state.run_state = self.ITERATING_TASKS
                            state.rescue_child_state.cur_role = state.cur_role
                            task = None
                        state.cur_rescue_task += 1

            elif state.run_state == self.ITERATING_ALWAYS:
                # And again, the process here is identical to ITERATING_TASKS, except
                # instead we either move onto the next block in the list, or we set the
                # run state to ITERATING_COMPLETE in the event of any errors, or when we
                # have hit the end of the list of blocks.
                if state.always_child_state:
                    if state.always_child_state.fail_state != self.FAILED_NONE:
                        state.always_child_state = None
                        state.fail_state |= self.FAILED_ALWAYS
                        state.run_state = self.ITERATING_COMPLETE
                    else:
                        (state.always_child_state, task) = self._get_next_task_from_state(state.always_child_state, host=host, peek=peek)
                        if task is None:
                            state.always_child_state = None
                else:
                    if state.cur_always_task >= len(block.always):
                        if state.fail_state != self.FAILED_NONE:
                            state.run_state = self.ITERATING_COMPLETE
                        else:
                            state.cur_block += 1
                            state.cur_regular_task = 0
                            state.cur_rescue_task  = 0
                            state.cur_always_task  = 0
                            state.run_state = self.ITERATING_TASKS
                            state.tasks_child_state = None
                            state.rescue_child_state = None
                            state.always_child_state = None
                    else:
                        task = block.always[state.cur_always_task]
                        if isinstance(task, Block) or state.always_child_state is not None:
                            state.always_child_state = HostState(blocks=[task])
                            state.always_child_state.run_state = self.ITERATING_TASKS
                            state.always_child_state.cur_role = state.cur_role
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
        s = self._set_failed_state(s)
        self._host_states[host.name] = s

    def get_failed_hosts(self):
        return dict((host, True) for (host, state) in iteritems(self._host_states) if state.run_state == self.ITERATING_COMPLETE and state.fail_state != self.FAILED_NONE)

    def _check_failed_state(self, state):
        if state is None:
            return False
        elif state.fail_state != self.FAILED_NONE:
            if state.run_state == self.ITERATING_RESCUE and state.fail_state&self.FAILED_RESCUE == 0 or \
               state.run_state == self.ITERATING_ALWAYS and state.fail_state&self.FAILED_ALWAYS == 0:
                return False
            else:
                return True
        elif state.run_state == self.ITERATING_TASKS and self._check_failed_state(state.tasks_child_state):
            cur_block = self._blocks[state.cur_block]
            if len(cur_block.rescue) > 0 and state.fail_state & self.FAILED_RESCUE == 0:
                return False
            else:
                return True
        elif state.run_state == self.ITERATING_RESCUE and self._check_failed_state(state.rescue_child_state):
            return True
        elif state.run_state == self.ITERATING_ALWAYS and self._check_failed_state(state.always_child_state):
            return True
        return False

    def is_failed(self, host):
        s = self.get_host_state(host)
        return self._check_failed_state(s)

    def get_original_task(self, host, task):
        '''
        Finds the task in the task list which matches the UUID of the given task.
        The executor engine serializes/deserializes objects as they are passed through
        the different processes, and not all data structures are preserved. This method
        allows us to find the original task passed into the executor engine.
        '''
        def _search_block(block):
            '''
            helper method to check a block's task lists (block/rescue/always)
            for a given task uuid. If a Block is encountered in the place of a
            task, it will be recursively searched (this happens when a task
            include inserts one or more blocks into a task list).
            '''
            for b in (block.block, block.rescue, block.always):
                for t in b:
                    if isinstance(t, Block):
                        res = _search_block(t)
                        if res:
                            return res
                    elif t._uuid == task._uuid:
                        return t
            return None

        def _search_state(state):
            for block in state._blocks:
                res = _search_block(block)
                if res:
                    return res
            for child_state in (state.tasks_child_state, state.rescue_child_state, state.always_child_state):
                if child_state is not None:
                    res = _search_state(child_state)
                    if res:
                        return res
            return None

        s = self.get_host_state(host)
        res = _search_state(s)
        if res:
            return res

        for block in self._play.handlers:
            res = _search_block(block)
            if res:
                return res

        return None

    def _insert_tasks_into_state(self, state, task_list):
        # if we've failed at all, or if the task list is empty, just return the current state
        if state.fail_state != self.FAILED_NONE and state.run_state not in (self.ITERATING_RESCUE, self.ITERATING_ALWAYS) or not task_list:
            return state

        if state.run_state == self.ITERATING_TASKS:
            if state.tasks_child_state:
                state.tasks_child_state = self._insert_tasks_into_state(state.tasks_child_state, task_list)
            else:
                target_block = state._blocks[state.cur_block].copy(exclude_parent=True)
                before = target_block.block[:state.cur_regular_task]
                after  = target_block.block[state.cur_regular_task:]
                target_block.block = before + task_list + after
                state._blocks[state.cur_block] = target_block
        elif state.run_state == self.ITERATING_RESCUE:
            if state.rescue_child_state:
                state.rescue_child_state = self._insert_tasks_into_state(state.rescue_child_state, task_list)
            else:
                target_block = state._blocks[state.cur_block].copy(exclude_parent=True)
                before = target_block.rescue[:state.cur_rescue_task]
                after  = target_block.rescue[state.cur_rescue_task:]
                target_block.rescue = before + task_list + after
                state._blocks[state.cur_block] = target_block
        elif state.run_state == self.ITERATING_ALWAYS:
            if state.always_child_state:
                state.always_child_state = self._insert_tasks_into_state(state.always_child_state, task_list)
            else:
                target_block = state._blocks[state.cur_block].copy(exclude_parent=True)
                before = target_block.always[:state.cur_always_task]
                after  = target_block.always[state.cur_always_task:]
                target_block.always = before + task_list + after
                state._blocks[state.cur_block] = target_block
        return state

    def add_tasks(self, host, task_list):
        self._host_states[host.name] = self._insert_tasks_into_state(self.get_host_state(host), task_list)

