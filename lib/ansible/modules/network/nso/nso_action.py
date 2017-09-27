#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 Cisco and/or its affiliates.
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

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: nso_action
short_description: Executes NSO actions and verifies output.
description:
  - This module provices support for executing NSO actions and then verifying
    that the output is as expected.
author: "Claes Nästén (@cnasten)"
options:
  url:
    description: NSO JSON-RPC URL, http://localhost:8080/jsonrpc
    required: true
  username:
    description: NSO username
    required: true
  password:
    description: NSO password
    required: true
  path:
    description: Path to NSO action.
    required: true
  input:
    description: >
      NSO action parameters.
  output_required:
     description: >
       Required output parameters.
  output_invalid:
     description: >
       List of result parameter names that will cause the task to fail if they
       are present.
  validate_strict:
     description: >
       If set to true, the task will fail if any output parameters not in
       output_required is present in the output.
version_added: "2.5"
'''

EXAMPLES = '''
- name: Sync NSO device
  nso_config:
    url: http://localhost:8080/jsonrpc
    username: admin
    password: admin
    path: /ncs:devices/device{ce0}/sync-from
    output_required:
      result: true
'''

RETURN = '''
output:
  description: Action output
  returned: success
  type: dict
  sample:
    result: true
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url

import json

try:
    unicode
    HAVE_UNICODE = True
except NameError:
    unicode = str
    HAVE_UNICODE = False


class ModuleFailException(Exception):
    def __init__(self, message):
        super(ModuleFailException, self).__init__(message)
        self.message = message


class NsoException(Exception):
    def __init__(self, message, error):
        super(NsoException, self).__init__(message)
        self.message = message
        self.error = error


class JsonRpc(object):
    def __init__(self, url):
        self._url = url

        self._id = 0
        self._trans = {}
        self._headers = {'Content-Type': 'application/json'}
        self._conn = None

    def login(self, user, passwd):
        payload = {
            'method': 'login', 'params': {'user': user, 'passwd': passwd}
        }
        resp, resp_json = self._call(payload)
        self._headers['Cookie'] = resp.headers['set-cookie']

    def logout(self):
        payload = {'method': 'logout', 'params': {}}
        self._call(payload)

    def get_system_setting(self, setting):
        payload = {'method': 'get_system_setting', 'params': {'operation': setting}}
        resp, resp_json = self._call(payload)
        return resp_json['result']

    def new_trans(self, **kwargs):
        payload = {'method': 'new_trans', 'params': kwargs}
        resp, resp_json = self._call(payload)
        return resp_json['result']['th']

    def get_schema(self, **kwargs):
        payload = {'method': 'get_schema', 'params': kwargs}
        resp, resp_json = self._read_call(payload)
        return resp_json['result']

    def get_module_prefix_map(self):
        payload = {'method': 'get_module_prefix_map', 'params': {}}
        resp, resp_json = self._call(payload)
        return resp_json['result']

    def get_value(self, path):
        payload = {
            'method': 'get_value',
            'params': {'path': path}
        }
        resp, resp_json = self._read_call(payload)
        return resp_json['result']

    def exists(self, path):
        payload = {'method': 'exists', 'params': {'path': path}}
        resp, resp_json = self._read_call(payload)
        return resp_json['result']['exists']

    def run_action(self, th, path, params=None):
        if params is None:
            params = {}

        payload = {
            'method': 'run_action',
            'params': {
                'format': 'json',
                'path': path,
                'params': params
            }
        }
        if th is None:
            resp, resp_json = self._read_call(payload)
        else:
            payload['params']['th'] = th
            resp, resp_json = self._call(payload)

        return resp_json['result']

    def _call(self, payload):
        self._id += 1
        if 'id' not in payload:
            payload['id'] = self._id

        if 'jsonrpc' not in payload:
            payload['jsonrpc'] = '2.0'

        data = json.dumps(payload)
        resp = open_url(
            self._url, method='POST', data=data, headers=self._headers)
        if resp.code != 200:
            raise NsoException(
                'NSO returned HTTP code {0}, expected 200'.format(resp.status), {})

        resp_body = resp.read()
        resp_json = json.loads(resp_body)

        if 'error' in resp_json:
            self._handle_call_error(payload, resp_json)
        return resp, resp_json

    def _handle_call_error(self, payload, resp_json):
        method = payload['method']

        error = resp_json['error']
        error_type = error['type'][len('rpc.method.'):]
        if error_type in ('unexpected_params',
                          'unknown_params_value',
                          'invalid_params',
                          'invalid_params_type',
                          'data_not_found'):
            key = error['data']['param']
            error_type_s = error_type.replace('_', ' ')
            if key == 'path':
                msg = 'NSO {0} {1}. path = {2}'.format(
                    method, error_type_s, payload['params']['path'])
            else:
                path = payload['params'].get('path', 'unknown')
                msg = 'NSO {0} {1}. path = {2}. {3} = {4}'.format(
                    method, error_type_s, path, key, payload['params'][key])
        else:
            msg = 'NSO {0} returned JSON-RPC error: {1}'.format(method, error)

        raise NsoException(msg, error)

    def _read_call(self, payload):
        if 'th' not in payload['params']:
            payload['params']['th'] = self._get_th(mode='read')
        return self._call(payload)

    def _write_call(self, payload):
        if 'th' not in payload['params']:
            payload['params']['th'] = self._get_th(mode='read_write')
        return self._call(payload)

    def _get_th(self, mode='read'):
        if mode not in self._trans:
            th = self.new_trans(mode=mode)
            self._trans[mode] = th
        return self._trans[mode]


