# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import fnmatch

from enum import IntEnum

from ansible import constants as C
from ansible.errors import AnsibleAssertionError
from ansible.inventory.host import Host
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.playbook.block import Block
from ansible.playbook.handler import Handler
from ansible.playbook.task import Task
from ansible.utils.display import Display


display = Display()


class IteratingStates(IntEnum):
    SETUP = 0
    TASKS = 1
    RESCUE = 2
    ALWAYS = 3
    HANDLERS = 4
    COMPLETE = 5


class HostState:
    __slots__ = (
        "_blocks", "handlers", "handler_notifications", "cur_block", "cur_regular_task", "cur_rescue_task",
        "cur_always_task", "cur_handlers_task", "run_state", "failed", "pre_flushing_run_state", "update_handlers",
        "pending_setup", "child_state", "did_start_at_task",
    )

    def __init__(self, blocks):
        self._blocks = blocks[:]
        self.handlers = []
        self.handler_notifications = []
        self.cur_block = 0
        self.cur_regular_task = 0
        self.cur_rescue_task = 0
        self.cur_always_task = 0
        self.cur_handlers_task = 0
        self.run_state = IteratingStates.SETUP
        self.failed = False
        self.pre_flushing_run_state = None
        self.update_handlers = True
        self.pending_setup = False
        self.child_state = None
        self.did_start_at_task = False

    def __repr__(self):
        return "HostState(%r)" % self._blocks

    def __str__(self):
        return (
            f"HOST STATE: block={self.cur_block}, task={self.cur_regular_task}, rescue={self.cur_rescue_task}, "
            f"always={self.cur_always_task}, handlers={self.cur_handlers_task}, run_state={self.run_state}, "
            f"failed={self.failed}, pre_flushing_run_state={self.pre_flushing_run_state}, "
            f"update_handlers={self.update_handlers}, pending_setup={self.pending_setup}, "
            f"child state? ({self.child_state}), did start at task? {self.did_start_at_task}"
        )

    def get_current_block(self) -> Block:
        return self._blocks[self.cur_block]

    def mark_failed(self) -> None:
        if self.run_state == IteratingStates.HANDLERS:
            self.run_state = self.pre_flushing_run_state
            self.update_handlers = True

        if self.run_state == IteratingStates.SETUP:
            self.failed = True
            self.run_state = IteratingStates.COMPLETE
        else:
            s = self.get_current()

            s.failed = True
            if s.run_state == IteratingStates.TASKS:
                if s.get_current_block().rescue:
                    s.run_state = IteratingStates.RESCUE
                elif s.get_current_block().always:
                    s.run_state = IteratingStates.ALWAYS
                else:
                    s.run_state = IteratingStates.COMPLETE
            elif s.run_state == IteratingStates.RESCUE:
                if s.get_current_block().always:
                    s.run_state = IteratingStates.ALWAYS
                else:
                    s.run_state = IteratingStates.COMPLETE
            elif s.run_state == IteratingStates.ALWAYS:
                s.run_state = IteratingStates.COMPLETE

    def is_failed(self) -> bool:
        return self.run_state == IteratingStates.COMPLETE and self.failed

    def clear_failed(self) -> None:
        state = self
        while state is not None:
            state.failed = False
            state = state.child_state

    def is_any_block_rescuing(self) -> bool:
        """Given the current HostState state, determines if the current block, or any child blocks,
        are in rescue mode."""
        state = self
        while state is not None:
            if state.run_state == IteratingStates.TASKS and state.get_current_block().rescue:
                return True
            state = state.child_state
        return False

    def insert_tasks(self, task_list: list[Block]) -> None:
        if self.run_state == IteratingStates.HANDLERS:
            self.handlers[self.cur_handlers_task:self.cur_handlers_task] = [h for b in task_list for h in b.block]
        else:
            state = self.get_current()

            target_block = state.get_current_block().copy()

            match state.run_state:
                case IteratingStates.TASKS:
                    target_block.block[state.cur_regular_task:state.cur_regular_task] = task_list
                case IteratingStates.RESCUE:
                    target_block.rescue[state.cur_rescue_task:state.cur_rescue_task] = task_list
                case IteratingStates.ALWAYS:
                    target_block.always[state.cur_always_task:state.cur_always_task] = task_list
                case _:
                    raise AssertionError(f"Unexpected run_state {state.run_state} detected while inserting tasks")

            state._blocks[state.cur_block] = target_block

    def get_current(self) -> HostState:
        s = self
        while s.child_state is not None:
            s = s.child_state
        return s

    def copy(self) -> HostState:
        new_state = HostState(self._blocks)
        new_state.handlers = self.handlers[:]
        new_state.handler_notifications = self.handler_notifications[:]
        new_state.cur_block = self.cur_block
        new_state.cur_regular_task = self.cur_regular_task
        new_state.cur_rescue_task = self.cur_rescue_task
        new_state.cur_always_task = self.cur_always_task
        new_state.cur_handlers_task = self.cur_handlers_task
        new_state.run_state = self.run_state
        new_state.failed = self.failed
        new_state.pre_flushing_run_state = self.pre_flushing_run_state
        new_state.update_handlers = self.update_handlers
        new_state.pending_setup = self.pending_setup
        new_state.did_start_at_task = self.did_start_at_task
        if self.child_state is not None:
            new_state.child_state = self.child_state.copy()
        return new_state


