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
from __future__ import annotations

DOCUMENTATION = """
    name: host_pinned
    short_description: Executes tasks on each host without interruption
    description:
        - Task execution is as fast as possible per host in batch as defined by C(serial) (default all).
          Ansible will not start a play for a host unless the play can be finished without interruption by tasks for another host,
          i.e. the number of hosts with an active play does not exceed the number of forks.
          Ansible will not wait for other hosts to finish the current task before queuing the next task for a host that has finished.
          Once a host is done with the play, it opens it's slot to a new host that was waiting to start.
          Other than that, it behaves just like the "free" strategy.
    version_added: "2.7"
    author: Ansible Core Team
"""

from ansible.plugins.strategy.free import StrategyModule as FreeStrategyModule
from ansible.utils.display import Display

display = Display()


class StrategyModule(FreeStrategyModule):

    def __init__(self, tqm):
        super(StrategyModule, self).__init__(tqm)
        self._host_pinned = True