class NsoAction(object):
    def __init__(self, module, client,
                 path, input,
                 output_required, output_invalid, validate_strict):
        self._module = module
        self._client = client
        self._path = path
        self._input = input
        self._output_required = output_required
        self._output_invalid = output_invalid
        self._validate_strict = validate_strict

    def main(self):
        schema = self._client.get_schema(path=self._path)
        if schema['data']['kind'] != 'action':
            raise ModuleFailException('{0} is not an action'.format(self._path))

        input_schema = [c for c in schema['data']['children']
                        if c.get('is_action_input', False)]

        for key, value in self._input.items():
            child = next((c for c in input_schema if c['name'] == key), None)
            if child is None:
                raise ModuleFailException('no parameter {0}'.format(key))

            # TODO: validate type etc

        output = self._client.run_action(None, self._path, self._input)
        for key, value in self._output_required.items():
            if key not in output:
                raise ModuleFailException('{0} not in result'.format(key))

            n_value = self._normalized_value(value, output[key], key)
            if value != n_value:
                msg = '{0} value mismatch. expected {1} got {2}'.format(
                    key, value, n_value)
                raise ModuleFailException(msg)

        for key in self._output_invalid.keys():
            if key in output:
                raise ModuleFailException('{0} not allowed in result'.format(key))

        if self._validate_strict:
            for name in output.keys():
                if name not in self._output_required:
                    raise ModuleFailException('{0} not allowed in result'.format(name))

        return output

    def _normalized_value(self, expected_value, value, key):
        if value is None:
            return None
        if isinstance(expected_value, bool):
            return value == 'true'
        if isinstance(expected_value, int):
            try:
                return int(value)
            except TypeError:
                raise ModuleFailException(
                    'returned value {0} for {1} is not a valid integer'.format(
                        key, value))
        if isinstance(expected_value, float):
            try:
                return float(value)
            except TypeError:
                raise ModuleFailException(
                    'returned value {0} for {1} is not a valid float'.format(
                        key, value))
        if isinstance(expected_value, (list, tuple)):
            if not isinstance(value, (list, tuple)):
                raise ModuleFailException(
                    'returned value {0} for {1} is not a list'.format(value, key))
            if len(expected_value) != len(value):
                raise ModuleFailException(
                    'list length mismatch for {0}'.format(key))

            normalized_value = []
            for i in range(len(expected_value)):
                normalized_value.append(
                    self._normalized_value(expected_value[i], value[i], '{0}[{1}]'.format(key, i)))
            return normalized_value

        if isinstance(expected_value, dict):
            if not isinstance(value, dict):
                raise ModuleFailException(
                    'returned value {0} for {1} is not a dict'.format(value, key))
            if len(expected_value) != len(value):
                raise ModuleFailException(
                    'dict length mismatch for {0}'.format(key))

            normalized_value = {}
            for k in expected_value.keys():
                n_k = self._normalized_value(k, k, '{0}[{1}]'.format(key, k))
                if n_k not in value:
                    raise ModuleFailException('missing {0} in value'.format(n_k))
                normalized_value[n_k] = self._normalized_value(expected_value[k], value[k], '{0}[{1}]'.format(key, k))
            return normalized_value

        if HAVE_UNICODE:
            if isinstance(expected_value, unicode) and isinstance(value, str):
                return value.decode('utf-8')
            if isinstance(expected_value, str) and isinstance(value, unicode):
                return value.encode('utf-8')
        else:
            if hasattr(expected_value, 'encode') and hasattr(value, 'decode'):
                return value.decode('utf-8')
            if hasattr(expected_value, 'decode') and hasattr(value, 'encode'):
                return value.encode('utf-8')

        return value


def verify_version(client):
    version_str = client.get_system_setting('version')
    version = [int(p) for p in version_str.split('.')]
    if len(version) < 2:
        raise ModuleFailException(
            'unsupported NSO version format {0}'.format(version_str))
    if version[0] < 4 or version[1] < 4 or (version[1] == 4 and version[2] < 3):
        raise ModuleFailException(
            'unsupported NSO version {0}, only 4.4.3 or later is supported'.format(version_str))


def connect(params):
    client = JsonRpc(params['url'])
    client.login(params['username'], params['password'])
    return client


def main():
    module = AnsibleModule(
        argument_spec=dict(
            url=dict(required=True),
            username=dict(required=True, no_log=True),
            password=dict(required=True, no_log=True),
            path=dict(required=True),
            input=dict(required=False, type='dict', default={}),
            output_required=dict(required=False, type='dict', default={}),
            output_invalid=dict(required=False, type='dict', default={}),
            validate_strict=dict(required=False, type='bool', default=False),
        ),
        supports_check_mode=False
    )
    p = module.params

    client = connect(p)
    nso_action = NsoAction(
        module,
        client,
        p['path'],
        p['input'],
        p['output_required'],
        p['output_invalid'],
        p['validate_strict'])
    try:
        verify_version(client)

        output = nso_action.main()
        client.logout()
        module.exit_json(changed=True, output=output)
    except NsoException as ex:
        client.logout()
        module.fail_json(msg=ex.message)
    except ModuleFailException as ex:
        client.logout()
        module.fail_json(msg=ex.message)


if __name__ == '__main__':
    main()
