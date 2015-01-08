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
        while work_to_do:

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
                    task = iterator.get_next_task_for_host(host)
                    if not task:
                        continue

                    work_to_do = True
                    if not callback_sent:
                        self._callback.playbook_on_task_start(task.get_name(), False)
                        callback_sent = True

                    host_name = host.get_name()
                    if 1: #host_name not in self._tqm._failed_hosts and host_name not in self._tqm._unreachable_hosts:
                        self._blocked_hosts[host_name] = True
                        self._queue_task(iterator._play, host, task, connection_info)

                    self._process_pending_results()

                debug("done queuing things up, now waiting for results queue to drain")
                self._wait_on_pending_results()
                debug("results queue empty")
            except IOError, e:
                debug("got IOError: %s" % e)
                # most likely an abort, return failed
                return 1

        # run the base class run() method, which executes the cleanup function
        # and runs any outstanding handlers which have been triggered

        result &= super(StrategyModule, self).run(iterator, connection_info)

        return result
