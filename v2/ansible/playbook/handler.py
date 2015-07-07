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

from v2.errors import AnsibleError
from v2.inventory import Host
from v2.playbook import Task

class Handler(Task):

    def __init__(self):
        pass

    def flag_for_host(self, host):
        assert instanceof(host, Host)
        pass

    def has_triggered(self):
        return self._triggered

    def set_triggered(self, triggered):
        assert instanceof(triggered, bool)
        self._triggered = triggered
