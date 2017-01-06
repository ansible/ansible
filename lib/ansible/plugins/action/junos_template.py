#
# Copyright 2015 Peter Sprygada <psprygada@ansible.com>
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

from ansible.plugins.action import ActionBase
from ansible.plugins.action.net_template import ActionModule as NetActionModule

class ActionModule(NetActionModule, ActionBase):

    def run(self, tmp=None, task_vars=None):
        src = self._task.args.get('src')

        if self._task.args.get('config_format') is None:
            if src.endswith('.xml'):
                fmt = 'xml'
            elif src.endswith('.set'):
                fmt = 'set'
            else:
                fmt = 'text'

            self._task.args['config_format'] = fmt

        if self._task.args.get('comment') is None:
            self._task.args['comment'] = self._task.name

        return super(ActionModule, self).run(tmp, task_vars)

