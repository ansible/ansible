# (c) 2018 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
author: Ansible Networking Team
httpapi: eos
short_description: Use eAPI to run command on eos platform
description:
  - This eos plugin provides low level abstraction api's for
    sending and receiving CLI commands with eos network devices.
version_added: "2.6"
options:
  eos_use_sessions:
    type: int
    default: 1
    description:
      - Specifies if sessions should be used on remote host or not
    env:
      - name: ANSIBLE_EOS_USE_SESSIONS
    vars:
      - name: ansible_eos_use_sessions
        version_added: '2.8'
"""

import json

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
        self._session_support = None

    def supports_sessions(self):
        use_session = self.get_option('eos_use_sessions')
        try:
            use_session = int(use_session)
        except ValueError:
            pass

        if not bool(use_session):
            self._session_support = False
        else:
            if self._session_support:
                return self._session_support

            response = self.send_request('show configuration sessions')
            self._session_support = 'error' not in response

        return self._session_support

    def send_request(self, data, **message_kwargs):
        data = to_list(data)
        become = self._become
        if become:
            self.connection.queue_message('vvvv', 'firing event: on_become')
            data.insert(0, {"cmd": "enable", "input": self._become_pass})

        output = message_kwargs.get('output', 'text')
        request = request_builder(data, output)
        headers = {'Content-Type': 'application/json-rpc'}

        response, response_data = self.connection.send('/command-api', request, headers=headers, method='POST')

        try:
            response_data = json.loads(to_text(response_data.getvalue()))
        except ValueError:
            raise ConnectionError('Response was not valid JSON, got {0}'.format(
                to_text(response_data.getvalue())
            ))

        results = handle_response(response_data)

        if become:
            results = results[1:]
        if len(results) == 1:
            results = results[0]

        return results

    def get_device_info(self):
        if self._device_info:
            return self._device_info

        device_info = {}

        device_info['network_os'] = 'eos'
        reply = self.send_request('show version', output='json')
        data = json.loads(reply)

        device_info['network_os_version'] = data['version']
        device_info['network_os_model'] = data['modelName']

        reply = self.send_request('show hostname | json')
        data = json.loads(reply)

        device_info['network_os_hostname'] = data['hostname']

        self._device_info = device_info
        return self._device_info

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

    def get_capabilities(self):
        result = {}
        result['rpc'] = []
        result['device_info'] = self.get_device_info()
        result['device_operations'] = self.get_device_operations()
        result.update(OPTIONS)
        result['network_api'] = 'eapi'

        return json.dumps(result)


def handle_response(response):
    if 'error' in response:
        error = response['error']

        error_text = []
        for data in error['data']:
            error_text.extend(data.get('errors', []))
        error_text = '\n'.join(error_text) or error['message']

        raise ConnectionError(error_text, code=error['code'])

    results = []

    for result in response['result']:
        if 'messages' in result:
            results.append(result['messages'][0])
        elif 'output' in result:
            results.append(result['output'].strip())
        else:
            results.append(json.dumps(result))

    return results


def request_builder(commands, output, reqid=None):
    params = dict(version=1, cmds=commands, format=output)
    return json.dumps(dict(jsonrpc='2.0', id=reqid, method='runCmds', params=params))
