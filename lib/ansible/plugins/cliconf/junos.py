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
cliconf: junos
short_description: Use junos cliconf to run command on Juniper Junos OS platform
description:
  - This junos plugin provides low level abstraction apis for
    sending and receiving CLI commands from Juniper Junos OS network devices.
version_added: "2.4"
"""

import json
import re

from itertools import chain
from functools import wraps

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase


def configure(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        prompt = self._connection.get_prompt()
        if not to_text(prompt, errors='surrogate_or_strict').strip().endswith('#'):
            self.send_command('configure')
        return func(self, *args, **kwargs)
    return wrapped


class Cliconf(CliconfBase):

    def get_text(self, ele, tag):
        try:
            return to_text(ele.find(tag).text, errors='surrogate_then_replace').strip()
        except AttributeError:
            pass

    def get_device_info(self):
        device_info = dict()
        device_info['network_os'] = 'junos'

        reply = self.get(command='show version')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'Junos: (\S+)', data)
        if match:
            device_info['network_os_version'] = match.group(1)

        match = re.search(r'Model: (\S+)', data, re.M)
        if match:
            device_info['network_os_model'] = match.group(1)

        match = re.search(r'Hostname: (\S+)', data, re.M)
        if match:
            device_info['network_os_hostname'] = match.group(1)
        return device_info

    def get_config(self, source='running', format='text', flags=None):
        if source != 'running':
            raise ValueError("fetching configuration from %s is not supported" % source)

        options_values = self.get_option_values()
        if format not in options_values['format']:
            raise ValueError("'format' value %s is invalid. Valid values are %s" % (format, ','.join(options_values['format'])))

        if format == 'text':
            cmd = 'show configuration'
        else:
            cmd = 'show configuration | display %s' % format

        cmd += ' '.join(to_list(flags))
        cmd = cmd.strip()
        return self.send_command(cmd)

    @configure
    def edit_config(self, candidate=None, commit=True, replace=None, comment=None):

        operations = self.get_device_operations()
        self.check_edit_config_capability(operations, candidate, commit, replace, comment)

        resp = {}
        results = []
        requests = []

        if replace:
            candidate = 'load replace {0}'.format(replace)

        for line in to_list(candidate):
            if not isinstance(line, Mapping):
                line = {'command': line}
            cmd = line['command']
            try:
                results.append(self.send_command(**line))
            except AnsibleConnectionFailure as exc:
                if "error: commit failed" in exc.message:
                    self.discard_changes()
                raise
            requests.append(cmd)

        diff = self.compare_configuration()
        if diff:
            resp['diff'] = diff

            if commit:
                self.commit(comment=comment)
            else:
                self.discard_changes()

        else:
            for cmd in ['top', 'exit']:
                self.send_command(cmd)

        resp['request'] = requests
        resp['response'] = results
        return resp

    def get(self, command, prompt=None, answer=None, sendonly=False, output=None, check_all=False):
        if output:
            command = self._get_command_with_output(command, output)
        return self.send_command(command, prompt=prompt, answer=answer, sendonly=sendonly, check_all=check_all)

    @configure
    def commit(self, comment=None, confirmed=False, at_time=None, synchronize=False):
        """
        Execute commit command on remote device.
        :param comment: Comment to be associated with commit
        :param confirmed: Boolean flag to indicate if the previous commit should confirmed
        :param at_time: Time at which to activate configuration changes
        :param synchronize: Boolean flag to indicate if commit should synchronize on remote peers
        :return: Command response received from device
        """
        command = 'commit'
        if comment:
            command += ' comment {0}'.format(comment)
        if confirmed:
            command += ' confirmed'
        if at_time:
            command += ' {0}'.format(at_time)
        if synchronize:
            command += ' peers-synchronize'

        command += ' and-quit'

        try:
            response = self.send_command(command)
        except AnsibleConnectionFailure:
            self.discard_changes()
            raise

        return response

    @configure
    def discard_changes(self):
        command = 'rollback 0'
        for cmd in chain(to_list(command), ['exit']):
            self.send_command(cmd)

    @configure
    def validate(self):
        return self.send_command('commit check')

    @configure
    def compare_configuration(self, rollback_id=None):
        command = 'show | compare'
        if rollback_id is not None:
            command += ' rollback %s' % int(rollback_id)
        resp = self.send_command(command)

        r = resp.splitlines()
        if len(r) == 1 and '[edit]' in r[0]:
            resp = ''

        return resp

    @configure
    def rollback(self, rollback_id, commit=True):
        resp = {}
        self.send_command('rollback %s' % int(rollback_id))
        resp['diff'] = self.compare_configuration()
        if commit:
            self.commit()
        else:
            self.discard_changes()
        return resp

    def get_diff(self, rollback_id=None):
        diff = {'config_diff': None}
        response = self.compare_configuration(rollback_id=rollback_id)
        if response:
            diff['config_diff'] = response
        return diff

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
            'supports_replace': True
        }

    def get_option_values(self):
        return {
            'format': ['text', 'set', 'xml', 'json'],
            'diff_match': [],
            'diff_replace': [],
            'output': ['text', 'set', 'xml', 'json']
        }

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        result['rpc'] += ['commit', 'discard_changes', 'run_commands', 'compare_configuration', 'validate', 'get_diff']
        result['device_operations'] = self.get_device_operations()
        result.update(self.get_option_values())
        return json.dumps(result)

    def _get_command_with_output(self, command, output):
        options_values = self.get_option_values()
        if output not in options_values['output']:
            raise ValueError("'output' value %s is invalid. Valid values are %s" % (output, ','.join(options_values['output'])))

        if output == 'json' and not command.endswith('| display json'):
            cmd = '%s | display json' % command
        elif output == 'xml' and not command.endswith('| display xml'):
            cmd = '%s | display xml' % command
        elif output == 'text' and (command.endswith('| display json') or command.endswith('| display xml')):
            cmd = command.rsplit('|', 1)[0]
        else:
            cmd = command
        return cmd
