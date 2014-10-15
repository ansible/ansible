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

class PlaybookExecutor:

   def __init__(self, list_of_plays=[]):
       # self.tqm = TaskQueueManager(forks)
       assert False

   def run(self):
       # for play in list_of_plays:
       #    for block in play.blocks:
       #        # block must know it’s playbook class and context
       #        tqm.enqueue(block)
       #        tqm.go()...	
       assert False

