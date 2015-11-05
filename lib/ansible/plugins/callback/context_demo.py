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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback import CallbackBase

class CallbackModule(CallbackBase):
    """
    This is a very trivial example of how any callback function can get at play and task objects.
    play will be 'None' for runner invocations, and task will be None for 'setup' invocations.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'context_demo'
    CALLBACK_NEEDS_WHITELIST = True

    def v2_on_any(self, *args, **kwargs):
        i = 0
        self._display.display("     --- ARGS ")
        for a in args:
            self._display.display('     %s: %s' % (i, a))
            i += 1

        self._display.display("      --- KWARGS ")
        for k in kwargs:
            self._display.display('     %s: %s' % (k, kwargs[k]))
