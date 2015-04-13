# Copyright 2012, Jeroen Hoekx <jeroen@hoekx.be>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import *
from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):
    ''' Create inventory groups based on variables '''

    ### We need to be able to modify the inventory
    BYPASS_HOST_LOOP = True
    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=dict()):

        if not 'key' in self._task.args:
            return dict(failed=True, msg="the 'key' param is required when using group_by")

        group_name = self._task.args.get('key')
        group_name = group_name.replace(' ','-')

        return dict(changed=True, add_group=group_name)

