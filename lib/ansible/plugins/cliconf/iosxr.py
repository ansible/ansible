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
cliconf: iosxr
short_description: Use iosxr cliconf to run command on Cisco IOS XR platform
description:
  - This iosxr plugin provides low level abstraction apis for
    sending and receiving CLI commands from Cisco IOS XR network devices.
version_added: "2.4"
"""

import re
import json

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.network.common.config import NetworkConfig, dumps
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.iosxr.iosxr import sanitize_config, mask_config_blocks_from_diff
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

        model_search_strs = [r'^Cisco (.+) \(revision', r'^[Cc]isco (\S+ \S+).+bytes of .*memory']
        for item in model_search_strs:
            match = re.search(item, data, re.M)
            if match:
                device_info['network_os_model'] = match.group(1)
                break

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
            if not isinstance(line, Mapping):
                line = {'command': line}
            cmd = line['command']
            results.append(self.send_command(**line))
            requests.append(cmd)

        # Before any commit happend, we can get a real configuration
        # diff from the device and make it available by the iosxr_config module.
        # This information can be usefull either in check mode or normal mode.
        resp['show_commit_config_diff'] = self.get('show commit changes diff')

        if commit:
            self.commit(comment=comment, label=label, replace=replace)
        else:
            self.discard_changes()

        self.abort(admin=admin)

        resp['request'] = requests
        resp['response'] = results
        return resp

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
        sanitized_candidate = sanitize_config(candidate)
        candidate_obj = NetworkConfig(indent=1)
        candidate_obj.load(sanitized_candidate)

        if running and diff_match != 'none':
            # running configuration
            running = mask_config_blocks_from_diff(running, candidate, "ansible")
            running = sanitize_config(running)

            running_obj = NetworkConfig(indent=1, contents=running, ignore_lines=diff_ignore_lines)
            configdiffobjs = candidate_obj.difference(running_obj, path=path, match=diff_match, replace=diff_replace)

        else:
            configdiffobjs = candidate_obj.items

        diff['config_diff'] = dumps(configdiffobjs, 'commands') if configdiffobjs else ''
        return diff

    def get(self, command=None, prompt=None, answer=None, sendonly=False, newline=True, output=None, check_all=False):
        if output:
            raise ValueError("'output' value %s is not supported for get" % output)
        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline, check_all=check_all)

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
            if not isinstance(cmd, Mapping):
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
                    raise ConnectionError(message=u'Failed to decode output from %s: %s' % (cmd, to_text(out)))

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
            'supports_diff_replace': True,
            'supports_commit': True,
            'supports_rollback': False,
            'supports_defaults': False,
            'supports_onbox_diff': False,
            'supports_commit_comment': True,
            'supports_multiline_delimiter': False,
            'supports_diff_match': True,
            'supports_diff_ignore_lines': True,
            'supports_generate_diff': True,
            'supports_replace': True,
            'supports_admin': True,
            'supports_commit_label': True
        }

    def get_option_values(self):
        return {
            'format': ['text'],
            'diff_match': ['line', 'strict', 'exact', 'none'],
            'diff_replace': ['line', 'block', 'config'],
            'output': []
        }

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        result['rpc'] += ['commit', 'discard_changes', 'get_diff', 'configure', 'exit']
        result['device_operations'] = self.get_device_operations()
        result.update(self.get_option_values())
        return json.dumps(result)
