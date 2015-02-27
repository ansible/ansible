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


# the primary running states for the play iteration
ITERATING_SETUP    = 0
ITERATING_TASKS    = 1
ITERATING_RESCUE   = 2
ITERATING_ALWAYS   = 3
ITERATING_COMPLETE = 4

# the failure states for the play iteration
FAILED_NONE        = 0
FAILED_SETUP       = 1
FAILED_TASKS       = 2
FAILED_RESCUE      = 3
FAILED_ALWAYS      = 4

class PlayState:

    '''
    A helper class, which keeps track of the task iteration
    state for a given playbook. This is used in the PlaybookIterator
    class on a per-host basis.
    '''

    # FIXME: this class is the representation of a finite state machine,
    #        so we really should have a well defined state representation
    #        documented somewhere...

    def __init__(self, parent_iterator, host):
        '''
        Create the initial state, which tracks the running state as well
        as the failure state, which are used when executing block branches
        (rescue/always)
        '''

        self._parent_iterator = parent_iterator
        self._run_state       = ITERATING_SETUP
        self._failed_state    = FAILED_NONE
        self._gather_facts    = parent_iterator._play.gather_facts
        #self._task_list       = parent_iterator._play.compile()
        self._task_list       = parent_iterator._task_list[:]
        self._host            = host

        self._cur_block       = None
        self._cur_role        = None
        self._cur_task_pos    = 0
        self._cur_rescue_pos  = 0
        self._cur_always_pos  = 0
        self._cur_handler_pos = 0

    def next(self, peek=False):
        '''
        Determines and returns the next available task from the playbook,
        advancing through the list of plays as it goes. If peek is set to True,
        the internal state is not stored.
        '''

        task = None

        # save this locally so that we can peek at the next task
        # without updating the internal state of the iterator
        run_state       = self._run_state
        failed_state    = self._failed_state
        cur_block       = self._cur_block
        cur_role        = self._cur_role
        cur_task_pos    = self._cur_task_pos
        cur_rescue_pos  = self._cur_rescue_pos
        cur_always_pos  = self._cur_always_pos
        cur_handler_pos = self._cur_handler_pos


        while True:
            if run_state == ITERATING_SETUP:
                if failed_state == FAILED_SETUP:
                    run_state = ITERATING_COMPLETE
                else:
                    run_state = ITERATING_TASKS

                    if self._gather_facts == 'smart' and not self._host.gathered_facts or boolean(self._gather_facts):
                        self._host.set_gathered_facts(True)
                        task = Task()
                        # FIXME: this is not the best way to get this...
                        task.set_loader(self._parent_iterator._play._loader)
                        task.action = 'setup'
                        break
            elif run_state == ITERATING_TASKS:
                # if there is any failure state besides FAILED_NONE, we should
                # change to some other running state
                if failed_state != FAILED_NONE or cur_task_pos > len(self._task_list) - 1:
                    # if there is a block (and there always should be), start running
                    # the rescue portion if it exists (and if we haven't failed that
                    # already), or the always portion (if it exists and we didn't fail
                    # there too). Otherwise, we're done iterating.
                    if cur_block:
                        if failed_state != FAILED_RESCUE and cur_block.rescue:
                            run_state = ITERATING_RESCUE
                            cur_rescue_pos = 0
                        elif failed_state != FAILED_ALWAYS and cur_block.always:
                            run_state = ITERATING_ALWAYS
                            cur_always_pos = 0
                        else:
                            run_state = ITERATING_COMPLETE
                    else:
                        run_state = ITERATING_COMPLETE
                else:
                    task = self._task_list[cur_task_pos]
                    if cur_block is not None and cur_block != task._block:
                        run_state = ITERATING_ALWAYS
                        continue
                    else:
                        cur_block = task._block
                    cur_task_pos += 1

                    # Break out of the while loop now that we have our task
                    break

            elif run_state == ITERATING_RESCUE:
                # If we're iterating through the rescue tasks, make sure we haven't
                # failed yet. If so, move on to the always block or if not get the
                # next rescue task (if one exists)
                if failed_state == FAILED_RESCUE or cur_block.rescue is None or cur_rescue_pos > len(cur_block.rescue) - 1:
                    run_state = ITERATING_ALWAYS
                else:
                    task = cur_block.rescue[cur_rescue_pos]
                    cur_rescue_pos += 1
                    break

            elif run_state == ITERATING_ALWAYS:
                # If we're iterating through the always tasks, make sure we haven't
                # failed yet. If so, we're done iterating otherwise get the next always
                # task (if one exists)
                if failed_state == FAILED_ALWAYS or cur_block.always is None or cur_always_pos > len(cur_block.always) - 1:
                    cur_block = None
                    if failed_state == FAILED_ALWAYS or cur_task_pos > len(self._task_list) - 1:
                        run_state = ITERATING_COMPLETE
                    else:
                        run_state = ITERATING_TASKS
                else:
                    task = cur_block.always[cur_always_pos]
                    cur_always_pos += 1
                    break

            elif run_state == ITERATING_COMPLETE:
                # done iterating, return None to signify that
                return None

        if task._role:
            # if we had a current role, mark that role as completed
            if cur_role and task._role != cur_role and not peek:
                cur_role._completed = True

            cur_role = task._role

            # if the current role has not had its task run flag set, mark
            # clear the completed flag so we can correctly determine if the
            # role was run
            if not cur_role._had_task_run and not peek:
                cur_role._completed = False

        # If we're not just peeking at the next task, save the internal state 
        if not peek:
            self._run_state       = run_state
            self._failed_state    = failed_state
            self._cur_block       = cur_block
            self._cur_role        = cur_role
            self._cur_task_pos    = cur_task_pos
            self._cur_rescue_pos  = cur_rescue_pos
            self._cur_always_pos  = cur_always_pos
            self._cur_handler_pos = cur_handler_pos

        return task

    def mark_failed(self):
        '''
        Escalates the failed state relative to the running state.
        '''
        if self._run_state == ITERATING_SETUP:
            self._failed_state = FAILED_SETUP
        elif self._run_state == ITERATING_TASKS:
            self._failed_state = FAILED_TASKS
        elif self._run_state == ITERATING_RESCUE:
            self._failed_state = FAILED_RESCUE
        elif self._run_state == ITERATING_ALWAYS:
            self._failed_state = FAILED_ALWAYS

    def add_tasks(self, task_list):
        if self._run_state == ITERATING_TASKS:
            before = self._task_list[:self._cur_task_pos]
            after  = self._task_list[self._cur_task_pos:]
            self._task_list = before + task_list + after
        elif self._run_state == ITERATING_RESCUE:
            before = self._cur_block.rescue[:self._cur_rescue_pos]
            after  = self._cur_block.rescue[self._cur_rescue_pos:]
            self._cur_block.rescue = before + task_list + after
        elif self._run_state == ITERATING_ALWAYS:
            before = self._cur_block.always[:self._cur_always_pos]
            after  = self._cur_block.always[self._cur_always_pos:]
            self._cur_block.always = before + task_list + after

