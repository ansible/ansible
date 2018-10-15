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
    strategy: free
    short_description: Executes tasks on each host independently
    description:
        - Task execution is as fast as possible per host in batch as defined by C(serial) (default all).
          Ansible will not wait for other hosts to finish the current task before queuing the next task for a host that has finished.
          Once a host is done with the play, it opens it's slot to a new host that was waiting to start.
    version_added: "2.0"
    author: Ansible Core Team
'''

import time

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.playbook.included_file import IncludedFile
from ansible.plugins.loader import action_loader
from ansible.plugins.strategy import StrategyBase
from ansible.template import Templar
from ansible.module_utils._text import to_text


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

        result = self._tqm.RUN_OK

        work_to_do = True
        while work_to_do and not self._tqm._terminated:

            hosts_left = self.get_hosts_left(iterator)

            if len(hosts_left) == 0:
                self._tqm.send_callback('v2_playbook_on_no_hosts_remaining')
                result = False
                break

            work_to_do = False        # assume we have no more work to do
            starting_host = last_host  # save current position so we know when we've looped back around and need to break

            # try and find an unblocked host with a task to run
            host_results = []
            while True:
                host = hosts_left[last_host]
                display.debug("next free host: %s" % host)
                host_name = host.get_name()

                # peek at the next task for the host, to see if there's
                # anything to do do for this host
                (state, task) = iterator.get_next_task_for_host(host, peek=True)
                display.debug("free host state: %s" % state, host=host_name)
                display.debug("free host task: %s" % task, host=host_name)
                if host_name not in self._tqm._unreachable_hosts and task:

                    # set the flag so the outer loop knows we've still found
                    # some work which needs to be done
                    work_to_do = True

                    display.debug("this host has work to do", host=host_name)

                    # check to see if this host is blocked (still executing a previous task)
                    if host_name not in self._blocked_hosts or not self._blocked_hosts[host_name]:
                        # pop the task, mark the host blocked, and queue it
                        self._blocked_hosts[host_name] = True
                        (state, task) = iterator.get_next_task_for_host(host)

                        try:
                            action = action_loader.get(task.action, class_only=True)
                        except KeyError:
                            # we don't care here, because the action may simply not have a
                            # corresponding action plugin
                            action = None

                        display.debug("getting variables", host=host_name)
                        task_vars = self._variable_manager.get_vars(play=iterator._play, host=host, task=task)
                        self.add_tqm_variables(task_vars, play=iterator._play)
                        templar = Templar(loader=self._loader, variables=task_vars)
                        display.debug("done getting variables", host=host_name)

                        try:
                            task.name = to_text(templar.template(task.name, fail_on_undefined=False), nonstring='empty')
                            display.debug("done templating", host=host_name)
                        except:
                            # just ignore any errors during task name templating,
                            # we don't care if it just shows the raw name
                            display.debug("templating failed for some reason", host=host_name)

                        run_once = templar.template(task.run_once) or action and getattr(action, 'BYPASS_HOST_LOOP', False)
                        if run_once:
                            if action and getattr(action, 'BYPASS_HOST_LOOP', False):
                                raise AnsibleError("The '%s' module bypasses the host loop, which is currently not supported in the free strategy "
                                                   "and would instead execute for every host in the inventory list." % task.action, obj=task._ds)
                            else:
                                display.warning("Using run_once with the free strategy is not currently supported. This task will still be "
                                                "executed for every host in the inventory list.")

                        # check to see if this task should be skipped, due to it being a member of a
                        # role which has already run (and whether that role allows duplicate execution)
                        if task._role and task._role.has_run(host):
                            # If there is no metadata, the default behavior is to not allow duplicates,
                            # if there is metadata, check to see if the allow_duplicates flag was set to true
                            if task._role._metadata is None or task._role._metadata and not task._role._metadata.allow_duplicates:
                                display.debug("'%s' skipped because role has already run" % task, host=host_name)
                                del self._blocked_hosts[host_name]
                                continue

                        if task.action == 'meta':
                            self._execute_meta(task, play_context, iterator, target_host=host)
                            self._blocked_hosts[host_name] = False
                        else:
                            # handle step if needed, skip meta actions as they are used internally
                            if not self._step or self._take_step(task, host_name):
                                if task.any_errors_fatal:
                                    display.warning("Using any_errors_fatal with the free strategy is not supported, "
                                                    "as tasks are executed independently on each host")
                                self._tqm.send_callback('v2_playbook_on_task_start', task, is_conditional=False)
                                self._queue_task(host, task, task_vars, play_context)
                                del task_vars
                    else:
                        display.debug("%s is blocked, skipping for now" % host_name)

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

            self.update_active_connections(results)

            try:
                included_files = IncludedFile.process_include_results(
                    host_results,
                    iterator=iterator,
                    loader=self._loader,
                    variable_manager=self._variable_manager
                )
            except AnsibleError as e:
                return self._tqm.RUN_ERROR

            if len(included_files) > 0:
                all_blocks = dict((host, []) for host in hosts_left)
                for included_file in included_files:
                    display.debug("collecting new blocks for %s" % included_file)
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
                    except AnsibleError as e:
                        for host in included_file._hosts:
                            iterator.mark_host_failed(host)
                        display.warning(str(e))
                        continue

                    for new_block in new_blocks:
                        task_vars = self._variable_manager.get_vars(play=iterator._play, task=new_block._parent)
                        final_block = new_block.filter_tagged_tasks(play_context, task_vars)
                        for host in hosts_left:
                            if host in included_file._hosts:
                                all_blocks[host].append(final_block)
                    display.debug("done collecting new blocks for %s" % included_file)

                display.debug("adding all collected blocks from %d included file(s) to iterator" % len(included_files))
                for host in hosts_left:
                    iterator.add_tasks(host, all_blocks[host])
                display.debug("done adding collected blocks to iterator")

            # pause briefly so we don't spin lock
            time.sleep(C.DEFAULT_INTERNAL_POLL_INTERVAL)

        # collect all the final results
        results = self._wait_on_pending_results(iterator)

        # run the base class run() method, which executes the cleanup function
        # and runs any outstanding handlers which have been triggered
        return super(StrategyModule, self).run(iterator, play_context, result)
