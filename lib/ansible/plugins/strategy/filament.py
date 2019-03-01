# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    strategy: filament
    short_description: Executes tasks in a laggy fashion
    description:
        - Task execution is in lockstep per host batch as defined by C(serial) (default all).
          Up to the fork limit of hosts will execute each task at the same time and then
          the next series of hosts until the batch is done, before going on to the next task.
    version_added: "2.0"
    notes:
     - This was the default Ansible behaviour before 'strategy plugins' were introduced in 2.0.
    author: Ansible Core Team
'''

from ansible.plugins.strategy.linear import StrategyModule as linear_sm
from time import sleep


class StrategyModule(linear_sm):

    def __init__(self, tqm):
        super(StrategyModule, self).__init__(tqm)

    def _queue_task(self, host, task, task_vars, play_context):
        super(StrategyModule, self)._queue_task(host, task, task_vars, play_context)
        sleep(1)