class PlayIterator:

    def __init__(self, inventory, play, play_context, variable_manager, all_vars, start_at_done=False):
        self._play = play
        self._blocks = []
        self._variable_manager = variable_manager

        setup_block = Block(play=self._play)
        # Gathering facts with run_once would copy the facts from one host to
        # the others.
        setup_block.run_once = False
        setup_task = Task(block=setup_block)
        setup_task.action = 'gather_facts'
        # TODO: hardcoded resolution here, but should use actual resolution code in the end,
        #       in case of 'legacy' mismatch
        setup_task.resolved_action = 'ansible.builtin.gather_facts'
        setup_task.name = 'Gathering Facts'
        setup_task.args = {}

        # Unless play is specifically tagged, gathering should 'always' run
        if not self._play.tags:
            setup_task.tags = ['always']

        # Default options to gather
        for option in ('gather_subset', 'gather_timeout', 'fact_path'):
            value = getattr(self._play, option, None)
            if value is not None:
                setup_task.args[option] = value

        setup_task.set_loader(self._play._loader)
        # short circuit fact gathering if the entire playbook is conditional
        if self._play._included_conditional is not None:
            setup_task.when = self._play._included_conditional[:]
        setup_block.block = [setup_task]

        setup_block = setup_block.filter_tagged_tasks(all_vars)
        self._blocks.append(setup_block)

        # keep flatten (no blocks) list of all tasks from the play
        # used for the lockstep mechanism in the linear strategy
        self.all_tasks = setup_block.get_tasks()

        for block in self._play.compile():
            new_block = block.filter_tagged_tasks(all_vars)
            if new_block.has_tasks():
                self._blocks.append(new_block)
                self.all_tasks.extend(new_block.get_tasks())

        # keep list of all handlers, it is copied into each HostState
        # at the beginning of IteratingStates.HANDLERS
        # the copy happens at each flush in order to restore the original
        # list and remove any included handlers that might not be notified
        # at the particular flush
        self.handlers = [h for b in self._play.handlers for h in b.block]

        self._host_states = {}
        start_at_matched = False
        batch = inventory.get_hosts(self._play.hosts, order=self._play.order)
        self.batch_size = len(batch)
        for host in batch:
            self.set_state_for_host(host.name, HostState(blocks=self._blocks))
            # if we're looking to start at a specific task, iterate through
            # the tasks for this host until we find the specified task
            if play_context.start_at_task is not None and not start_at_done:
                while True:
                    (s, task) = self.get_next_task_for_host(host, peek=True)
                    if s.run_state == IteratingStates.COMPLETE:
                        break
                    if task.name == play_context.start_at_task or (task.name and fnmatch.fnmatch(task.name, play_context.start_at_task)) or \
                       task.get_name() == play_context.start_at_task or fnmatch.fnmatch(task.get_name(), play_context.start_at_task):
                        start_at_matched = True
                        break
                    self.set_state_for_host(host.name, s)

                # finally, reset the host's state to IteratingStates.SETUP
                if start_at_matched:
                    self._host_states[host.name].did_start_at_task = True
                    self._host_states[host.name].run_state = IteratingStates.SETUP

        if start_at_matched:
            # we have our match, so clear the start_at_task field on the
            # play context to flag that we've started at a task (and future
            # plays won't try to advance)
            play_context.start_at_task = None

        self.end_play = False
        self.cur_task = 0

    def get_host_state(self, host: Host) -> HostState:
        # Since we're using the PlayIterator to carry forward failed hosts,
        # in the event that a previous host was not in the current inventory
        # we create a stub state for it now
        if host.name not in self._host_states:
            # FIXME why is this needed?
            self.set_state_for_host(host.name, HostState(blocks=[]))

        return self._host_states[host.name].copy()

    def get_next_task_for_host(self, host: Host, peek: bool = False) -> tuple[HostState, Task | Handler | None]:
        display.debug("getting the next task for host %s" % host.name)
        s = self.get_host_state(host)

        if s.run_state == IteratingStates.COMPLETE:
            display.debug("host %s is done iterating, returning" % host.name)
            return s, None

        s, task = self._get_next_task_from_state(s, host=host)

        if not peek:
            self.set_state_for_host(host.name, s)

        display.debug("done getting next task for host %s" % host.name)
        display.debug(" ^ task is: %s" % task)
        display.debug(" ^ state is: %s" % s)
        return s, task

    def _get_next_task_from_state(self, state: HostState, host: Host) -> tuple[HostState, Task | Handler | None]:
        while True:
            try:
                block = state.get_current_block()
            except IndexError:
                state.run_state = IteratingStates.COMPLETE
                return state, None

            match state.run_state:
                case IteratingStates.SETUP:
                    if not state.pending_setup:
                        state.pending_setup = True

                        gathering = C.DEFAULT_GATHERING
                        gather_facts = boolean(self._play.gather_facts, strict=False)
                        implied = self._play.gather_facts is None or gather_facts
                        if (gathering == 'implicit' and implied) or \
                           (gathering == 'explicit' and gather_facts) or \
                           (gathering == 'smart' and implied and
                                not (self._variable_manager._fact_cache.get(host.name, {}).get('_ansible_facts_gathered', False))):
                            # The setup block is always self._blocks[0], as we inject it
                            # during the play compilation in __init__ above.
                            setup_block = self._blocks[0]
                            if setup_block.has_tasks() and len(setup_block.block) > 0:
                                return state, setup_block.block[0]
                    else:
                        state.pending_setup = False
                        state.run_state = IteratingStates.TASKS
                        if not state.did_start_at_task:
                            # FIXME ???
                            state.cur_block += 1
                case IteratingStates.TASKS:
                    if state.child_state:
                        state.child_state, task = self._get_next_task_from_state(state.child_state, host=host)
                        if state.child_state.is_failed():
                            state.child_state = None
                            state.mark_failed()
                        elif state.child_state.run_state == IteratingStates.COMPLETE:
                            state.child_state = None
                        else:
                            return state, task
                    else:
                        try:
                            task = block.block[state.cur_regular_task]
                        except IndexError:
                            state.run_state = IteratingStates.ALWAYS
                        else:
                            state.cur_regular_task += 1
                            if isinstance(task, Block):
                                state.child_state = HostState(blocks=[task])
                                state.child_state.run_state = IteratingStates.TASKS
                            else:
                                return state, task
                case IteratingStates.RESCUE:
                    if state.child_state:
                        state.child_state, task = self._get_next_task_from_state(state.child_state, host=host)
                        if state.child_state.is_failed():
                            state.child_state = None
                            state.mark_failed()
                        elif state.child_state.run_state == IteratingStates.COMPLETE:
                            state.child_state = None
                        else:
                            return state, task
                    else:
                        try:
                            task = block.rescue[state.cur_rescue_task]
                        except IndexError:
                            state.run_state = IteratingStates.ALWAYS
                            state.failed = len(block.rescue) == 0
                        else:
                            state.cur_rescue_task += 1
                            if isinstance(task, Block):
                                state.child_state = HostState(blocks=[task])
                                state.child_state.run_state = IteratingStates.TASKS
                            else:
                                return state, task
                case IteratingStates.ALWAYS:
                    if state.child_state:
                        state.child_state, task = self._get_next_task_from_state(state.child_state, host=host)
                        if state.child_state.is_failed():
                            state.child_state = None
                            state.mark_failed()
                        elif state.child_state.run_state == IteratingStates.COMPLETE:
                            state.child_state = None
                        else:
                            return state, task
                    else:
                        try:
                            task = block.always[state.cur_always_task]
                        except IndexError:
                            if state.failed:
                                state.run_state = IteratingStates.COMPLETE
                            else:
                                state.run_state = IteratingStates.TASKS
                                state.cur_block += 1
                                state.cur_regular_task = 0
                                state.cur_rescue_task = 0
                                state.cur_always_task = 0
                        else:
                            state.cur_always_task += 1
                            if isinstance(task, Block):
                                state.child_state = HostState(blocks=[task])
                                state.child_state.run_state = IteratingStates.TASKS
                            else:
                                return state, task
                case IteratingStates.HANDLERS:
                    if state.update_handlers:
                        # reset handlers for HostState since handlers from include_tasks
                        # might be there from previous flush
                        state.handlers = self.handlers[:]
                        state.update_handlers = False

                    while True:
                        try:
                            task = state.handlers[state.cur_handlers_task]
                        except IndexError:
                            state.cur_handlers_task = 0
                            state.run_state = state.pre_flushing_run_state
                            state.update_handlers = True
                            break
                        else:
                            state.cur_handlers_task += 1
                            if isinstance(task, Handler) and task.is_host_notified(host):
                                return state, task
                case IteratingStates.COMPLETE:
                    return state, None

    def mark_host_failed(self, host: Host) -> None:
        s = self.get_state_for_host(host.name)
        display.debug("marking host %s failed, current state: %s" % (host, s))
        s.mark_failed()
        display.debug("^ failed state is now: %s" % s)
        self._play._removed_hosts.append(host.name)

    def get_failed_hosts(self) -> dict[str, bool]:
        return dict((host, True) for (host, state) in self._host_states.items() if state.get_current().is_failed())

    def is_failed(self, host: Host) -> bool:
        return self.get_state_for_host(host.name).get_current().is_failed()

    def clear_host_errors(self, host: Host) -> None:
        self.get_state_for_host(host.name).clear_failed()

    def add_tasks(self, host: Host, task_list: list[Block]) -> None:
        if task_list:
            self.get_state_for_host(host.name).insert_tasks(task_list)

    @property
    def host_states(self) -> dict[str, HostState]:
        return self._host_states

    def get_state_for_host(self, hostname: str) -> HostState:
        if hostname not in self._host_states:
            self.set_state_for_host(hostname, HostState(blocks=[]))
        return self._host_states[hostname]

    def set_state_for_host(self, hostname: str, state: HostState) -> None:
        if not isinstance(state, HostState):
            raise AnsibleAssertionError('Expected state to be a HostState but was a %s' % type(state))
        self._host_states[hostname] = state

    def set_run_state_for_host(self, hostname: str, run_state: IteratingStates) -> None:
        if not isinstance(run_state, IteratingStates):
            raise AnsibleAssertionError('Expected run_state to be a IteratingStates but was %s' % (type(run_state)))
        self._host_states[hostname].run_state = run_state

    def add_notification(self, hostname: str, notification: str) -> None:
        # preserve order
        host_state = self._host_states[hostname]
        if notification not in host_state.handler_notifications:
            host_state.handler_notifications.append(notification)

    def clear_notification(self, hostname: str, notification: str) -> None:
        self._host_states[hostname].handler_notifications.remove(notification)
