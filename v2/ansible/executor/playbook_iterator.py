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
       self._done            = False

   def next(self, peek=False):
       '''
       Determines and returns the next available task from the playbook,
       advancing through the list of plays as it goes.
       '''

       task = None

       # we save these locally so that we can peek at the next task
       # without updating the internal state of the iterator
       cur_play     = self._cur_play
       task_list    = self._task_list
       cur_task_pos = self._cur_task_pos

       while True:
           # when we hit the end of the playbook entries list, we set a flag
           # and return None to indicate we're there
           # FIXME: accessing the entries and parent iterator playbook members
           #        should be done through accessor functions
           if self._done or cur_play > len(self._parent_iterator._playbook._entries) - 1:
               self._done = True
               return None

           # initialize the task list by calling the .compile() method
           # on the play, which will call compile() for all child objects
           if task_list is None:
               task_list = self._parent_iterator._playbook._entries[cur_play].compile()

           # if we've hit the end of this plays task list, move on to the next
           # and reset the position values for the next iteration
           if cur_task_pos > len(task_list) - 1:
               cur_play += 1
               task_list = None
               cur_task_pos = 0
               continue
           else:
               # FIXME: do tag/conditional evaluation here and advance
               #        the task position if it should be skipped without
               #        returning a task
               task = task_list[cur_task_pos]
               cur_task_pos += 1

               # Skip the task if it is the member of a role which has already
               # been run, unless the role allows multiple executions
               if task._role:
                   # FIXME: this should all be done via member functions
                   #        instead of direct access to internal variables
                   if task._role.has_run() and not task._role._metadata._allow_duplicates:
                       continue

               # Break out of the while loop now that we have our task
               break

       # If we're not just peeking at the next task, save the internal state 
       if not peek:
           self._cur_play     = cur_play
           self._task_list    = task_list
           self._cur_task_pos = cur_task_pos

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
       self._first_host   = None

       # build the per-host dictionary of playbook states
       for host in inventory.get_hosts():
           if self._first_host is None:
               self._first_host = host
           self._host_entries[host.get_name()] = PlaybookState(parent_iterator=self)

   def get_next_task(self, peek=False):
       ''' returns the next task for host[0] '''
       return self._host_entries[self._first_host.get_name()].next(peek=peek)

   def get_next_task_for_host(self, host, peek=False):
       ''' fetch the next task for the given host '''
       if host.get_name() not in self._host_entries:
           raise AnsibleError("invalid host specified for playbook iteration")

       return self._host_entries[host.get_name()].next(peek=peek)
