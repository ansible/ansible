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

import os
import pickle
import sys
import traceback

from jinja2.exceptions import TemplateNotFound

HAS_PYCRYPTO_ATFORK = False
try:
    from Crypto.Random import atfork
    HAS_PYCRYPTO_ATFORK = True
except Exception:
    # We only need to call atfork if pycrypto is used because it will need to
    # reinitialize its RNG.  Since old paramiko could be using pycrypto, we
    # need to take charge of calling it.
    pass

from ansible.errors import AnsibleConnectionFailure
from ansible.executor.process.base import AnsibleProcessBase
from ansible.executor.task_executor import TaskExecutor
from ansible.executor.task_result import TaskResult
from ansible.module_utils._text import to_text
from ansible.module_utils.six import iteritems
from ansible.module_utils.urls import ParseResultDottedDict as DottedDict
from ansible.plugins import new_loader as plugin_loader
from ansible.plugins.new_loader import add_all_plugin_dirs
from ansible.utils.cpu import mask_to_bytes, sched_setaffinity
from ansible.utils.display import Display
from ansible.utils.inventory import add_host, add_group
from ansible.utils.sentinel import Sentinel


__all__ = ['WorkerProcess']

display = Display()


class WorkerProcess(AnsibleProcessBase):
    '''
    The worker thread class, which uses TaskExecutor to run tasks
    read from a job queue and pushes results into a results queue
    for reading later.
    '''

    def __init__(self, in_q, final_q, hostvars, loader):

        super(WorkerProcess, self).__init__()

        self._in_q = in_q
        self._final_q = final_q
        self._hostvars = hostvars
        self._loader = loader

    def _save_stdin(self):
        self._new_stdin = os.devnull
        try:
            if sys.stdin.isatty() and sys.stdin.fileno() is not None:
                try:
                    self._new_stdin = os.fdopen(os.dup(sys.stdin.fileno()))
                except OSError:
                    # couldn't dupe stdin, most likely because it's
                    # not a valid file descriptor, so we just rely on
                    # using the one that was passed in
                    pass
        except (AttributeError, ValueError):
            # couldn't get stdin's fileno, so we just carry on
            pass

    def start(self):
        '''
        multiprocessing.Process replaces the worker's stdin with a new file
        opened on os.devnull, but we wish to preserve it if it is connected to
        a terminal. Therefore dup a copy prior to calling the real start(),
        ensuring the descriptor is preserved somewhere in the new child, and
        make sure it is closed in the parent when start() completes.
        '''

        self._save_stdin()
        try:
            return super(WorkerProcess, self).start()
        finally:
            if self._new_stdin != os.devnull:
                self._new_stdin.close()

    def _run(self):
        '''
        Called when the process is started.  Pushes the result onto the
        results queue. We also remove the host from the blocked hosts list, to
        signify that they are ready for their next task.
        '''

        if HAS_PYCRYPTO_ATFORK:
            atfork()

        # every CPU except 0 and 1
        # s = mask_to_bytes(0xFFFFFFFFFFFFFFFC)
        # sched_setaffinity(os.getpid(), len(s), s)

        while True:
            try:
                job = self._in_q.get()
                if job is Sentinel:
                    break

                display.debug("worker got a job")
                host, task, pc, vars_path, worker_update = job
                host = DottedDict(host)
                task = DottedDict(task)
                pc = DottedDict(pc)

                # process worker state updates
                for update in worker_update:
                    display.debug("processing worker update: %s" % (update,))
                    if 'add_host' in update:
                        add_host(update['add_host'], self._hostvars._inventory)
                    elif 'add_group' in update:
                        add_group(update['host'], update['add_group'], self._hostvars._inventory)
                    elif 'plugin_path' in update:
                        add_all_plugin_dirs(update['plugin_path'])
                    elif 'host_vars' in update:
                        # facts that came in as an include_vars result, this is the
                        # same code the results processing does in strategy/Base
                        for (var_name, var_value) in iteritems(update['host_vars']):
                            for target_host in update['host_list']:
                                self._hostvars._variable_manager.set_host_variable(target_host, var_name, var_value)

                # read in task vars from the temp file and clean it up
                display.debug("reading task vars file")
                with open(vars_path, 'rb') as f:
                    task_vars = pickle.load(f)

                try:
                    os.unlink(vars_path)
                except IOError as e:
                    pass

                # re-add the hostvars to task_vars (which were excluded on the main proc side)
                task_vars['hostvars'] = self._hostvars

                # run it!
                display.debug("running TaskExecutor")
                te = TaskExecutor(
                    host=host,
                    task=task,
                    job_vars=task_vars,
                    play_context=pc,
                    new_stdin=self._new_stdin,
                    loader=self._loader,
                    shared_loader_obj=plugin_loader,
                    final_q=self._final_q,
                )
                result = te.run()
                display.debug("done running TaskExecutor, returning result")
                self._final_q.put(
                    TaskResult(
                        host=host,
                        task=task,
                        return_data=result,
                    ),
                    block=True
                )
                display.debug("worker done running job")
            except Exception as e:
                display.debug("WORKER EXCEPTION: %s" % str(e))
                display.debug('Callback Exception: \n' + ' '.join(traceback.format_tb(sys.exc_info()[2])))
                task_result = TaskResult(
                    host=host,
                    task=task,
                    return_data=dict(failed=True, exception=to_text(traceback.format_exc()), stdout=''),
                )
                self._final_q.put(task_result, block=True)

        display.debug("WORKER PROCESS EXITING")
