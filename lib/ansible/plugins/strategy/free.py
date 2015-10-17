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

import time

from ansible.errors import *
from ansible.playbook.included_file import IncludedFile
from ansible.plugins.strategy import StrategyBase

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

class StrategyModule(StrategyBase):

    def run(self, iterator, play_context):
        '''
        The "free" strategy is a bit more complex, in that it allows tasks to
        be sent to hosts as quickly as they can be processed. This means that
        some hosts may finish very quickly if run tasks result in little or no
        work being done versus other systems.

        The algorithm used here also tries to be more "fair" when iterating
        through hosts by remembering the last host in the list to be given a task
        and starting the search from there as opposed to the top of the hosts
        list again, which would end up favoring hosts near the beginning of the
        list.
        '''

        # the last host to be given a task
        last_host = 0

        result = True

        work_to_do = True
        while work_to_do and not self._tqm._terminated:

            hosts_left = [host for host in self._inventory.get_hosts(iterator._play.hosts) if host.name not in self._tqm._unreachable_hosts]
            if len(hosts_left) == 0:
                self._tqm.send_callback('v2_playbook_on_no_hosts_remaining')
                result = False
                break

            work_to_do = False        # assume we have no more work to do
            starting_host = last_host # save current position so we know when we've
                                      # looped back around and need to break

            # try and find an unblocked host with a task to run
            host_results = []
            while True:
                host = hosts_left[last_host]
                self._display.debug("next free host: %s" % host)
                host_name = host.get_name()

                # peek at the next task for the host, to see if there's
                # anything to do do for this host
                (state, task) = iterator.get_next_task_for_host(host, peek=True)
                self._display.debug("free host state: %s" % state)
                self._display.debug("free host task: %s" % task)
                if host_name not in self._tqm._failed_hosts and host_name not in self._tqm._unreachable_hosts and task:

                    # set the flag so the outer loop knows we've still found
                    # some work which needs to be done
                    work_to_do = True

                    self._display.debug("this host has work to do")

                    # check to see if this host is blocked (still executing a previous task)
                    if not host_name in self._blocked_hosts or not self._blocked_hosts[host_name]:
                        # pop the task, mark the host blocked, and queue it
                        self._blocked_hosts[host_name] = True
                        (state, task) = iterator.get_next_task_for_host(host)

                        self._display.debug("getting variables")
                        task_vars = self._variable_manager.get_vars(loader=self._loader, play=iterator._play, host=host, task=task)
                        self._display.debug("done getting variables")

                        # check to see if this task should be skipped, due to it being a member of a
                        # role which has already run (and whether that role allows duplicate execution)
                        if task._role and task._role.has_run(host):
                            # If there is no metadata, the default behavior is to not allow duplicates,
                            # if there is metadata, check to see if the allow_duplicates flag was set to true
                            if task._role._metadata is None or task._role._metadata and not task._role._metadata.allow_duplicates:
                                self._display.debug("'%s' skipped because role has already run" % task)
                                continue

                        if task.action == 'meta':
                            # meta tasks store their args in the _raw_params field of args,
                            # since they do not use k=v pairs, so get that
                            meta_action = task.args.get('_raw_params')
                            if meta_action == 'noop':
                                # FIXME: issue a callback for the noop here?
                                continue
                            elif meta_action == 'flush_handlers':
                                # FIXME: in the 'free' mode, flushing handlers should result in
                                #        only those handlers notified for the host doing the flush
                                self.run_handlers(iterator, play_context)
                            else:
                                raise AnsibleError("invalid meta action requested: %s" % meta_action, obj=task._ds)

                            self._blocked_hosts[host_name] = False
                        else:
                            # handle step if needed, skip meta actions as they are used internally
                            if not self._step or self._take_step(task, host_name):
                                self._tqm.send_callback('v2_playbook_on_task_start', task, is_conditional=False)
                                self._queue_task(host, task, task_vars, play_context)

                # move on to the next host and make sure we
                # haven't gone past the end of our hosts list
                last_host += 1
                if last_host > len(hosts_left) - 1:
                    last_host = 0

                # if we've looped around back to the start, break out
                if last_host == starting_host:
                    break

            results = self._process_pending_results(iterator)
            host_results.extend(results)

            try:
                included_files = IncludedFile.process_include_results(host_results, self._tqm, iterator=iterator, loader=self._loader, variable_manager=self._variable_manager)
            except AnsibleError as e:
                return False

            if len(included_files) > 0:
                for included_file in included_files:
                    # included hosts get the task list while those excluded get an equal-length
                    # list of noop tasks, to make sure that they continue running in lock-step
                    try:
                        new_blocks = self._load_included_file(included_file, iterator=iterator)
                    except AnsibleError as e:
                        for host in included_file._hosts:
                            iterator.mark_host_failed(host)
                        self._display.warning(str(e))
                        continue

                    for host in hosts_left:
                        if host in included_file._hosts:
                            task_vars = self._variable_manager.get_vars(loader=self._loader, play=iterator._play, host=host, task=included_file._task)
                            final_blocks = []
                            for new_block in new_blocks:
                                final_blocks.append(new_block.filter_tagged_tasks(play_context, task_vars))
                            iterator.add_tasks(host, final_blocks)

            # pause briefly so we don't spin lock
            time.sleep(0.05)

        try:
            results = self._wait_on_pending_results(iterator)
            host_results.extend(results)
        except Exception as e:
            # FIXME: ctrl+c can cause some failures here, so catch them
            #        with the appropriate error type
            pass

        # run the base class run() method, which executes the cleanup function
        # and runs any outstanding handlers which have been triggered
        return super(StrategyModule, self).run(iterator, play_context, result)

