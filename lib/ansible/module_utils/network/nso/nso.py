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


from ansible.module_utils.basic import env_fallback
from ansible.module_utils.urls import open_url

import json
import re

try:
    unicode
    HAVE_UNICODE = True
except NameError:
    unicode = str
    HAVE_UNICODE = False


nso_argument_spec = dict(
    url=dict(required=True),
    username=dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME']), required=True),
    password=dict(fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD']), required=True, no_log=True)
)


class State(object):
    SET = 'set'
    PRESENT = 'present'
    ABSENT = 'absent'
    CHECK_SYNC = 'check-sync'
    DEEP_CHECK_SYNC = 'deep-check-sync'
    IN_SYNC = 'in-sync'
    DEEP_IN_SYNC = 'deep-in-sync'

    SYNC_STATES = ('check-sync', 'deep-check-sync', 'in-sync', 'deep-in-sync')


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
            'method': 'login',
            'params': {'user': user, 'passwd': passwd}
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

        if self._is_leaf(schema):
            if self._is_empty_leaf(schema):
                exists = self._client.exists(path)
                if exists and value != [None]:
                    self._add_value(path, State.ABSENT, None)
                elif not exists and value == [None]:
                    self._add_value(path, State.PRESENT, None)
            else:
                value_type = self._get_type(parent, maybe_qname)
                if value_type == 'identityref':
                    value, t_value = self._get_prefix_name(value)
                self._add_value(path, State.SET, value)
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
                    self._add_value(entry_path, State.ABSENT, None)
            else:
                if not entry_exists:
                    self._add_value(entry_path, State.PRESENT, None)
                if entry_state in State.SYNC_STATES:
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

            value_type = self._get_type(path, key)
            if value_type == 'identityref':
                value, t_value = self._get_prefix_name(value)
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
        child_schema = self._get_child(schema, qname)
        if child_schema is not None:
            return child_schema

        # no child was found, look for a choice with a child matching
        for child_schema in schema['children']:
            if child_schema['kind'] != 'choice':
                continue
            choice_child_schema = self._get_choice_child(child_schema, qname)
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
        return self._ensure_schema_cached(path)['data']

    def _get_type(self, parent_path, key):
        all_schema = self._ensure_schema_cached(parent_path)
        parent_schema = all_schema['data']
        meta = all_schema['meta']

        schema = self._find_child(parent_path, parent_schema, key)
        if self._is_leaf(schema):
            path_type = schema['type']
            if path_type.get('primitive', False):
                return path_type['name']
            else:
                path_type_key = '{0}:{1}'.format(
                    path_type['namespace'], path_type['name'])
                type_info = meta['types'][path_type_key]
                return type_info[-1]['name']
        return None

    def _ensure_schema_cached(self, path):
        path = self._path_re.sub('', path)
        if path not in self._schema_cache:
            schema = self._client.get_schema(path=path, levels=1)
            self._schema_cache[path] = schema
        return self._schema_cache[path]

    def _get_module_prefix_map(self):
        if self._module_prefix_map_cache is None:
            self._module_prefix_map_cache = self._client.get_module_prefix_map()
        return self._module_prefix_map_cache

    def _get_child(self, schema, qname):
        # no child specified, return parent
        if qname is None:
            return schema

        name_key = ':' in qname and 'qname' or 'name'
        return next((c for c in schema['children']
                     if c.get(name_key, None) == qname), None)

    def _get_choice_child(self, schema, qname):
        name_key = ':' in qname and 'qname' or 'name'
        for child_case in schema['cases']:
            # look for direct child
            choice_child_schema = next(
                (c for c in child_case['children']
                 if c.get(name_key, None) == qname), None)
            if choice_child_schema is not None:
                return choice_child_schema

            # look for nested choice
            for child_schema in child_case['children']:
                if child_schema['kind'] != 'choice':
                    continue
                choice_child_schema = self._get_choice_child(child_schema, qname)
                if choice_child_schema is not None:
                    return choice_child_schema
        return None

    def _is_leaf(self, schema):
        return schema.get('kind', None) in ('key', 'leaf', 'leaf-list')

    def _is_empty_leaf(self, schema):
        return (schema.get('kind', None) == 'leaf' and
                schema['type'].get('primitive', False) and
                schema['type'].get('name', '') == 'empty')


def connect(params):
    client = JsonRpc(params['url'])
    client.login(params['username'], params['password'])
    return client


def verify_version(client):
    version_str = client.get_system_setting('version')
    version = [int(p) for p in version_str.split('.')]
    if len(version) < 2:
        raise ModuleFailException(
            'unsupported NSO version format {0}'.format(version_str))
    if (version[0] < 4 or version[1] < 4 or
            (version[1] == 4 and (len(version) < 3 or version[2] < 3))):
        raise ModuleFailException(
            'unsupported NSO version {0}, only 4.4.3 or later is supported'.format(version_str))


def normalize_value(expected_value, value, key):
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
                normalize_value(expected_value[i], value[i], '{0}[{1}]'.format(key, i)))
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
            n_k = normalize_value(k, k, '{0}[{1}]'.format(key, k))
            if n_k not in value:
                raise ModuleFailException('missing {0} in value'.format(n_k))
            normalized_value[n_k] = normalize_value(expected_value[k], value[k], '{0}[{1}]'.format(key, k))
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
