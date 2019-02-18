# (c) 2017, Red Hat, Inc. <support@ansible.com>
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

import multiprocessing
import signal
import threading

from abc import ABCMeta, abstractmethod
from collections import deque

from ansible.executor.shared_plugin_loader import SharedPluginLoaderObj
from ansible.module_utils.six import with_metaclass

__all__ = ["ProcessModelBase", "keyboard_interrupt_event", "ResultsSentinel"]


class ResultsSentinel:
    pass


keyboard_interrupt_event = multiprocessing.Event()


def keyboard_interrupt_handler(signum, frame):
    keyboard_interrupt_event.set()


class ProcessModelBase(with_metaclass(ABCMeta, object)):

    def __init__(self, tqm):
        self._terminated = False
        self._tqm = tqm
        # the sentinel object used to terminate things listening on queues
        self._sentinel = ResultsSentinel()
        # the final queue results are copied to, whether from forks or threads
        self._final_q = deque()
        # a lock used to synchronize around the final_q
        self._final_q_lock = threading.Condition(threading.Lock())
        self._workers = None
        self._cur_worker = 0

        # the shared loader object is used to send updated versions of
        # the plugin loader objects to the forked processes. Since we no
        # longer have long-running forked processes, this is not strictly
        # necessary, but it does cut down on the number of params we have
        # to send to the new fork
        self._shared_loader_obj = SharedPluginLoaderObj()

        # tie SIGINT to our custom handler which will set an event
        signal.signal(signal.SIGINT, keyboard_interrupt_handler)

    def terminate(self):
        self._terminated = True

    def get_result(self):
        data = None
        try:
            self._final_q_lock.acquire()
            data = self._final_q.popleft()
        except Exception as e:
            pass
        finally:
            self._final_q_lock.release()
        return data

    @abstractmethod
    def initialize_workers(self, num):
        pass

    @abstractmethod
    def put_job(self, data):
        pass

    @abstractmethod
    def put_result(self, data):
        pass

    @abstractmethod
    def cleanup(self):
        pass
