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
import time

from itertools import chain

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase, enable_mode
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

        device_info['network_os'] = 'eos'
        reply = self.get('show version | json')
        data = json.loads(reply)

        device_info['network_os_version'] = data['version']
        device_info['network_os_model'] = data['modelName']

        reply = self.get('show hostname | json')
        data = json.loads(reply)

        device_info['network_os_hostname'] = data['hostname']

        return device_info

    @enable_mode
    def get_config(self, source='running', format='text', flags=None):
        lookup = {'running': 'running-config', 'startup': 'startup-config'}
        if source not in lookup:
            return self.invalid_params("fetching configuration from %s is not supported" % source)

        cmd = 'show %s ' % lookup[source]
        if format and format is not 'text':
            cmd += '| %s ' % format

        cmd += ' '.join(to_list(flags))
        cmd = cmd.strip()
        return self.send_command(cmd)

    @enable_mode
    def edit_config(self, command):
        for cmd in chain(['configure'], to_list(command), ['end']):
            self.send_command(cmd)

    def get(self, command, prompt=None, answer=None, sendonly=False):
        return self.send_command(command, prompt=prompt, answer=answer, sendonly=sendonly)

    def get_capabilities(self):
        result = {}
        result['rpc'] = self.get_base_rpc()
        result['device_info'] = self.get_device_info()
        if isinstance(self._connection, NetworkCli):
            result['network_api'] = 'cliconf'
        else:
            result['network_api'] = 'eapi'
        return json.dumps(result)

    # Imported from module_utils
    def close_session(self, session):
        # to close session gracefully execute abort in top level session prompt.
        self.get('end')
        self.get('configure session %s' % session)
        self.get('abort')

    def run_commands(self, commands, check_rc=True):
        """Run list of commands on remote device and return results
        """
        responses = list()
        multiline = False

        for cmd in to_list(commands):
            if isinstance(cmd, dict):
                command = cmd['command']
                prompt = cmd['prompt']
                answer = cmd['answer']
            else:
                command = cmd
                prompt = None
                answer = None

            if command == 'end':
                continue
            elif command.startswith('banner') or multiline:
                multiline = True
            elif command == 'EOF' and multiline:
                multiline = False

            try:
                out = self.get(command, prompt, answer, multiline)
            except AnsibleConnectionFailure as e:
                if check_rc:
                    raise
                out = getattr(e, 'err', e)
            out = to_text(out, errors='surrogate_or_strict')

            if out is not None:
                try:
                    out = json.loads(out)
                except ValueError:
                    out = out.strip()

                responses.append(out)

        return responses

    def load_config(self, commands, commit=False, replace=False):
        """Loads the config commands onto the remote device
        """
        session = 'ansible_%s' % int(time.time())
        result = {'session': session}

        self.get('configure session %s' % session)
        if replace:
            self.get('rollback clean-config')

        try:
            self.run_commands(commands)
        except AnsibleConnectionFailure:
            self.close_session(session)
            raise

        out = self.get('show session-config diffs')
        if out:
            result['diff'] = out.strip()

        if commit:
            self.get('commit')
        else:
            self.close_session(session)

        return result
