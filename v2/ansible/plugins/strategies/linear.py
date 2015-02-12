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
from ansible.plugins.strategies import StrategyBase
from ansible.utils.debug import debug

class StrategyModule(StrategyBase):

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
                hosts_left = self.get_hosts_remaining(iterator._play)
                debug("done getting the remaining hosts for this loop")
                if len(hosts_left) == 0:
                    debug("out of hosts to run on")
                    self._callback.playbook_on_no_hosts_remaining()
                    result = False
                    break

                # queue up this task for each host in the inventory
                callback_sent = False
                work_to_do = False
                for host in hosts_left:
                    while True:
                        task = iterator.get_next_task_for_host(host)
                        if not task:
                            break

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

                        if not task.evaluate_tags(connection_info.only_tags, connection_info.skip_tags, task_vars) and task.action != 'setup':
                            debug("'%s' failed tag evaluation" % task)
                            continue

                        break

                    if not task:
                        continue

                    work_to_do = True
                    if task.action == 'meta':
                        # meta tasks store their args in the _raw_params field of args,
                        # since they do not use k=v pairs, so get that
                        meta_action = task.args.get('_raw_params')
                        if meta_action == 'flush_handlers':
                            self.run_handlers(iterator, connection_info)
                        else:
                            raise AnsibleError("invalid meta action requested: %s" % meta_action, obj=task._ds)
                    else:
                        if not callback_sent:
                            self._callback.playbook_on_task_start(task.get_name(), False)
                            callback_sent = True

                        self._blocked_hosts[host.get_name()] = True
                        self._queue_task(host, task, task_vars, connection_info)

                    self._process_pending_results(iterator)

                debug("done queuing things up, now waiting for results queue to drain")
                self._wait_on_pending_results(iterator)
                debug("results queue empty")
            except (IOError, EOFError), e:
                debug("got IOError/EOFError in task loop: %s" % e)
                # most likely an abort, return failed
                return 1

        # run the base class run() method, which executes the cleanup function
        # and runs any outstanding handlers which have been triggered

        return super(StrategyModule, self).run(iterator, connection_info, result)

