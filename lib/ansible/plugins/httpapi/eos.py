# (c) 2018 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text
from ansible.module_utils.network.common.utils import to_list

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class HttpApi:
    def __init__(self, connection):
        self.connection = connection

    def send_request(self, data, **message_kwargs):
        if 'become' in message_kwargs:
            display.vvvv('firing event: on_become')
            # TODO ??? self._terminal.on_become(passwd=auth_pass)

        try:
            command = json.loads(data)
            output = cmd['output']
        except ValueError:
            output = 'json'

        request = request_builder(data, output)
        headers = {'Content-Type': 'application/json-rpc'}

        response = self.connection.send('/command-api', request, headers=headers, method='POST')
        response = json.loads(to_text(response.read()))
        return handle_response(response)


def handle_response(response):
    if 'error' in response:
        raise AnsibleConnectionFailure(response['error'])

    result = response['result'][0]
    if 'messages' in result:
        result = result['messages'][0]
    else:
        result = json.dumps(result)
    return result.strip()


def request_builder(commands, output, reqid=None):
    params = dict(version=1, cmds=to_list(commands), format=output)
    return json.dumps(dict(jsonrpc='2.0', id=reqid, method='runCmds', params=params))
