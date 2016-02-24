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

import json
import multiprocessing
import os
import signal
import sys
import time
import traceback
import zlib

from jinja2.exceptions import TemplateNotFound

# TODO: not needed if we use the cryptography library with its default RNG
# engine
HAS_ATFORK=True
try:
    from Crypto.Random import atfork
except ImportError:
    HAS_ATFORK=False

from ansible.errors import AnsibleError, AnsibleConnectionFailure
from ansible.executor.task_executor import TaskExecutor
from ansible.executor.task_result import TaskResult
from ansible.playbook.handler import Handler
from ansible.playbook.task import Task
from ansible.vars.unsafe_proxy import AnsibleJSONUnsafeDecoder

from ansible.utils.debug import debug
from ansible.utils.unicode import to_unicode

__all__ = ['WorkerProcess']


class WorkerProcess(multiprocessing.Process):
    '''
    The worker thread class, which uses TaskExecutor to run tasks
    read from a job queue and pushes results into a results queue
    for reading later.
    '''

    def __init__(self, rslt_q, task_vars, host, task, play_context, loader, variable_manager, shared_loader_obj):

        super(WorkerProcess, self).__init__()
        # takes a task queue manager as the sole param:
        self._rslt_q            = rslt_q
        self._task_vars         = task_vars
        self._host              = host
        self._task              = task
        self._play_context      = play_context
        self._loader            = loader
        self._variable_manager  = variable_manager
        self._shared_loader_obj = shared_loader_obj

        # dupe stdin, if we have one
        self._new_stdin = sys.stdin
        try:
            fileno = sys.stdin.fileno()
            if fileno is not None:
                try:
                    self._new_stdin = os.fdopen(os.dup(fileno))
                except OSError:
                    # couldn't dupe stdin, most likely because it's
                    # not a valid file descriptor, so we just rely on
                    # using the one that was passed in
                    pass
        except ValueError:
            # couldn't get stdin's fileno, so we just carry on
            pass

    def run(self):
        '''
        Called when the process is started, and loops indefinitely
        until an error is encountered (typically an IOerror from the
        queue pipe being disconnected). During the loop, we attempt
        to pull tasks off the job queue and run them, pushing the result
        onto the results queue. We also remove the host from the blocked
        hosts list, to signify that they are ready for their next task.
        '''

        if HAS_ATFORK:
            atfork()

        try:
            # execute the task and build a TaskResult from the result
            debug("running TaskExecutor() for %s/%s" % (self._host, self._task))
            executor_result = TaskExecutor(
                self._host,
                self._task,
                self._task_vars,
                self._play_context,
                self._new_stdin,
                self._loader,
                self._shared_loader_obj,
                self._rslt_q
            ).run()

            debug("done running TaskExecutor() for %s/%s" % (self._host, self._task))
            self._host.vars = dict()
            self._host.groups = []
            task_result = TaskResult(self._host, self._task, executor_result)

            # put the result on the result queue
            debug("sending task result")
            self._rslt_q.put(task_result)
            debug("done sending task result")

        except AnsibleConnectionFailure:
            self._host.vars = dict()
            self._host.groups = []
            task_result = TaskResult(self._host, self._task, dict(unreachable=True))
            self._rslt_q.put(task_result, block=False)

        except Exception as e:
            if not isinstance(e, (IOError, EOFError, KeyboardInterrupt, SystemExit)) or isinstance(e, TemplateNotFound):
                try:
                    self._host.vars = dict()
                    self._host.groups = []
                    task_result = TaskResult(self._host, self._task, dict(failed=True, exception=to_unicode(traceback.format_exc()), stdout=''))
                    self._rslt_q.put(task_result, block=False)
                except:
                    debug(u"WORKER EXCEPTION: %s" % to_unicode(e))
                    debug(u"WORKER TRACEBACK: %s" % to_unicode(traceback.format_exc()))

        debug("WORKER PROCESS EXITING")

