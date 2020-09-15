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

DOCUMENTATION = """
---
author: Ansible Networking Team
cliconf: eos
short_description: Use eos cliconf to run command on Arista EOS platform
description:
  - This eos plugin provides low level abstraction apis for
    sending and receiving CLI commands from Arista EOS network devices.
version_added: "2.4"
options:
  eos_use_sessions:
    type: boolean
    default: yes
    description:
      - Specifies if sessions should be used on remote host or not
    env:
      - name: ANSIBLE_EOS_USE_SESSIONS
    vars:
      - name: ansible_eos_use_sessions
        version_added: '2.7'
"""

import json
import time
import re

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.common.config import NetworkConfig, dumps
from ansible.plugins.cliconf import CliconfBase, enable_mode


class Cliconf(CliconfBase):

    def __init__(self, *args, **kwargs):
        super(Cliconf, self).__init__(*args, **kwargs)
        self._session_support = None

    @enable_mode
    def get_config(self, source='running', format='text', flags=None):
        options_values = self.get_option_values()
        if format not in options_values['format']:
            raise ValueError("'format' value %s is invalid. Valid values are %s" % (format, ','.join(options_values['format'])))

        lookup = {'running': 'running-config', 'startup': 'startup-config'}
        if source not in lookup:
            raise ValueError("fetching configuration from %s is not supported" % source)

        cmd = 'show %s ' % lookup[source]
        if format and format != 'text':
            cmd += '| %s ' % format

        cmd += ' '.join(to_list(flags))
        cmd = cmd.strip()
        return self.send_command(cmd)

    @enable_mode
    def edit_config(self, candidate=None, commit=True, replace=None, comment=None):

        operations = self.get_device_operations()
        self.check_edit_config_capability(operations, candidate, commit, replace, comment)

        if (commit is False) and (not self.supports_sessions()):
            raise ValueError('check mode is not supported without configuration session')

        resp = {}
        session = None
        if self.supports_sessions():
            session = 'ansible_%s' % int(time.time())
            resp.update({'session': session})
            self.send_command('configure session %s' % session)
            if replace:
                self.send_command('rollback clean-config')
        else:
            self.send_command('configure')

        results = []
        requests = []
        multiline = False
        for line in to_list(candidate):
            if not isinstance(line, Mapping):
                line = {'command': line}

            cmd = line['command']
            if cmd == 'end':
                continue
            elif cmd.startswith('banner') or multiline:
                multiline = True
            elif cmd == 'EOF' and multiline:
                multiline = False

            if multiline:
                line['sendonly'] = True

            if cmd != 'end' and cmd[0] != '!':
                try:
                    results.append(self.send_command(**line))
                    requests.append(cmd)
                except AnsibleConnectionFailure as e:
                    self.discard_changes(session)
                    raise AnsibleConnectionFailure(e.message)

        resp['request'] = requests
        resp['response'] = results
        if self.supports_sessions():
            out = self.send_command('show session-config diffs')
            if out:
                resp['diff'] = out.strip()

            if commit:
                self.commit()
            else:
                self.discard_changes(session)
        else:
            self.send_command('end')
        return resp

    def get(self, command, prompt=None, answer=None, sendonly=False, output=None, newline=True, check_all=False):
        if output:
            command = self._get_command_with_output(command, output)
        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline, check_all=check_all)

    def commit(self):
        self.send_command('commit')

    def discard_changes(self, session=None):
        commands = ['end']
        if self.supports_sessions():
            # to close session gracefully execute abort in top level session prompt.
            commands.extend(['configure session %s' % session, 'abort'])

        for cmd in commands:
            self.send_command(cmd)

    def run_commands(self, commands=None, check_rc=True):
        if commands is None:
            raise ValueError("'commands' value is required")
        responses = list()
        for cmd in to_list(commands):
            if not isinstance(cmd, Mapping):
                cmd = {'command': cmd}

            output = cmd.pop('output', None)
            if output:
                cmd['command'] = self._get_command_with_output(cmd['command'], output)

            try:
                out = self.send_command(**cmd)
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

    def get_diff(self, candidate=None, running=None, diff_match='line', diff_ignore_lines=None, path=None, diff_replace='line'):
        diff = {}
        device_operations = self.get_device_operations()
        option_values = self.get_option_values()

        if candidate is None and device_operations['supports_generate_diff']:
            raise ValueError("candidate configuration is required to generate diff")

        if diff_match not in option_values['diff_match']:
            raise ValueError("'match' value %s in invalid, valid values are %s" % (diff_match, ', '.join(option_values['diff_match'])))

        if diff_replace not in option_values['diff_replace']:
            raise ValueError("'replace' value %s in invalid, valid values are %s" % (diff_replace, ', '.join(option_values['diff_replace'])))

        # prepare candidate configuration
        candidate_obj = NetworkConfig(indent=3)
        candidate_obj.load(candidate)

        if running and diff_match != 'none' and diff_replace != 'config':
            # running configuration
            running_obj = NetworkConfig(indent=3, contents=running, ignore_lines=diff_ignore_lines)
            configdiffobjs = candidate_obj.difference(running_obj, path=path, match=diff_match, replace=diff_replace)

        else:
            configdiffobjs = candidate_obj.items

        diff['config_diff'] = dumps(configdiffobjs, 'commands') if configdiffobjs else ''
        return diff

    def supports_sessions(self):
        if not self.get_option('eos_use_sessions'):
            self._session_support = False
        else:
            if self._session_support:
                return self._session_support

            try:
                self.get('show configuration sessions')
                self._session_support = True
            except AnsibleConnectionFailure:
                self._session_support = False

        return self._session_support

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

        try:
            reply = self.get('bash timeout 5 cat /mnt/flash/boot-config')

            match = re.search(r'SWI=(.+)$', reply, re.M)
            if match:
                device_info['network_os_image'] = match.group(1)
        except AnsibleConnectionFailure:
            # This requires enable mode to run
            self._connection.queue_message('vvv', "Unable to gather network_os_image without enable mode")

        return device_info

    def get_device_operations(self):
        return {
            'supports_diff_replace': True,
            'supports_commit': bool(self.supports_sessions()),
            'supports_rollback': False,
            'supports_defaults': False,
            'supports_onbox_diff': bool(self.supports_sessions()),
            'supports_commit_comment': False,
            'supports_multiline_delimiter': False,
            'supports_diff_match': True,
            'supports_diff_ignore_lines': True,
            'supports_generate_diff': not bool(self.supports_sessions()),
            'supports_replace': bool(self.supports_sessions()),
        }

    def get_option_values(self):
        return {
            'format': ['text', 'json'],
            'diff_match': ['line', 'strict', 'exact', 'none'],
            'diff_replace': ['line', 'block', 'config'],
            'output': ['text', 'json']
        }

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        result['rpc'] += ['commit', 'discard_changes', 'get_diff', 'run_commands', 'supports_sessions']
        result['device_operations'] = self.get_device_operations()
        result.update(self.get_option_values())

        return json.dumps(result)

    def set_cli_prompt_context(self):
        """
        Make sure we are in the operational cli mode
        :return: None
        """
        if self._connection.connected:
            self._update_cli_prompt_context(config_context='(config', exit_command='abort')

    def _get_command_with_output(self, command, output):
        options_values = self.get_option_values()
        if output not in options_values['output']:
            raise ValueError("'output' value %s is invalid. Valid values are %s" % (output, ','.join(options_values['output'])))

        if output == 'json' and not command.endswith('| json'):
            cmd = '%s | json' % command
        else:
            cmd = command
        return cmd
