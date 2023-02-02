# Copyright: (c) 2023, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.utils.display import Display
from ansible.utils.multiprocessing import context as multiprocessing_context

import sys

display = Display()


# subclass current module to define getters/setters
class WorkerSync(sys.modules[__name__].__class__):  # type: ignore[misc]
    _worker_id = None
    _worker_q = None

    @property
    def worker_queue(self):
        if self._worker_q is None:
            raise ImportError("worker_queue cannot be imported outside of the WorkerProcess")
        return self._worker_q

    @worker_queue.setter
    def worker_queue(self, value):
        if multiprocessing_context.parent_process() is not None:
            raise NotImplementedError
        self._worker_q = value

    @property
    def worker_id(self):
        if self._worker_id is None:
            raise ImportError("worker_id cannot be imported outside of the WorkerProcess")
        return self._worker_id

    @worker_id.setter
    def worker_id(self, value):
        if multiprocessing_context.parent_process() is not None:
            raise NotImplementedError
        self._worker_id = value

    def send_prompt(self, **kwargs):
        if self._worker_id is None:
            raise ImportError("send_prompt cannot be imported outside of the WorkerProcess")
        display._final_q.send_prompt(worker_id=self._worker_id, **kwargs)


sys.modules[__name__].__class__ = WorkerSync
