# (c) 2018-9999, zhikang zhang
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
from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
    strategy: filament_strategy
    short_description: Executes tasks in a linear fashion and do a sleep every tasks
    description:
        - Sleep will occur after all the hosts finished a task and before they ask for a new one.
    version_added: "2.6"
    notes:
     - This is a practice plugin.
    author: Ansible Core Team
'''

import time

from ansible.errors import AnsibleError, AnsibleAssertionError
from ansible.plugins.strategy.linear import StrategyModule as LinearStrategy

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class StrategyModule(LinearStrategy):

    def _get_next_task_lockstep(self, hosts, iterator):
        host_tasks = super(StrategyModule, self)._get_next_task_lockstep(hosts, iterator)
        # if the ansible is running gathering fact or internal meta tasks, do not sleep
        import epdb; epdb.st()
        if host_tasks is not None:
            for host, task in host_tasks:
                if task is not None and (task.action == 'meta' or task.action == 'setup'):
                    return host_tasks
        # if it's a regular playbook task, do sleep
        display.display("----SLEEP----")
        time.sleep(1)
        display.display("----WAKE----")
        return host_tasks
