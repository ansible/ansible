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
cliconf: nxos
short_description: Use nxos cliconf to run command on Cisco NX-OS platform
description:
  - This nxos plugin provides low level abstraction apis for
    sending and receiving CLI commands from Cicso NX-OS network devices.
version_added: "2.4"
"""

import json
import re

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.network.common.config import NetworkConfig, dumps
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase, enable_mode


class Cliconf(CliconfBase):

    def __init__(self, *args, **kwargs):
        self._module_context = {}
        super(Cliconf, self).__init__(*args, **kwargs)

    def read_module_context(self, module_key):
        if self._module_context.get(module_key):
            return self._module_context[module_key]

        return None

    def save_module_context(self, module_key, module_context):
        self._module_context[module_key] = module_context

        return None

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'nxos'
        reply = self.get('show version')
        platform_reply = self.get('show inventory')

        match_sys_ver = re.search(r'\s+system:\s+version\s*(\S+)', reply, re.M)
        if match_sys_ver:
            device_info['network_os_version'] = match_sys_ver.group(1)
        else:
            match_kick_ver = re.search(r'\s+kickstart:\s+version\s*(\S+)', reply, re.M)
            if match_kick_ver:
                device_info['network_os_version'] = match_kick_ver.group(1)

        if 'network_os_version' not in device_info:
            match_sys_ver = re.search(r'\s+NXOS:\s+version\s*(\S+)', reply, re.M)
            if match_sys_ver:
                device_info['network_os_version'] = match_sys_ver.group(1)

        match_chassis_id = re.search(r'Hardware\n\s+cisco(.+)$', reply, re.M)
        if match_chassis_id:
            device_info['network_os_model'] = match_chassis_id.group(1).strip()

        match_host_name = re.search(r'\s+Device name:\s*(\S+)', reply, re.M)
        if match_host_name:
            device_info['network_os_hostname'] = match_host_name.group(1)

        match_isan_file_name = re.search(r'\s+system image file is:\s*(\S+)', reply, re.M)
        if match_isan_file_name:
            device_info['network_os_image'] = match_isan_file_name.group(1)
        else:
            match_kick_file_name = re.search(r'\s+kickstart image file is:\s*(\S+)', reply, re.M)
            if match_kick_file_name:
                device_info['network_os_image'] = match_kick_file_name.group(1)

        if 'network_os_image' not in device_info:
            match_isan_file_name = re.search(r'\s+NXOS image file is:\s*(\S+)', reply, re.M)
            if match_isan_file_name:
                device_info['network_os_image'] = match_isan_file_name.group(1)

        match_os_platform = re.search(r'NAME: "Chassis",\s*DESCR:.*\n'
                                      r'PID:\s*(\S+)', platform_reply, re.M)
        if match_os_platform:
            device_info['network_os_platform'] = match_os_platform.group(1)

        return device_info

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
        candidate_obj = NetworkConfig(indent=2)
        candidate_obj.load(candidate)

        if running and diff_match != 'none' and diff_replace != 'config':
            # running configuration
            running_obj = NetworkConfig(indent=2, contents=running, ignore_lines=diff_ignore_lines)
            configdiffobjs = candidate_obj.difference(running_obj, path=path, match=diff_match, replace=diff_replace)

        else:
            configdiffobjs = candidate_obj.items

        diff['config_diff'] = dumps(configdiffobjs, 'commands') if configdiffobjs else ''
        return diff

    def get_config(self, source='running', format='text', flags=None):
        options_values = self.get_option_values()
        if format not in options_values['format']:
            raise ValueError("'format' value %s is invalid. Valid values are %s" % (format, ','.join(options_values['format'])))

        lookup = {'running': 'running-config', 'startup': 'startup-config'}
        if source not in lookup:
            raise ValueError("fetching configuration from %s is not supported" % source)

        cmd = 'show {0} '.format(lookup[source])
        if format and format != 'text':
            cmd += '| %s ' % format

        if flags:
            cmd += ' '.join(to_list(flags))
        cmd = cmd.strip()

        return self.send_command(cmd)

    def edit_config(self, candidate=None, commit=True, replace=None, comment=None):
        resp = {}
        operations = self.get_device_operations()
        self.check_edit_config_capability(operations, candidate, commit, replace, comment)
        results = []
        requests = []

        if replace:
            device_info = self.get_device_info()
            if '9K' not in device_info.get('network_os_platform', ''):
                raise ConnectionError(message=u'replace is supported only on Nexus 9K devices')
            candidate = 'config replace {0}'.format(replace)

        if commit:
            self.send_command('configure terminal')

            for line in to_list(candidate):
                if not isinstance(line, Mapping):
                    line = {'command': line}

                cmd = line['command']
                if cmd != 'end':
                    results.append(self.send_command(**line))
                    requests.append(cmd)

            self.send_command('end')
        else:
            raise ValueError('check mode is not supported')

        resp['request'] = requests
        resp['response'] = results
        return resp

    def get(self, command, prompt=None, answer=None, sendonly=False, output=None, check_all=False):
        if output:
            command = self._get_command_with_output(command, output)
        return self.send_command(command, prompt=prompt, answer=answer, sendonly=sendonly, check_all=check_all)

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
                if check_rc is True:
                    raise
                out = getattr(e, 'err', e)

            if out is not None:
                try:
                    out = to_text(out, errors='surrogate_or_strict').strip()
                except UnicodeError:
                    raise ConnectionError(message=u'Failed to decode output from %s: %s' % (cmd, to_text(out)))

                try:
                    out = json.loads(out)
                except ValueError:
                    pass

                responses.append(out)
        return responses

    def get_device_operations(self):
        return {
            'supports_diff_replace': True,
            'supports_commit': False,
            'supports_rollback': False,
            'supports_defaults': True,
            'supports_onbox_diff': False,
            'supports_commit_comment': False,
            'supports_multiline_delimiter': False,
            'supports_diff_match': True,
            'supports_diff_ignore_lines': True,
            'supports_generate_diff': True,
            'supports_replace': True
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
        result['rpc'] += ['get_diff', 'run_commands']
        result['device_operations'] = self.get_device_operations()
        result.update(self.get_option_values())

        return json.dumps(result)

    def _get_command_with_output(self, command, output):
        options_values = self.get_option_values()
        if output not in options_values['output']:
            raise ValueError("'output' value %s is invalid. Valid values are %s" % (output, ','.join(options_values['output'])))

        if output == 'json' and not command.endswith('| json'):
            cmd = '%s | json' % command
        elif output == 'text' and command.endswith('| json'):
            cmd = command.rsplit('|', 1)[0]
        else:
            cmd = command
        return cmd
