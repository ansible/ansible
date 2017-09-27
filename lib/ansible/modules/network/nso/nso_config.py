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
module: nso_config
short_description: Manage NSO configuration and service synchronization.
description:
  - This module provides support for managing configuration in NSO and
    can also ensure services are in sync.
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
  data:
    description: >
      NSO data in format as | display json converted to YAML. List entries can
      be annotated with a __state entry. Set to in-sync/deep-in-sync for
      services to verify service is in sync with the network. Set to absent in
      list entries to ensure they are deleted if they exist in NSO.
    required: true
version_added: "2.5"
'''

EXAMPLES = '''
- name: Create L3VPN
  nso_config:
    url: http://localhost:8080/jsonrpc
    username: username
    password: password
    data:
      l3vpn:vpn:
        l3vpn:
        - name: company
          route-distinguisher: 999
          endpoint:
          - id: branch-office1
            ce-device: ce6
            ce-interface: GigabitEthernet0/12
            ip-network: 10.10.1.0/24
            bandwidth: 12000000
            as-number: 65101
          - id: branch-office2
            ce-device: ce1
            ce-interface: GigabitEthernet0/11
            ip-network: 10.7.7.0/24
            bandwidth: 6000000
            as-number: 65102
          - id: branch-office3
            __state: absent
        __state: in-sync
'''

RETURN = '''
changes:
    description: List of changes
    returned: always
    type: complex
    sample:
        - path: "/l3vpn:vpn/l3vpn{example}/endpoint{office}/bandwidth"
          from: '6000000'
          to: '12000000'
          type: set
    contains:
        path:
            description: Path to value changed
            returned: always
            type: string
        from:
            description: Previous value if any, else null
            returned: When previous value is present on value change
            type: string
        to:
            description: Current value if any, else null.
            returned: When new value is present on value change
        type:
            description: Type of change. create|delete|set|re-deploy
diffs:
    description: List of sync changes
    returned: always
    type: complex
    sample:
        - path: "/l3vpn:vpn/l3vpn{example}"
          diff: |2
             devices {
                 device pe3 {
                     config {
                         alu:service {
                             vprn 65101 {
                                 bgp {
                                     group example-ce6 {
            -                            peer-as 65102;
            +                            peer-as 65101;
                                     }
                                 }
                             }
                         }
                     }
                 }
             }
    contains:
        path:
            description: keypath to service changed
            returned: always
            type: string
        diff:
            description: configuration difference triggered the re-deploy
            returned: always
            type: string
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url

import json
import re
import sys

STATE_SET = 'set'
STATE_PRESENT = 'present'
STATE_ABSENT = 'absent'
STATE_CHECK_SYNC = 'check-sync'
STATE_DEEP_CHECK_SYNC = 'deep-check-sync'
STATE_IN_SYNC = 'in-sync'
STATE_DEEP_IN_SYNC = 'deep-in-sync'

