#!/usr/bin/python
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

import copy
import hashlib
import os
import re
import sys
import time
import traceback
import uuid

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text, to_bytes
from ansible.module_utils.connection import Connection
from ansible.plugins.action import ActionBase
from ansible.module_utils.six.moves.urllib.parse import urlsplit
from ansible.utils.display import Display

# From nxos module
from ansible.module_utils.compat.paramiko import paramiko
from ansible.module_utils._text import to_native, to_text, to_bytes
from ansible.module_utils.basic import AnsibleModule


try:
    from scp import SCPClient
    HAS_SCP = True
except ImportError:
    HAS_SCP = False

try:
    import pexpect
    HAS_PEXPECT = True
except ImportError:
    HAS_PEXPECT = False

display = Display()


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        changed = True
        socket_path = None
        play_context = copy.deepcopy(self._play_context)

        result = super(ActionModule, self).run(task_vars=task_vars)

        if play_context.connection != 'network_cli':
            # It is supported only with network_cli
            result['failed'] = True
            result['msg'] = ('please use network_cli connection type for net_put module')
            return result

        # Get playbook values
        pv = self.process_playbook_values()

        return result

    def process_playbook_values(self):
        ''' Get playbook values and perform input validation '''
        argument_spec = dict(
            local_file=dict(type='str'),
            remote_file=dict(type='str'),
            file_system=dict(type='str', default='bootflash:'),
            connect_ssh_port=dict(type='int', default=22),
            file_pull=dict(type='bool', default=False),
            file_pull_timeout=dict(type='int', default=300),
            local_file_directory=dict(type='str'),
            remote_scp_server=dict(type='str'),
            remote_scp_server_user=dict(type='str'),
            remote_scp_server_password=dict(no_log=True),
            vrf=dict(type='str', default='management'),
        )

        required_if = [("file_pull", True, ["remote_file", "remote_scp_server"]),
                       ("file_pull", False, ["local_file"])]

        required_together = [['remote_scp_server',
                              'remote_scp_server_user',
                              'remote_scp_server_password']]

        def check_required(required_if, required_together):
            ''' Helper method to check arg dependencies '''
            import epdb ; epdb.serve()
            test = 'val'

        params = {}
        # Process key value pairs from playbook task
        for key in argument_spec.keys():
            params[key] = self._task.args.get(key, argument_spec[key].get('default'))
            if params[key] is None:
                continue
            if argument_spec[key].get('type') is None:
                argument_spec[key]['type'] = 'str'
            type_ok = False
            type = argument_spec[key]['type']
            if type == 'str':
                if isinstance(params[key], str) or isinstance(params[key], unicode):
                    type_ok = True
            elif type == 'int':
                if isinstance(params[key], int):
                    type_ok = True
            elif type == 'bool':
                if isinstance(params[key], bool):
                    type_ok = True
            else:
                raise ValueError('Unrecognized type <{0}> for arg <{1}>'.format(type, key))

            if not type_ok:
                raise ValueError('Playbook arg <{0}> value should be of type <{1}>'.format(key, type))

            check_required(required_if, required_together)

        return params
