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
import sys
import time
import traceback

from jinja2.exceptions import TemplateNotFound

from ansible.errors import AnsibleConnectionFailure
from ansible.executor.task_executor import TaskExecutor
from ansible.executor.task_result import TaskResult
from ansible.module_utils._text import to_text

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

__all__ = ['WorkerProcess']


def run_worker(tqm, shared_loader_obj):
    '''
    The worker thread class, which uses TaskExecutor to run tasks
    read from a job queue and pushes results into a results queue
    for reading later.
    '''

    # import cProfile, pstats, StringIO
    # pr = cProfile.Profile()
    # pr.enable()

    display.debug("STARTING WORKER")
    while not tqm._terminated:
        job = tqm.get_job()
        if job is None:
            time.sleep(0.0001)
            continue

        display.debug("WORKER GOT A JOB")
        (host, task, play_context, task_vars) = job

        try:
            # execute the task and build a TaskResult from the result
            display.debug("running TaskExecutor() for %s/%s" % (host, task))
            executor_result = TaskExecutor(
                host,
                task,
                task_vars,
                play_context,
                None, #new_stdin
                tqm._loader,
                shared_loader_obj,
                tqm, #rslt_q
            ).run()

            display.debug("done running TaskExecutor() for %s/%s" % (host, task))

            # put the result on the result queue
            display.debug("sending task result")
            tqm.put_result(TaskResult(
                host,
                task,
                executor_result,
            ))
            display.debug("done task result")

        except AnsibleConnectionFailure:
            tqm.put_result(TaskResult(
                host,
                task,
                dict(unreachable=True),
            ))

        except Exception as e:
            if not isinstance(e, (IOError, EOFError, KeyboardInterrupt, SystemExit)) or isinstance(e, TemplateNotFound):
                try:
                    tqm.put_result(TaskResult(
                        host,
                        task,
                        dict(failed=True, exception=to_text(traceback.format_exc()), stdout=''),
                    ))
                except:
                    display.debug(u"WORKER EXCEPTION: %s" % to_text(e))
                    display.debug(u"WORKER TRACEBACK: %s" % to_text(traceback.format_exc()))

    # pr.disable()
    # s = StringIO.StringIO()
    # sortby = 'time'
    # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    # ps.print_stats()
    # with open('worker_%06d.stats' % os.getpid(), 'w') as f:
    #     f.write(s.getvalue())

    display.debug("WORKER PROCESS EXITING")
