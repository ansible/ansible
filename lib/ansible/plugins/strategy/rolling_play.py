# (c) 2023, Max Gautier <mg@max.gautier.name>
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

DOCUMENTATION = '''
    name: rolling_play
    short_description: Execute a whole play in a rolling update manner
    description:
        - Same behavior as the 'host_pinned' strategy, except for 'throttle' which is used as "the maximum number of hosts running the whole
          play at once".
          Note that using this strategy without the 'throttle' parameter at the play level makes little sense.
    version_added: "2.17"
    author: Max Gautier
'''

from ansible.plugins.strategy.free import StrategyModule as FreeStrategyModule
from ansible.utils.display import Display

display = Display()


class StrategyModule(FreeStrategyModule):

    def __init__(self, tqm):
        super(StrategyModule, self).__init__(tqm)
        self._host_pinned = True
        self._rolling_play = True
