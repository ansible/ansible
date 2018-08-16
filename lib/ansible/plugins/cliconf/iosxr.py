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

import collections
import re
import json

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase


class Cliconf(CliconfBase):

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'iosxr'
        reply = self.get('show version | utility head -n 20')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'Version (\S+)$', data, re.M)
        if match:
            device_info['network_os_version'] = match.group(1)

        match = re.search(r'image file is "(.+)"', data)
        if match:
            device_info['network_os_image'] = match.group(1)

        match = re.search(r'^Cisco (.+) \(revision', data, re.M)
        if match:
            device_info['network_os_model'] = match.group(1)

        match = re.search(r'^(.+) uptime', data, re.M)
        if match:
            device_info['network_os_hostname'] = match.group(1)

        return device_info

    def configure(self, admin=False):
        prompt = to_text(self._connection.get_prompt(), errors='surrogate_or_strict').strip()
        if not prompt.endswith(')#'):
            if admin and 'admin-' not in prompt:
                self.send_command('admin')
            self.send_command('configure terminal')

    def abort(self, admin=False):
        prompt = to_text(self._connection.get_prompt(), errors='surrogate_or_strict').strip()
        if prompt.endswith(')#'):
            self.send_command('abort')
            if admin and 'admin-' in prompt:
                self.send_command('exit')

    def get_config(self, source='running', format='text', flags=None):
        if source not in ['running']:
            raise ValueError("fetching configuration from %s is not supported" % source)

        lookup = {'running': 'running-config'}

        cmd = 'show {0} '.format(lookup[source])
        cmd += ' '.join(to_list(flags))
        cmd = cmd.strip()

        return self.send_command(cmd)

    def edit_config(self, candidate=None, commit=True, admin=False, replace=None, comment=None, label=None):
        operations = self.get_device_operations()
        self.check_edit_config_capability(operations, candidate, commit, replace, comment)

        resp = {}
        results = []
        requests = []

        self.configure(admin=admin)

        if replace:
            candidate = 'load {0}'.format(replace)

        for line in to_list(candidate):
            if not isinstance(line, collections.Mapping):
                line = {'command': line}
            cmd = line['command']
            results.append(self.send_command(**line))
            requests.append(cmd)

        if commit:
            self.commit(comment=comment, label=label, replace=replace)
        else:
            self.discard_changes()

        self.abort(admin=admin)

        resp['request'] = requests
        resp['response'] = results
        return resp

    def get_diff(self, admin=False):
        self.configure(admin=admin)

        diff = {'config_diff': None}
        response = self.send_command('show commit changes diff')
        for item in response.splitlines():
            if item and item[0] in ['<', '+', '-']:
                diff['config_diff'] = response
                break
        return diff

    def get(self, command=None, prompt=None, answer=None, sendonly=False, newline=True, output=None):
        if output:
            raise ValueError("'output' value %s is not supported for get" % output)
        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline)

    def commit(self, comment=None, label=None, replace=None):
        cmd_obj = {}
        if replace:
            cmd_obj['command'] = 'commit replace'
            cmd_obj['prompt'] = 'This commit will replace or remove the entire running configuration'
            cmd_obj['answer'] = 'yes'
        else:
            if comment and label:
                cmd_obj['command'] = 'commit label {0} comment {1}'.format(label, comment)
            elif comment:
                cmd_obj['command'] = 'commit comment {0}'.format(comment)
            elif label:
                cmd_obj['command'] = 'commit label {0}'.format(label)
            else:
                cmd_obj['command'] = 'commit'

        self.send_command(**cmd_obj)

    def run_commands(self, commands=None, check_rc=True):
        if commands is None:
            raise ValueError("'commands' value is required")
        responses = list()
        for cmd in to_list(commands):
            if not isinstance(cmd, collections.Mapping):
                cmd = {'command': cmd}

            output = cmd.pop('output', None)
            if output:
                raise ValueError("'output' value %s is not supported for run_commands" % output)

            try:
                out = self.send_command(**cmd)
            except AnsibleConnectionFailure as e:
                if check_rc:
                    raise
                out = getattr(e, 'err', e)

            if out is not None:
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

    def discard_changes(self):
        self.send_command('abort')

    def get_device_operations(self):
        return {
            'supports_diff_replace': False,
            'supports_commit': True,
            'supports_rollback': True,
            'supports_defaults': False,
            'supports_onbox_diff': True,
            'supports_commit_comment': True,
            'supports_multiline_delimiter': False,
            'supports_diff_match': False,
            'supports_diff_ignore_lines': False,
            'supports_generate_diff': False,
            'supports_replace': True,
            'supports_admin': True,
            'supports_commit_label': True
        }

    def get_option_values(self):
        return {
            'format': ['text'],
            'diff_match': [],
            'diff_replace': [],
            'output': []
        }

    def get_capabilities(self):
        result = {}
        result['rpc'] = self.get_base_rpc() + ['commit', 'discard_changes', 'get_diff', 'configure', 'exit']
        result['network_api'] = 'cliconf'
        result['device_info'] = self.get_device_info()
        result['device_operations'] = self.get_device_operations()
        result.update(self.get_option_values())
        return json.dumps(result)
