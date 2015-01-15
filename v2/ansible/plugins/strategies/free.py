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

from ansible.plugins.strategies import StrategyBase

class StrategyModule(StrategyBase):

    def run(self, iterator, connection_info):
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

        work_to_do = True
        while work_to_do and not self._tqm._terminated:

            hosts_left = self.get_hosts_remaining()
            if len(hosts_left) == 0:
                self._callback.playbook_on_no_hosts_remaining()
                break

            # using .qsize() is a best estimate anyway, due to the
            # multiprocessing/threading concerns (per the python docs)
            if 1: #if self._job_queue.qsize() < len(hosts_left):

                work_to_do = False        # assume we have no more work to do
                starting_host = last_host # save current position so we know when we've
                                          # looped back around and need to break

                # try and find an unblocked host with a task to run
                while True:
                    host = hosts_left[last_host]
                    host_name = host.get_name()

                    # peek at the next task for the host, to see if there's
                    # anything to do do for this host
                    if host_name not in self._tqm._failed_hosts and host_name not in self._tqm._unreachable_hosts and iterator.get_next_task_for_host(host, peek=True):

                        # FIXME: check task tags, etc. here as we do in linear
                        # FIXME: handle meta tasks here, which will require a tweak
                        #        to run_handlers so that only the handlers on this host
                        #        are flushed and not all

                        # set the flag so the outer loop knows we've still found
                        # some work which needs to be done
                        work_to_do = True

                        # check to see if this host is blocked (still executing a previous task)
                        if not host_name in self._blocked_hosts:
                            # pop the task, mark the host blocked, and queue it
                            self._blocked_hosts[host_name] = True
                            task = iterator.get_next_task_for_host(host)
                            #self._callback.playbook_on_task_start(task.get_name(), False)
                            self._queue_task(iterator._play, host, task, connection_info)

                    # move on to the next host and make sure we
                    # haven't gone past the end of our hosts list
                    last_host += 1
                    if last_host > len(hosts_left) - 1:
                        last_host = 0

                    # if we've looped around back to the start, break out
                    if last_host == starting_host:
                        break

            # pause briefly so we don't spin lock
            time.sleep(0.05)

        try:
            self._wait_for_pending_results()
        except:
            # FIXME: ctrl+c can cause some failures here, so catch them
            #        with the appropriate error type
            pass

        # run the base class run() method, which executes the cleanup function
        # and runs any outstanding handlers which have been triggered
        super(StrategyModule, self).run(iterator, connection_info)

