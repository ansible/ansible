#
# (c) 2017 Red Hat Inc.
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

import json

from itertools import chain

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase
from ansible.plugins.connection.network_cli import Connection as NetworkCli


class Cliconf(CliconfBase):

    def send_command(self, command, prompt=None, answer=None, sendonly=False, newline=True, prompt_retry_check=False):
        """Executes a cli command and returns the results
        This method will execute the CLI command on the connection and return
        the results to the caller.  The command output will be returned as a
        string
        """
        kwargs = {'command': to_bytes(command), 'sendonly': sendonly,
                  'newline': newline, 'prompt_retry_check': prompt_retry_check}
        if prompt is not None:
            kwargs['prompt'] = to_bytes(prompt)
        if answer is not None:
            kwargs['answer'] = to_bytes(answer)

        if isinstance(self._connection, NetworkCli):
            resp = self._connection.send(**kwargs)
        else:
            resp = self._connection.send_request(command, **kwargs)
        return resp

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'nxos'
        reply = self.get('show version | json')
        data = json.loads(reply)
        platform_reply = self.get('show inventory | json')
        platform_info = json.loads(platform_reply)

        device_info['network_os_version'] = data.get('sys_ver_str') or data.get('kickstart_ver_str')
        device_info['network_os_model'] = data['chassis_id']
        device_info['network_os_hostname'] = data['host_name']
        device_info['network_os_image'] = data.get('isan_file_name') or data.get('kick_file_name')

        inventory_table = platform_info['TABLE_inv']['ROW_inv']
        for info in inventory_table:
            if 'Chassis' in info['name']:
                device_info['network_os_platform'] = info['productid']

        return device_info

    def get_config(self, source='running', format='text', flags=None):
        lookup = {'running': 'running-config', 'startup': 'startup-config'}

        cmd = 'show {0} '.format(lookup[source])
        if flags:
            cmd += ' '.join(flags)
        cmd = cmd.strip()

        return self.send_command(cmd)

    def edit_config(self, command):
        responses = []
        for cmd in chain(['configure'], to_list(command), ['end']):
            responses.append(self.send_command(cmd))

        return json.dumps(responses)

    def get(self, command, prompt=None, answer=None, sendonly=False):
        return self.send_command(command, prompt=prompt, answer=answer, sendonly=sendonly)

    def get_capabilities(self):
        result = {}
        result['rpc'] = self.get_base_rpc()
        result['device_info'] = self.get_device_info()
        if isinstance(self._connection, NetworkCli):
            result['network_api'] = 'cliconf'
        else:
            result['network_api'] = 'nxapi'
        return json.dumps(result)

    # Migrated from module_utils
    def run_commands(self, commands, check_rc=True):
        """Run list of commands on remote device and return results
        """
        responses = list()

        for item in to_list(commands):
            if item['output'] == 'json' and not item['command'].endswith('| json'):
                cmd = '%s | json' % item['command']
            elif item['output'] == 'text' and item['command'].endswith('| json'):
                cmd = item['command'].rsplit('|', 1)[0]
            else:
                cmd = item['command']

            try:
                out = self.get(cmd)
            except AnsibleConnectionFailure as e:
                if check_rc:
                    raise
                out = getattr(e, 'err', e)

            try:
                out = to_text(out, errors='surrogate_or_strict').strip()
            except UnicodeError:
                raise ConnectionError(msg=u'Failed to decode output from %s: %s' % (cmd, to_text(out)))

            try:
                out = json.loads(out)
            except ValueError:
                pass

            responses.append(out)
        return responses
