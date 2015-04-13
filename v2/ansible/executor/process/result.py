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

from six.moves import queue
import multiprocessing
import os
import signal
import sys
import time
import traceback

HAS_ATFORK=True
try:
    from Crypto.Random import atfork
except ImportError:
    HAS_ATFORK=False

from ansible.playbook.handler import Handler
from ansible.playbook.task import Task

from ansible.utils.debug import debug

__all__ = ['ResultProcess']


class ResultProcess(multiprocessing.Process):
    '''
    The result worker thread, which reads results from the results
    queue and fires off callbacks/etc. as necessary.
    '''

    def __init__(self, final_q, workers):

        # takes a task queue manager as the sole param:
        self._final_q           = final_q
        self._workers           = workers
        self._cur_worker        = 0
        self._terminated        = False

        super(ResultProcess, self).__init__()

    def _send_result(self, result):
        debug("sending result: %s" % (result,))
        self._final_q.put(result, block=False)
        debug("done sending result")

    def _read_worker_result(self):
        result = None
        starting_point = self._cur_worker
        while True:
            (worker_prc, main_q, rslt_q) = self._workers[self._cur_worker]
            self._cur_worker += 1
            if self._cur_worker >= len(self._workers):
                self._cur_worker = 0

            try:
                if not rslt_q.empty():
                    debug("worker %d has data to read" % self._cur_worker)
                    result = rslt_q.get(block=False)
                    debug("got a result from worker %d: %s" % (self._cur_worker, result))
                    break
            except queue.Empty:
                pass

            if self._cur_worker == starting_point:
                break

        return result

    def terminate(self):
        self._terminated = True
        super(ResultProcess, self).terminate()

    def run(self):
        '''
        The main thread execution, which reads from the results queue
        indefinitely and sends callbacks/etc. when results are received.
        '''

        if HAS_ATFORK:
            atfork()

        while True:
            try:
                result = self._read_worker_result()
                if result is None:
                    time.sleep(0.1)
                    continue

                host_name = result._host.get_name()

                # send callbacks, execute other options based on the result status
                # FIXME: this should all be cleaned up and probably moved to a sub-function.
                #        the fact that this sometimes sends a TaskResult and other times
                #        sends a raw dictionary back may be confusing, but the result vs.
                #        results implementation for tasks with loops should be cleaned up
                #        better than this
                if result.is_unreachable():
                    self._send_result(('host_unreachable', result))
                elif result.is_failed():
                    self._send_result(('host_task_failed', result))
                elif result.is_skipped():
                    self._send_result(('host_task_skipped', result))
                else:
                    # if this task is notifying a handler, do it now
                    if result._task.notify:
                        # The shared dictionary for notified handlers is a proxy, which
                        # does not detect when sub-objects within the proxy are modified.
                        # So, per the docs, we reassign the list so the proxy picks up and
                        # notifies all other threads
                        for notify in result._task.notify:
                            self._send_result(('notify_handler', result._host, notify))

                    if result._task.loop:
                        # this task had a loop, and has more than one result, so
                        # loop over all of them instead of a single result
                        result_items = result._result['results']
                    else:
                        result_items = [ result._result ]

                    for result_item in result_items:
                        #if 'include' in result_item:
                        #    include_variables = result_item.get('include_variables', dict())
                        #    if 'item' in result_item:
                        #        include_variables['item'] = result_item['item']
                        #    self._send_result(('include', result._host, result._task, result_item['include'], include_variables))
                        #elif 'add_host' in result_item:
                        if 'add_host' in result_item:
                            # this task added a new host (add_host module)
                            self._send_result(('add_host', result_item))
                        elif 'add_group' in result_item:
                            # this task added a new group (group_by module)
                            self._send_result(('add_group', result._host, result_item))
                        elif 'ansible_facts' in result_item:
                            # if this task is registering facts, do that now
                            if result._task.action in ('set_fact', 'include_vars'):
                                for (key, value) in result_item['ansible_facts'].iteritems():
                                    self._send_result(('set_host_var', result._host, key, value))
                            else:
                                self._send_result(('set_host_facts', result._host, result_item['ansible_facts']))

                    # finally, send the ok for this task
                    self._send_result(('host_task_ok', result))

                # if this task is registering a result, do it now
                if result._task.register:
                    self._send_result(('set_host_var', result._host, result._task.register, result._result))

            except queue.Empty:
                pass
            except (KeyboardInterrupt, IOError, EOFError):
                break
            except:
                # FIXME: we should probably send a proper callback here instead of
                #        simply dumping a stack trace on the screen
                traceback.print_exc()
                break

