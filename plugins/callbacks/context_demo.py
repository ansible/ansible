# (C) 2012, Michael DeHaan, <michael.dehaan@gmail.com>

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

import os
import time
import json

class CallbackModule(object):
    """
    This is a very trivial example of how any callback function can get at play and task objects.
    play will be 'None' for runner invocations, and task will be None for 'setup' invocations.
    """

    def on_any(self, *args, **kwargs):
        play = getattr(self, 'play', None)
        task = getattr(self, 'task', None)
        print "play = %s, task = %s, args = %s, kwargs = %s" % (play,task,args,kwargs)
