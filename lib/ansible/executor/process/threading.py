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


def run_worker(task_vars, host, task, play_context, loader, variable_manager, shared_loader_obj):
    '''
    The worker thread class, which uses TaskExecutor to run tasks
    read from a job queue and pushes results into a results queue
    for reading later.
    '''

    # import cProfile, pstats, StringIO
    # pr = cProfile.Profile()
    # pr.enable()

    try:
        # execute the task and build a TaskResult from the result
        display.debug("running TaskExecutor() for %s/%s" % (host, task))
        executor_result = TaskExecutor(
            host,
            task,
            task_vars,
            play_context,
            None, #new_stdin
            loader,
            shared_loader_obj,
            None, #rslt_q
        ).run()

        display.debug("done running TaskExecutor() for %s/%s" % (host, task))
        task_result = TaskResult(
            host,
            task,
            executor_result,
        )

        # put the result on the result queue
        display.debug("sending task result")
        return task_result

    except AnsibleConnectionFailure:
        return TaskResult(
            host,
            task,
            dict(unreachable=True),
        )

    except Exception as e:
        if not isinstance(e, (IOError, EOFError, KeyboardInterrupt, SystemExit)) or isinstance(e, TemplateNotFound):
            try:
                return TaskResult(
                    host,
                    task,
                    dict(failed=True, exception=to_text(traceback.format_exc()), stdout=''),
                )
            except:
                display.debug(u"WORKER EXCEPTION: %s" % to_text(e))
                display.debug(u"WORKER TRACEBACK: %s" % to_text(traceback.format_exc()))

    display.debug("WORKER PROCESS EXITING")

    # pr.disable()
    # s = StringIO.StringIO()
    # sortby = 'time'
    # ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    # ps.print_stats()
    # with open('worker_%06d.stats' % os.getpid(), 'w') as f:
    #     f.write(s.getvalue())
