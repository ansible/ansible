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

from multiprocessing.managers import SyncManager, BaseProxy
from ansible.playbook.handler import Handler
from ansible.playbook.task import Task
from ansible.playbook.play import Play
from ansible.errors import AnsibleError

__all__ = ['AnsibleManager']


class VariableManagerWrapper:
    '''
    This class simply acts as a wrapper around the VariableManager class,
    since manager proxies expect a new object to be returned rather than
    any existing one. Using this wrapper, a shared proxy can be created
    and an existing VariableManager class assigned to it, which can then
    be accessed through the exposed proxy methods.
    '''

    def __init__(self):
        self._vm = None

    def get_vars(self, loader, play=None, host=None, task=None):
        return self._vm.get_vars(loader=loader, play=play, host=host, task=task)

    def set_variable_manager(self, vm):
        self._vm = vm

    def set_host_variable(self, host, varname, value):
        self._vm.set_host_variable(host, varname, value)

    def set_host_facts(self, host, facts):
        self._vm.set_host_facts(host, facts)

class AnsibleManager(SyncManager):
    '''
    This is our custom manager class, which exists only so we may register
    the new proxy below
    '''
    pass

AnsibleManager.register(
    typeid='VariableManagerWrapper',
    callable=VariableManagerWrapper,
)

