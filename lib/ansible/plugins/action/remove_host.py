# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright 2012, Seth Vidal <skvidal@fedoraproject.org>
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

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    ''' Remove an inventory host from the memory inventory'''

    # We need to be able to modify the inventory
    BYPASS_HOST_LOOP = True
    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        host_name = self._task.args.get('name')

        if self._play_context.check_mode:
            result['skipped'] = True
            result['msg'] = 'check mode not supported for this module'
            return result

        result['changed'] = True
        result['remove_host'] = dict(host_name=host_name)
        return result
