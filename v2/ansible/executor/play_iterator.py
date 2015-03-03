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

from ansible.errors import *
from ansible.playbook.task import Task

from ansible.utils.boolean import boolean

__all__ = ['PlayIterator']

class HostState:
    def __init__(self, blocks):
        self._blocks          = blocks[:]

        self.cur_block        = 0
        self.cur_regular_task = 0
        self.cur_rescue_task  = 0
        self.cur_always_task  = 0
        self.cur_role         = None
        self.run_state        = PlayIterator.ITERATING_SETUP
        self.fail_state       = PlayIterator.FAILED_NONE
        self.pending_setup    = False

    def __repr__(self):
        return "HOST STATE: block=%d, task=%d, rescue=%d, always=%d, role=%s, run_state=%d, fail_state=%d, pending_setup=%s" % (
            self.cur_block,
            self.cur_regular_task,
            self.cur_rescue_task,
            self.cur_always_task,
            self.cur_role,
            self.run_state,
            self.fail_state,
            self.pending_setup,
        )

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

    def __init__(self, inventory, play):
        # FIXME: should we save the post_validated play from below here instead?
        self._play = play

        # post validate the play, as we need some fields to be finalized now
        # so that we can use them to setup the iterator properly
        all_vars = inventory._variable_manager.get_vars(loader=inventory._loader, play=play)
        new_play = play.copy()
        new_play.post_validate(all_vars, fail_on_undefined=False)

        self._blocks  = new_play.compile()
        self._host_states = {}
        for host in inventory.get_hosts(new_play.hosts):
             self._host_states[host.name] = HostState(blocks=self._blocks)

    def get_host_state(self, host):
        try:
            return self._host_states[host.name].copy()
        except KeyError:
            raise AnsibleError("invalid host (%s) specified for playbook iteration" % host)

    def get_next_task_for_host(self, host, peek=False, lock_step=True):
        s = self.get_host_state(host)

        task = None
        if s.run_state == self.ITERATING_COMPLETE:
            return None
        else:
            while True:
                try:
                    cur_block = s._blocks[s.cur_block]
                except IndexError:
                    s.run_state = self.ITERATING_COMPLETE
                    break

                if s.run_state == self.ITERATING_SETUP:
                    s.run_state = self.ITERATING_TASKS
                    if self._play._gather_facts == 'smart' and not host.gathered_facts or boolean(self._play._gather_facts):
                        # mark the host as having gathered facts
                        host.set_gathered_facts(True)

                        task = Task()
                        task.action = 'setup'
                        task.set_loader(self._play._loader)

                elif s.run_state == self.ITERATING_TASKS:
                    # clear the pending setup flag, since we're past that and it didn't fail
                    if s.pending_setup:
                        s.pending_setup = False

                    if s.fail_state & self.FAILED_TASKS == self.FAILED_TASKS:
                        s.run_state = self.ITERATING_RESCUE
                    elif s.cur_regular_task >= len(cur_block.block):
                        s.run_state = self.ITERATING_ALWAYS
                    else:
                        task = cur_block.block[s.cur_regular_task]
                        s.cur_regular_task += 1
                        break
                elif s.run_state == self.ITERATING_RESCUE:
                    if s.fail_state & self.FAILED_RESCUE == self.FAILED_RESCUE:
                        s.run_state = self.ITERATING_ALWAYS
                    elif s.cur_rescue_task >= len(cur_block.rescue):
                        if len(cur_block.rescue) > 0:
                            s.fail_state = self.FAILED_NONE
                        s.run_state = self.ITERATING_ALWAYS
                    else:
                        task = cur_block.rescue[s.cur_rescue_task]
                        s.cur_rescue_task += 1
                        break
                elif s.run_state == self.ITERATING_ALWAYS:
                    if s.cur_always_task >= len(cur_block.always):
                        if s.fail_state != self.FAILED_NONE:
                            s.run_state = self.ITERATING_COMPLETE
                            break
                        else:
                            s.cur_block += 1
                            s.cur_regular_task = 0
                            s.cur_rescue_task  = 0
                            s.cur_always_task  = 0
                            s.run_state = self.ITERATING_TASKS
                    else:
                        task= cur_block.always[s.cur_always_task]
                        s.cur_always_task += 1
                        break

        if task and task._role:
            # if we had a current role, mark that role as completed
            if s.cur_role and task._role != s.cur_role and s.cur_role._had_task_run and not peek:
                s.cur_role._completed = True

            s.cur_role = task._role

        if not peek:
            self._host_states[host.name] = s

        return (s, task)

    def mark_host_failed(self, host):
        s = self.get_host_state(host)
        if s.pending_setup:
            s.fail_state |= self.FAILED_SETUP
            s.run_state = self.ITERATING_COMPLETE
        elif s.run_state == self.ITERATING_TASKS:
            s.fail_state |= self.FAILED_TASKS
            s.run_state = self.ITERATING_RESCUE
        elif s.run_state == self.ITERATING_RESCUE:
            s.fail_state |= self.FAILED_RESCUE
            s.run_state = self.ITERATING_ALWAYS
        elif s.run_state == self.ITERATING_ALWAYS:
            s.fail_state |= self.FAILED_ALWAYS
            s.run_state = self.ITERATING_COMPLETE
        self._host_states[host.name] = s

    def get_failed_hosts(self):
        return dict((host, True) for (host, state) in self._host_states.iteritems() if state.run_state == self.ITERATING_COMPLETE and state.failed_state != self.FAILED_NONE)

    def get_original_task(self, host, task):
        '''
        Finds the task in the task list which matches the UUID of the given task.
        The executor engine serializes/deserializes objects as they are passed through
        the different processes, and not all data structures are preserved. This method
        allows us to find the original task passed into the executor engine.
        '''
        s = self.get_host_state(host)
        for block in s._blocks:
            if block.block:
                for t in block.block:
                    if t._uuid == task._uuid:
                        return t
            if block.rescue:
                for t in block.rescue:
                    if t._uuid == task._uuid:
                        return t
            if block.always:
                for t in block.always:
                    if t._uuid == task._uuid:
                        return t
        return None

    def add_tasks(self, host, task_list):
        s = self.get_host_state(host)
        target_block = s._blocks[s.cur_block].copy()

        if s.run_state == self.ITERATING_TASKS:
            before = target_block.block[:s.cur_regular_task]
            after  = target_block.block[s.cur_regular_task:]
            target_block.block = before + task_list + after
        elif s.run_state == self.ITERATING_RESCUE:
            before = target_block.rescue[:s.cur_rescue_task]
            after  = target_block.rescue[s.cur_rescue_task:]
            target_block.rescue = before + task_list + after
        elif s.run_state == self.ITERATING_ALWAYS:
            before = target_block.always[:s.cur_always_task]
            after  = target_block.always[s.cur_always_task:]
            target_block.always = before + task_list + after

        s._blocks[s.cur_block] = target_block
        self._host_states[host.name] = s

