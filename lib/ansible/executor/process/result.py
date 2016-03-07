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

from ansible.compat.six.moves import queue
from ansible.compat.six import iteritems, text_type
from ansible.vars import strip_internal_keys

import multiprocessing
import time
import traceback

# TODO: not needed if we use the cryptography library with its default RNG
# engine
HAS_ATFORK=True
try:
    from Crypto.Random import atfork
except ImportError:
    HAS_ATFORK=False

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
        debug(u"sending result: %s" % ([text_type(x) for x in result],))
        self._final_q.put(result)
        debug("done sending result")

    def _read_worker_result(self):
        result = None
        starting_point = self._cur_worker
        while True:
            (worker_prc, rslt_q) = self._workers[self._cur_worker]
            self._cur_worker += 1
            if self._cur_worker >= len(self._workers):
                self._cur_worker = 0

            try:
                if not rslt_q.empty():
                    debug("worker %d has data to read" % self._cur_worker)
                    result = rslt_q.get()
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
                    time.sleep(0.0001)
                    continue

                # send callbacks for 'non final' results
                if '_ansible_retry' in result._result:
                    self._send_result(('v2_playbook_retry', result))
                    continue
                elif '_ansible_item_result' in result._result:
                    if result.is_failed() or result.is_unreachable():
                        self._send_result(('v2_playbook_item_on_failed', result))
                    elif result.is_skipped():
                        self._send_result(('v2_playbook_item_on_skipped', result))
                    else:
                        self._send_result(('v2_playbook_item_on_ok', result))
                        if 'diff' in result._result:
                            self._send_result(('v2_on_file_diff', result))
                    continue

                clean_copy = strip_internal_keys(result._result)
                if 'invocation' in clean_copy:
                    del clean_copy['invocation']

                # if this task is registering a result, do it now
                if result._task.register:
                    self._send_result(('register_host_var', result._host, result._task, clean_copy))

                # send callbacks, execute other options based on the result status
                # TODO: this should all be cleaned up and probably moved to a sub-function.
                #       the fact that this sometimes sends a TaskResult and other times
                #       sends a raw dictionary back may be confusing, but the result vs.
                #       results implementation for tasks with loops should be cleaned up
                #       better than this
                if result.is_unreachable():
                    self._send_result(('host_unreachable', result))
                elif result.is_failed():
                    self._send_result(('host_task_failed', result))
                elif result.is_skipped():
                    self._send_result(('host_task_skipped', result))
                else:
                    if result._task.loop:
                        # this task had a loop, and has more than one result, so
                        # loop over all of them instead of a single result
                        result_items = result._result['results']
                    else:
                        result_items = [ result._result ]

                    for result_item in result_items:
                        # if this task is notifying a handler, do it now
                        if '_ansible_notify' in result_item:
                            if result.is_changed():
                                # The shared dictionary for notified handlers is a proxy, which
                                # does not detect when sub-objects within the proxy are modified.
                                # So, per the docs, we reassign the list so the proxy picks up and
                                # notifies all other threads
                                for notify in result_item['_ansible_notify']:
                                    self._send_result(('notify_handler', result, notify))

                        if 'add_host' in result_item:
                            # this task added a new host (add_host module)
                            self._send_result(('add_host', result_item))
                        elif 'add_group' in result_item:
                            # this task added a new group (group_by module)
                            self._send_result(('add_group', result._host, result_item))
                        elif 'ansible_facts' in result_item:
                            # if this task is registering facts, do that now
                            item = result_item.get('item', None)
                            if result._task.action == 'include_vars':
                                for (key, value) in iteritems(result_item['ansible_facts']):
                                    self._send_result(('set_host_var', result._host, result._task, item, key, value))
                            else:
                                self._send_result(('set_host_facts', result._host, result._task, item, result_item['ansible_facts']))

                    # finally, send the ok for this task
                    self._send_result(('host_task_ok', result))

            except queue.Empty:
                pass
            except (KeyboardInterrupt, SystemExit, IOError, EOFError):
                break
            except:
                # TODO: we should probably send a proper callback here instead of
                #       simply dumping a stack trace on the screen
                traceback.print_exc()
                break