SYNC_STATES = (STATE_CHECK_SYNC, STATE_DEEP_CHECK_SYNC,
               STATE_IN_SYNC, STATE_DEEP_IN_SYNC)


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

    def delete_trans(self, th):
        payload = {'method': 'delete_trans', 'params': {'th': th}}
        resp, resp_json = self._call(payload)

    def validate_trans(self, th):
        payload = {'method': 'validate_trans', 'params': {'th': th}}
        resp, resp_json = self._write_call(payload)
        return resp_json['result']

    def get_trans_changes(self, th):
        payload = {'method': 'get_trans_changes', 'params': {'th': th}}
        resp, resp_json = self._write_call(payload)
        return resp_json['result']['changes']

    def validate_commit(self, th):
        payload = {'method': 'validate_commit', 'params': {'th': th}}
        resp, resp_json = self._write_call(payload)
        return resp_json['result'].get('warnings', [])

    def commit(self, th):
        payload = {'method': 'commit', 'params': {'th': th}}
        resp, resp_json = self._write_call(payload)
        return resp_json['result']

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

    def create(self, th, path):
        payload = {'method': 'create', 'params': {'th': th, 'path': path}}
        self._write_call(payload)

    def delete(self, th, path):
        payload = {'method': 'delete', 'params': {'th': th, 'path': path}}
        self._write_call(payload)

    def set_value(self, th, path, value):
        payload = {
            'method': 'set_value',
            'params': {'th': th, 'path': path, 'value': value}
        }
        resp, resp_json = self._write_call(payload)
        return resp_json['result']

    def run_action(self, th, path, params=None):
        if params is None:
            params = {}

        payload = {
            'method': 'run_action',
            'params': {
                'format': 'normal',
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


class ValueBuilder(object):
    class Value(object):
        __slots__ = ['path', 'state', 'value']

        def __init__(self, path, state, value):
            self.path = path
            self.state = state
            self.value = value

        def __lt__(self, rhs):
            l_len = len(self.path.split('/'))
            r_len = len(rhs.path.split('/'))
            if l_len == r_len:
                return self.path.__lt__(rhs.path)
            return l_len < r_len

        def __str__(self):
            return 'Value<path={0}, state={1}, value={2}>'.format(
                self.path, self.state, self.value)

    def __init__(self, client):
        self._client = client
        self._schema_cache = {}
        self._module_prefix_map_cache = None
        self._values = []
        self._values_dirty = False
        self._path_re = re.compile('{[^}]*}')

    def build(self, parent, maybe_qname, value, schema=None):
        qname, name = self._get_prefix_name(maybe_qname)
        if name is None:
            path = parent
        else:
            path = '{0}/{1}'.format(parent, qname)

        if schema is None:
            schema = self._get_schema(path)

        if schema['kind'] in ('leaf', 'leaf-list'):
            if self._is_empty_leaf(schema):
                exists = self._client.exists(path)
                if exists and value != [None]:
                    self._add_value(path, STATE_ABSENT, None)
                elif not exists and value == [None]:
                    self._add_value(path, STATE_PRESENT, None)
            else:
                self._add_value(path, STATE_SET, value)
        elif isinstance(value, dict):
            self._build_dict(path, schema, value)
        elif isinstance(value, list):
            self._build_list(path, schema, value)
        else:
            raise ModuleFailException(
                'unsupported schema {0} at {1}'.format(
                    schema['kind'], path))

    @property
    def values(self):
        if self._values_dirty:
            self._values.sort()
            self._values_dirty = False

        return self._values

    def _build_dict(self, path, schema, value):
        keys = schema.get('key', [])
        for dict_key, dict_value in value.items():
            qname, name = self._get_prefix_name(dict_key)
            if dict_key in ('__state', ) or name in keys:
                continue

            child_schema = self._find_child(path, schema, qname)
            self.build(path, dict_key, dict_value, child_schema)

    def _build_list(self, path, schema, value):
        for entry in value:
            entry_key = self._build_key(path, entry, schema['key'])
            entry_path = '{0}{{{1}}}'.format(path, entry_key)
            entry_state = entry.get('__state', 'present')
            entry_exists = self._client.exists(entry_path)

            if entry_state == 'absent':
                if entry_exists:
                    self._add_value(entry_path, STATE_ABSENT, None)
            else:
                if not entry_exists:
                    self._add_value(entry_path, STATE_PRESENT, None)
                if entry_state in SYNC_STATES:
                    self._add_value(entry_path, entry_state, None)

            self.build(entry_path, None, entry)

    def _build_key(self, path, entry, schema_keys):
        key_parts = []
        for key in schema_keys:
            value = entry.get(key, None)
            if value is None:
                raise ModuleFailException(
                    'required leaf {0} in {1} not set in data'.format(
                        key, path))
            key_parts.append(self._quote_key(value))
        return ' '.join(key_parts)

    def _quote_key(self, key):
        if isinstance(key, bool):
            return key and 'true' or 'false'

        q_key = []
        for c in str(key):
            if c in ('{', '}', "'", '\\'):
                q_key.append('\\')
            q_key.append(c)
        q_key = ''.join(q_key)
        if ' ' in q_key:
            return '{0}'.format(q_key)
        return q_key

    def _find_child(self, path, schema, qname):
        if 'children' not in schema:
            schema = self._get_schema(path)

        # look for the qualified name if : is in the name
        name_key = ':' in qname and 'qname' or 'name'
        child_schema = next(
            (c for c in schema['children'] if c.get(name_key, None) == qname), None)
        if child_schema is not None:
            return child_schema

        # no child was found, look for a choice with a child matching
        for child_schema in schema['children']:
            if child_schema['kind'] != 'choice':
                continue

            for child_case in child_schema['cases']:
                choice_child_schema = next(
                    (c for c in child_case['children'] if c.get(name_key, None) == qname), None)
                if choice_child_schema is not None:
                    return choice_child_schema

        raise ModuleFailException(
            'no child in {0} with name {1}. children {2}'.format(
                path, qname, ','.join((c.get('qname', c.get('name', None)) for c in schema['children']))))

    def _add_value(self, path, state, value):
        self._values.append(ValueBuilder.Value(path, state, value))
        self._values_dirty = True

    def _get_prefix_name(self, qname):
        if qname is None:
            return None, None
        if ':' not in qname:
            return qname, qname

        module_prefix_map = self._get_module_prefix_map()
        module, name = qname.split(':', 1)
        if module not in module_prefix_map:
            raise ModuleFailException(
                'no module mapping for module {0}. loaded modules {1}'.format(
                    module, ','.join(sorted(module_prefix_map.keys()))))

        return '{0}:{1}'.format(module_prefix_map[module], name), name

    def _get_schema(self, path):
        path = self._path_re.sub('', path)
        if path not in self._schema_cache:
            schema = self._client.get_schema(path=path, levels=1)
            self._schema_cache[path] = schema['data']
        return self._schema_cache[path]

    def _get_module_prefix_map(self):
        if self._module_prefix_map_cache is None:
            self._module_prefix_map_cache = self._client.get_module_prefix_map()
        return self._module_prefix_map_cache

    def _is_empty_leaf(self, schema):
        return (schema['kind'] == 'leaf' and
                schema['type'].get('primitive', False) and
                schema['type'].get('name', '') == 'empty')


class NsoConfig(object):
    def __init__(self, check_mode, client, data):
        self._check_mode = check_mode
        self._client = client
        self._data = data

        self._changes = []
        self._diffs = []

    def main(self):
        # build list of values from configured data
        value_builder = ValueBuilder(self._client)
        for key, value in self._data.items():
            value_builder.build('', key, value)

        self._data_write(value_builder.values)

        # check sync AFTER configuration is written
        sync_values = self._sync_check(value_builder.values)
        self._sync_ensure(sync_values)

        return self._changes, self._diffs

    def _data_write(self, values):
        th = self._client.new_trans(mode='read_write')

        for value in values:
            if value.state == STATE_SET:
                self._client.set_value(th, value.path, value.value)
            elif value.state == STATE_PRESENT:
                self._client.create(th, value.path)
            elif value.state == STATE_ABSENT:
                self._client.delete(th, value.path)

        changes = self._client.get_trans_changes(th)
        for change in changes:
            if change['op'] == 'value_set':
                self._changes.append({
                    'path': change['path'],
                    'from': change['old'] or None,
                    'to': change['value'],
                    'type': 'set'
                })
            elif change['op'] in ('created', 'deleted'):
                self._changes.append({
                    'path': change['path'],
                    'type': change['op'][:-1]
                })

        if len(changes) > 0:
            warnings = self._client.validate_commit(th)
            if len(warnings) > 0:
                raise NsoException(
                    'failed to validate transaction with warnings: {0}'.format(
                        ', '.join((str(warning) for warning in warnings))), {})

        if self._check_mode or len(changes) == 0:
            self._client.delete_trans(th)
        else:
            self._client.commit(th)

    def _sync_check(self, values):
        sync_values = []

        for value in values:
            if value.state in (STATE_CHECK_SYNC, STATE_IN_SYNC):
                action = 'check-sync'
            elif value.state in (STATE_DEEP_CHECK_SYNC, STATE_DEEP_IN_SYNC):
                action = 'deep-check-sync'
            else:
                action = None

            if action is not None:
                action_path = '{0}/{1}'.format(value.path, action)
                action_params = {'outformat': 'cli'}
                resp = self._client.run_action(None, action_path, action_params)
                if len(resp) > 0:
                    sync_values.append(
                        ValueBuilder.Value(value.path, value.state, resp[0]['value']))

        return sync_values

    def _sync_ensure(self, sync_values):
        for value in sync_values:
            if value.state in (STATE_CHECK_SYNC, STATE_DEEP_CHECK_SYNC):
                raise NsoException(
                    '{0} out of sync, diff {1}'.format(value.path, value.value), {})

            action_path = '{0}/{1}'.format(value.path, 're-deploy')
            if not self._check_mode:
                result = self._client.run_action(None, action_path)
                if not result:
                    raise NsoException(
                        'failed to re-deploy {0}'.format(value.path), {})

            self._changes.append({'path': value.path, 'type': 're-deploy'})
            self._diffs.append({'path': value.path, 'diff': value.value})


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
            data=dict(required=True, type='dict')
        ),
        supports_check_mode=True
    )
    p = module.params

    client = connect(p)
    nso_config = NsoConfig(module.check_mode, client, p['data'])
    try:
        verify_version(client)

        changes, diffs = nso_config.main()
        client.logout()

        changed = len(changes) > 0
        module.exit_json(
            changed=changed, changes=changes, diffs=diffs)

    except NsoException as ex:
        client.logout()
        module.fail_json(msg=ex.message)
    except ModuleFailException as ex:
        client.logout()
        module.fail_json(msg=ex.message)


if __name__ == '__main__':
    main()