class PlayIterator:

    '''
    The main iterator class, which keeps the state of the playbook
    on a per-host basis using the above PlaybookState class.
    '''

    def __init__(self, inventory, play):
        self._play         = play
        self._inventory    = inventory
        self._host_entries = dict()
        self._first_host   = None

        # Build the per-host dictionary of playbook states, using a copy
        # of the play object so we can post_validate it to ensure any templated
        # fields are filled in without modifying the original object, since
        # post_validate() saves the templated values.

        # FIXME: this is a hacky way of doing this, the iterator should
        #        instead get the loader and variable manager directly
        #        as args to __init__
        all_vars = inventory._variable_manager.get_vars(loader=inventory._loader, play=play)
        new_play = play.copy()
        new_play.post_validate(all_vars, fail_on_undefined=False)

        self._task_list = new_play.compile()
        for host in inventory.get_hosts(new_play.hosts):
            if self._first_host is None:
                self._first_host = host
            self._host_entries[host.get_name()] = PlayState(parent_iterator=self, host=host)

    # FIXME: remove, probably not required anymore
    #def get_next_task(self, peek=False):
    #    ''' returns the next task for host[0] '''
    #
    #    first_entry = self._host_entries[self._first_host.get_name()]
    #    if not peek:
    #        for entry in self._host_entries:
    #            if entry != self._first_host.get_name():
    #                target_entry = self._host_entries[entry]
    #                if target_entry._cur_task_pos == first_entry._cur_task_pos:
    #                    target_entry.next()
    #    return first_entry.next(peek=peek)

    def get_next_task_for_host(self, host, peek=False):
        ''' fetch the next task for the given host '''
        if host.get_name() not in self._host_entries:
            raise AnsibleError("invalid host (%s) specified for playbook iteration" % host)

        return self._host_entries[host.get_name()].next(peek=peek)

    def mark_host_failed(self, host):
        ''' mark the given host as failed '''
        if host.get_name() not in self._host_entries:
            raise AnsibleError("invalid host (%s) specified for playbook iteration" % host)

        self._host_entries[host.get_name()].mark_failed()

    def get_original_task(self, task):
        '''
        Finds the task in the task list which matches the UUID of the given task.
        The executor engine serializes/deserializes objects as they are passed through
        the different processes, and not all data structures are preserved. This method
        allows us to find the original task passed into the executor engine.
        '''

        for t in self._task_list:
            if t._uuid == task._uuid:
                return t

        return None

    def add_tasks(self, host, task_list):
        if host.name not in self._host_entries:
            raise AnsibleError("invalid host (%s) specified for playbook iteration (expanding task list)" % host)

        self._host_entries[host.name].add_tasks(task_list)
