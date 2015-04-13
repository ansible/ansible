# (c) 2013-2014, Benno Joy <benno@ansible.com>
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

import os

from types import NoneType

from ansible.errors import AnsibleError
from ansible.parsing import DataLoader
from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=dict()):

        source = self._task.args.get('_raw_params')

        if self._task._role:
            source = self._loader.path_dwim_relative(self._task._role._role_path, 'vars', source)
        else:
            source = self._loader.path_dwim(source)

        if os.path.exists(source):
            data = self._loader.load_from_file(source)
            if data is None:
                data = {}
            if not isinstance(data, dict):
                raise AnsibleError("%s must be stored as a dictionary/hash" % source)
            return dict(ansible_facts=data)
        else:
            return dict(failed=True, msg="Source file not found.", file=source)

