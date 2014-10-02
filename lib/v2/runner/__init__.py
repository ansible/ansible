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

from v2.inventory import Host
from v2.playbook import Task

class Runner(object):
    def __init__(self, host, task):
        self.host   = host
        self.task   = task
        self.action = self.get_action()

    def get_action(self):
        # returns the action plugin from plugins/action/
        # for the given task
        return None

    def execute(self):
        # runs the given task on the given host using
        # the action determined by get_action()
        return

