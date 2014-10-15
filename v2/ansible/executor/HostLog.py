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

class HostLog:

   def __init__(self, host):
       self.host = host

   def add_task_result(self, task_result):
       pass

   def has_failures(self):
       assert False

   def has_changes(self):
       assert False

   def get_tasks(self, are_executed=None, are_changed=None, are_successful=None):
       assert False

   def get_current_running_task(self)
       # atomic decorator likely required?
       assert False


