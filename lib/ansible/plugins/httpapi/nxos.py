# (c) 2018 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
author: Ansible Networking Team
httpapi: nxos
short_description: Use NX-API to run command on nxos platform
description:
  - This eos plugin provides low level abstraction api's for
    sending and receiving CLI commands with nxos network devices.
version_added: "2.6"
"""

import json
import re
import collections

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.httpapi import HttpApiBase


OPTIONS = {
    'format': ['text', 'json'],
    'diff_match': ['line', 'strict', 'exact', 'none'],
    'diff_replace': ['line', 'block', 'config'],
    'output': ['text', 'json']
}


class HttpApi(HttpApiBase):
    def __init__(self, *args, **kwargs):
        super(HttpApi, self).__init__(*args, **kwargs)
        self._device_info = None
        self._module_context = {}

    def read_module_context(self, module_key):
        if self._module_context.get(module_key):
            return self._module_context[module_key]

        return None

    def save_module_context(self, module_key, module_context):
        self._module_context[module_key] = module_context

        return None

    def send_request(self, data, **message_kwargs):
        output = None
        queue = list()
        responses = list()

        for item in to_list(data):
            cmd_output = message_kwargs.get('output', 'text')
            if isinstance(item, dict):
                command = item['command']
                if 'output' in item:
                    cmd_output = item['output']
            else:
                command = item

            # Emulate '| json' from CLI
            if command.endswith('| json'):
                command = command.rsplit('|', 1)[0]
                cmd_output = 'json'

            if output and output != cmd_output:
                responses.extend(self._run_queue(queue, output))
                queue = list()

            output = cmd_output
            queue.append(command)

        if queue:
            responses.extend(self._run_queue(queue, output))

        if len(responses) == 1:
            return responses[0]
        return responses

    def _run_queue(self, queue, output):
        if self._become:
            self.connection.queue_message('vvvv', 'firing event: on_become')
            queue.insert(0, 'enable')

        request = request_builder(queue, output)
        headers = {'Content-Type': 'application/json'}

        response, response_data = self.connection.send('/ins', request, headers=headers, method='POST')

        try:
            response_data = json.loads(to_text(response_data.getvalue()))
        except ValueError:
            raise ConnectionError('Response was not valid JSON, got {0}'.format(
                to_text(response_data.getvalue())
            ))

        results = handle_response(response_data)

        if self._become:
            results = results[1:]
        return results

    def get_device_info(self):
        if self._device_info:
            return self._device_info

        device_info = {}

        device_info['network_os'] = 'nxos'
        reply = self.send_request('show version')
        platform_reply = self.send_request('show inventory')

        find_os_version = [r'\s+system:\s+version\s*(\S+)', r'\s+kickstart:\s+version\s*(\S+)', r'\s+NXOS:\s+version\s*(\S+)']
        for regex in find_os_version:
            match_ver = re.search(regex, reply, re.M)
            if match_ver:
                device_info['network_os_version'] = match_ver.group(1)
                break

        match_chassis_id = re.search(r'Hardware\n\s+cisco\s*(\S+\s+\S+)', reply, re.M)
        if match_chassis_id:
            device_info['network_os_model'] = match_chassis_id.group(1)

        match_host_name = re.search(r'\s+Device name:\s*(\S+)', reply, re.M)
        if match_host_name:
            device_info['network_os_hostname'] = match_host_name.group(1)

        find_os_image = [r'\s+system image file is:\s*(\S+)', r'\s+kickstart image file is:\s*(\S+)', r'\s+NXOS image file is:\s*(\S+)']
        for regex in find_os_image:
            match_file_name = re.search(regex, reply, re.M)
            if match_file_name:
                device_info['network_os_image'] = match_file_name.group(1)
                break

        match_os_platform = re.search(r'NAME: (?:"Chassis"| Chassis ),\s*DESCR:.*\nPID:\s*(\S+)', platform_reply, re.M)
        if match_os_platform:
            device_info['network_os_platform'] = match_os_platform.group(1)

        self._device_info = device_info
        return self._device_info

    def get_device_operations(self):
        platform = self.get_device_info().get('network_os_platform', '')
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
            'supports_replace': True if '9K' in platform else False,
        }

    def get_capabilities(self):
        result = {}
        result['rpc'] = []
        result['device_info'] = self.get_device_info()
        result['device_operations'] = self.get_device_operations()
        result.update(OPTIONS)
        result['network_api'] = 'nxapi'

        return json.dumps(result)


def handle_response(response):
    results = []

    if response['ins_api'].get('outputs'):
        for output in to_list(response['ins_api']['outputs']['output']):
            if output['code'] != '200':
                raise ConnectionError('%s: %s' % (output['input'], output['msg']), code=output['code'])
            elif 'body' in output:
                result = output['body']
                if isinstance(result, dict):
                    result = json.dumps(result)

                results.append(result.strip())

    return results


def request_builder(commands, output, version='1.0', chunk='0', sid=None):
    """Encodes a NXAPI JSON request message
    """
    output_to_command_type = {
        'text': 'cli_show_ascii',
        'json': 'cli_show',
        'bash': 'bash',
        'config': 'cli_conf'
    }

    maybe_output = commands[0].split('|')[-1].strip()
    if maybe_output in output_to_command_type:
        command_type = output_to_command_type[maybe_output]
        commands = [command.split('|')[0].strip() for command in commands]
    else:
        try:
            command_type = output_to_command_type[output]
        except KeyError:
            msg = 'invalid format, received %s, expected one of %s' % \
                (output, ','.join(output_to_command_type.keys()))
            raise ConnectionError(msg)

    if isinstance(commands, (list, set, tuple)):
        commands = ' ;'.join(commands)

    # Order should not matter but some versions of NX-OS software fail
    # to process the payload properly if 'input' gets serialized before
    # 'type' and the payload of 'input' contains the word 'type'.
    msg = collections.OrderedDict()
    msg['version'] = version
    msg['type'] = command_type
    msg['chunk'] = chunk
    msg['sid'] = sid
    msg['input'] = commands
    msg['output_format'] = 'json'

    return json.dumps(dict(ins_api=msg))
