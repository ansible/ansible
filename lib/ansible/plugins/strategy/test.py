# (c) 2016, Radware LTD.

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


from ansible.plugins.strategy import linear

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class StrategyModule(linear.StrategyModule):
    """
    The "test" strategy implements the linear strategy, while making sure
    that tasks of action type "assert" will not stop the entire play on failure.
    This makes running test plays a little more similar to running tests - don't
    stop running tests on the first failure, but run the entire test suite.

    This strategy is best used with the assert_su



    mmary callback plugin, so that once
    the test play has completed running it'll generate a detailed report of the
    tests run in the play.

    Assumptions:
      test plays are play where each regular task is followed by an "assert" task checking that
      the previous task completed in a predetermined state (whether failed or succeeded)

      The regular tasks should have ignore_errors set to true and register their output under the variable "result"

    The strategy sets ignore_errors = True for "assert" tasks and adds the results of the previous tasks to the task
    args so they are easily accessible to the reporting plugin.
    """

    def __init__(self, tqm):
        self.curr_tqm = tqm
        super(StrategyModule, self).__init__(tqm)

    def _queue_task(self, host, task, task_vars, play_context):
        """
        set ignore_errors: yes for tasks of action type 'assert' and
        add the registered data from the previous task to the current task's args
        """

        self.curr_host = host
        self.curr_task = task
        self.curr_task_vars = task_vars
        self.curr_play_context = play_context

        if task.action == "assert":
            task.ignore_errors = True
            task.args['last'] = "{{ result }}"

        super(StrategyModule, self)._queue_task(host, task, task_vars, play_context)