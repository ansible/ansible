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

class PlaybookState:

   '''
   A helper class, which keeps track of the task iteration
   state for a given playbook. This is used in the PlaybookIterator
   class on a per-host basis.
   '''
   def __init__(self, parent_iterator):
       self._parent_iterator = parent_iterator
       self._cur_play        = 0
       self._task_list       = None
       self._cur_task_pos    = 0

   def next(self):
       '''
       Determines and returns the next available task from the playbook,
       advancing through the list of plays as it goes.
       '''

       while True:
           # when we hit the end of the playbook entries list, we return
           # None to indicate we're there
           if self._cur_play > len(self._parent_iterator._playbook._entries) - 1:
               return None

           # initialize the task list by calling the .compile() method
           # on the play, which will call compile() for all child objects
           if self._task_list is None:
               self._task_list = self._parent_iterator._playbook._entries[self._cur_play].compile()

           # if we've hit the end of this plays task list, move on to the next
           # and reset the position values for the next iteration
           if self._cur_task_pos > len(self._task_list) - 1:
               self._cur_play += 1
               self._task_list = None
               self._cur_task_pos = 0
               continue
           else:
               # FIXME: do tag/conditional evaluation here and advance
               #        the task position if it should be skipped without
               #        returning a task
               task = self._task_list[self._cur_task_pos]
               self._cur_task_pos += 1

               # Skip the task if it is the member of a role which has already
               # been run, unless the role allows multiple executions
               if task._role:
                   # FIXME: this should all be done via member functions
                   #        instead of direct access to internal variables
                   if task._role.has_run() and not task._role._metadata._allow_duplicates:
                       continue

               return task

class PlaybookIterator:

   '''
   The main iterator class, which keeps the state of the playbook
   on a per-host basis using the above PlaybookState class.
   '''

   def __init__(self, inventory, log_manager, playbook):
       self._playbook     = playbook
       self._log_manager  = log_manager
       self._host_entries = dict()

       # build the per-host dictionary of playbook states
       for host in inventory.get_hosts():
           self._host_entries[host.get_name()] = PlaybookState(parent_iterator=self)

   def get_next_task_for_host(self, host):
       ''' fetch the next task for the given host '''
       if host.get_name() not in self._host_entries:
           raise AnsibleError("invalid host specified for playbook iteration")

       return self._host_entries[host.get_name()].next()
