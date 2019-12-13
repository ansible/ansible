#
# Copyright 2018 Red Hat Inc.
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
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action.network import ActionModule as ActionNetworkModule


class ActionModule(ActionNetworkModule):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        self._config_module = True

        if self._play_context.connection.split('.')[-1] != 'network_cli':
            return {'failed': True, 'msg': 'Connection type %s is not valid for this module. Must use fully qualified'
                                           ' name of network_cli connection type.' % self._play_context.connection}

        return super(ActionModule, self).run(task_vars=task_vars)
