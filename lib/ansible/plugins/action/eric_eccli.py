#
# Copyright (c) 2019 Ericsson AB.
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


import re
import sys
import copy

from ansible.plugins.action.normal import ActionModule as _ActionModule
from ansible.module_utils._text import to_text
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils.network.common.utils import load_provider
from ansible.module_utils.network.ios.ios import ios_provider_spec
from ansible.utils.display import Display

display = Display()


class ActionModule(_ActionModule):

    def run(self, tmp=None, task_vars=None):
        if self._play_context.connection != 'network_cli':
            return {'failed': True, 'msg': 'Connection type %s is not valid for cli_config module' % self._play_context.connection}

        return super(ActionModule, self).run(task_vars=task_vars)
