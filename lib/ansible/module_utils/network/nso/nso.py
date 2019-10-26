# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Cisco and/or its affiliates.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.urls import open_url
from ansible.module_utils._text import to_text

import json
import re
import socket

try:
    unicode
    HAVE_UNICODE = True
except NameError:
    unicode = str
    HAVE_UNICODE = False


nso_argument_spec = dict(
    url=dict(type='str', required=True),
    username=dict(type='str', required=True, fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    password=dict(type='str', required=True, no_log=True, fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD'])),
    timeout=dict(type='int', default=300),
    validate_certs=dict(type='bool', default=False)
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
    def __init__(self, url, timeout, validate_certs):
        self._url = url
        self._timeout = timeout
        self._validate_certs = validate_certs
        self._id = 0
        self._trans = {}
        self._headers = {'Content-Type': 'application/json'}
        self._conn = None
        self._system_settings = {}

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
        if setting not in self._system_settings:
            payload = {'method': 'get_system_setting', 'params': {'operation': setting}}
            resp, resp_json = self._call(payload)
            self._system_settings[setting] = resp_json['result']
        return self._system_settings[setting]

    def new_trans(self, **kwargs):
        payload = {'method': 'new_trans', 'params': kwargs}
        resp, resp_json = self._call(payload)
        return resp_json['result']['th']

    def get_trans(self, mode):
        if mode not in self._trans:
            th = self.new_trans(mode=mode)
            self._trans[mode] = th
        return self._trans[mode]

    def delete_trans(self, th):
        payload = {'method': 'delete_trans', 'params': {'th': th}}
        resp, resp_json = self._call(payload)
        self._maybe_delete_trans(th)

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
        if len(resp_json['result']) == 0:
            self._maybe_delete_trans(th)
        return resp_json['result']

    def get_schema(self, **kwargs):
        payload = {'method': 'get_schema', 'params': kwargs}
        resp, resp_json = self._maybe_write_call(payload)
        return resp_json['result']

    def get_module_prefix_map(self, path=None):
        if path is None:
            payload = {'method': 'get_module_prefix_map', 'params': {}}
            resp, resp_json = self._call(payload)
        else:
            payload = {'method': 'get_module_prefix_map', 'params': {'path': path}}
            resp, resp_json = self._maybe_write_call(payload)
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
        try:
            resp, resp_json = self._read_call(payload)
            return resp_json['result']['exists']
        except NsoException as ex:
            # calling exists on a sub-list when the parent list does
            # not exists will cause data.not_found errors on recent
            # NSO
            if 'type' in ex.error and ex.error['type'] == 'data.not_found':
                return False
            raise

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

    def show_config(self, path, operational=False):
        payload = {
            'method': 'show_config',
            'params': {
                'path': path,
                'result_as': 'json',
                'with_oper': operational}
        }
        resp, resp_json = self._read_call(payload)
        return resp_json['result']

    def query(self, xpath, fields):
        payload = {
            'method': 'query',
            'params': {
                'xpath_expr': xpath,
                'selection': fields
            }
        }
        resp, resp_json = self._read_call(payload)
        return resp_json['result']['results']

    def run_action(self, th, path, params=None):
        if params is None:
            params = {}

        if is_version(self, [(4, 5), (4, 4, 3)]):
            result_format = 'json'
        else:
            result_format = 'normal'

        payload = {
            'method': 'run_action',
            'params': {
                'format': result_format,
                'path': path,
                'params': params
            }
        }
        if th is None:
            resp, resp_json = self._read_call(payload)
        else:
            payload['params']['th'] = th
            resp, resp_json = self._call(payload)

        if result_format == 'normal':
            # this only works for one-level results, list entries,
            # containers etc will have / in their name.
            result = {}
            for info in resp_json['result']:
                result[info['name']] = info['value']
        else:
            result = resp_json['result']

        return result

    def _call(self, payload):
        self._id += 1
        if 'id' not in payload:
            payload['id'] = self._id

        if 'jsonrpc' not in payload:
            payload['jsonrpc'] = '2.0'

        data = json.dumps(payload)
        try:
            resp = open_url(
                self._url, timeout=self._timeout,
                method='POST', data=data, headers=self._headers,
                validate_certs=self._validate_certs)
            if resp.code != 200:
                raise NsoException(
                    'NSO returned HTTP code {0}, expected 200'.format(resp.status), {})
        except socket.timeout:
            raise NsoException('request timed out against NSO at {0}'.format(self._url), {})

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
            payload['params']['th'] = self.get_trans(mode='read')
        return self._call(payload)

    def _write_call(self, payload):
        if 'th' not in payload['params']:
            payload['params']['th'] = self.get_trans(mode='read_write')
        return self._call(payload)

    def _maybe_write_call(self, payload):
        if 'read_write' in self._trans:
            return self._write_call(payload)
        else:
            return self._read_call(payload)

    def _maybe_delete_trans(self, th):
        for mode in ('read', 'read_write'):
            if th == self._trans.get(mode, None):
                del self._trans[mode]


class ValueBuilder(object):
    PATH_RE = re.compile('{[^}]*}')
    PATH_RE_50 = re.compile('{[^}]*}$')

    class Value(object):
        __slots__ = ['path', 'tag_path', 'state', 'value', 'deps']

        def __init__(self, path, state, value, deps):
            self.path = path
            self.tag_path = ValueBuilder.PATH_RE.sub('', path)
            self.state = state
            self.value = value
            self.deps = deps

            # nodes can depend on themselves
            if self.tag_path in self.deps:
                self.deps.remove(self.tag_path)

        def __lt__(self, rhs):
            l_len = len(self.path.split('/'))
            r_len = len(rhs.path.split('/'))
            if l_len == r_len:
                return self.path.__lt__(rhs.path)
            return l_len < r_len

        def __str__(self):
            return 'Value<path={0}, state={1}, value={2}>'.format(
                self.path, self.state, self.value)

    class ValueIterator(object):
        def __init__(self, client, values, delayed_values):
            self._client = client
            self._values = values
            self._delayed_values = delayed_values
            self._pos = 0

        def __iter__(self):
            return self

        def __next__(self):
            return self.next()

        def next(self):
            if self._pos >= len(self._values):
                if len(self._delayed_values) == 0:
                    raise StopIteration()

                builder = ValueBuilder(self._client, delay=False)
                for (parent, maybe_qname, value) in self._delayed_values:
                    builder.build(parent, maybe_qname, value)
                del self._delayed_values[:]
                self._values.extend(builder.values)

                return self.next()

            value = self._values[self._pos]
            self._pos += 1
            return value

    def __init__(self, client, mode='config', delay=None):
        self._client = client
        self._mode = mode
        self._schema_cache = {}
        self._module_prefix_map_cache = {}
        self._values = []
        self._values_dirty = False
        self._delay = delay is None and mode == 'config' and is_version(self._client, [(5, 0)])
        self._delayed_values = []

    def build(self, parent, maybe_qname, value, schema=None):
        qname, name = self.get_prefix_name(parent, maybe_qname)
        if name is None:
            path = parent
        else:
            path = '{0}/{1}'.format(parent, qname)

        if schema is None:
            schema = self._get_schema(path)

        if self._delay and schema.get('is_mount_point', False):
            # delay conversion of mounted values, required to get
            # shema information on 5.0 and later.
            self._delayed_values.append((parent, maybe_qname, value))
        elif self._is_leaf_list(schema) and is_version(self._client, [(4, 5)]):
            self._build_leaf_list(path, schema, value)
        elif self._is_leaf(schema):
            deps = schema.get('deps', [])
            if self._is_empty_leaf(schema):
                exists = self._client.exists(path)
                if exists and value != [None]:
                    self._add_value(path, State.ABSENT, None, deps)
                elif not exists and value == [None]:
                    self._add_value(path, State.PRESENT, None, deps)
            else:
                if maybe_qname is None:
                    value_type = self.get_type(path)
                else:
                    value_type = self._get_child_type(parent, qname)

                if 'identityref' in value_type:
                    if isinstance(value, list):
                        value = [ll_v for ll_v, t_ll_v
                                 in [self.get_prefix_name(parent, v) for v in value]]
                    else:
                        value, t_value = self.get_prefix_name(parent, value)
                self._add_value(path, State.SET, value, deps)
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
            self._values = ValueBuilder.sort_values(self._values)
            self._values_dirty = False

        return ValueBuilder.ValueIterator(self._client, self._values, self._delayed_values)

    @staticmethod
    def sort_values(values):
        class N(object):
            def __init__(self, v):
                self.tmp_mark = False
                self.mark = False
                self.v = v

        sorted_values = []
        nodes = [N(v) for v in sorted(values)]

        def get_node(tag_path):
            return next((m for m in nodes
                         if m.v.tag_path == tag_path), None)

        def is_cycle(n, dep, visited):
            visited.add(n.v.tag_path)
            if dep in visited:
                return True

            dep_n = get_node(dep)
            if dep_n is not None:
                for sub_dep in dep_n.v.deps:
                    if is_cycle(dep_n, sub_dep, visited):
                        return True

            return False

        # check for dependency cycles, remove if detected. sort will
        # not be 100% but allows for a best-effort to work around
        # issue in NSO.
        for n in nodes:
            for dep in n.v.deps:
                if is_cycle(n, dep, set()):
                    n.v.deps.remove(dep)

        def visit(n):
            if n.tmp_mark:
                return False
            if not n.mark:
                n.tmp_mark = True
                for m in nodes:
                    if m.v.tag_path in n.v.deps:
                        if not visit(m):
                            return False

                n.tmp_mark = False
                n.mark = True

                sorted_values.insert(0, n.v)

            return True

        n = next((n for n in nodes if not n.mark), None)
        while n is not None:
            visit(n)
            n = next((n for n in nodes if not n.mark), None)

        return sorted_values[::-1]

    def _build_dict(self, path, schema, value):
        keys = schema.get('key', [])
        for dict_key, dict_value in value.items():
            qname, name = self.get_prefix_name(path, dict_key)
            if dict_key in ('__state', ) or name in keys:
                continue

            child_schema = self._find_child(path, schema, qname)
            self.build(path, dict_key, dict_value, child_schema)

    def _build_leaf_list(self, path, schema, value):
        deps = schema.get('deps', [])
        entry_type = self.get_type(path, schema)

        if self._mode == 'verify':
            for entry in value:
                if 'identityref' in entry_type:
                    entry, t_entry = self.get_prefix_name(path, entry)
                entry_path = '{0}{{{1}}}'.format(path, entry)
                if not self._client.exists(entry_path):
                    self._add_value(entry_path, State.ABSENT, None, deps)
        else:
            # remove leaf list if treated as a list and then re-create the
            # expected list entries.
            self._add_value(path, State.ABSENT, None, deps)

            for entry in value:
                if 'identityref' in entry_type:
                    entry, t_entry = self.get_prefix_name(path, entry)
                entry_path = '{0}{{{1}}}'.format(path, entry)
                self._add_value(entry_path, State.PRESENT, None, deps)

    def _build_list(self, path, schema, value):
        deps = schema.get('deps', [])
        for entry in value:
            entry_key = self._build_key(path, entry, schema['key'])
            entry_path = '{0}{{{1}}}'.format(path, entry_key)
            entry_state = entry.get('__state', 'present')
            entry_exists = self._client.exists(entry_path)

            if entry_state == 'absent':
                if entry_exists:
                    self._add_value(entry_path, State.ABSENT, None, deps)
            else:
                if not entry_exists:
                    self._add_value(entry_path, State.PRESENT, None, deps)
                if entry_state in State.SYNC_STATES:
                    self._add_value(entry_path, entry_state, None, deps)

            self.build(entry_path, None, entry)

    def _build_key(self, path, entry, schema_keys):
        key_parts = []
        for key in schema_keys:
            value = entry.get(key, None)
            if value is None:
                raise ModuleFailException(
                    'required leaf {0} in {1} not set in data'.format(
                        key, path))

            value_type = self._get_child_type(path, key)
            if 'identityref' in value_type:
                value, t_value = self.get_prefix_name(path, value)
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
            return '"{0}"'.format(q_key)
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

    def _add_value(self, path, state, value, deps):
        self._values.append(ValueBuilder.Value(path, state, value, deps))
        self._values_dirty = True

    def get_prefix_name(self, path, qname):
        if not isinstance(qname, (str, unicode)):
            return qname, None
        if ':' not in qname:
            return qname, qname

        module_prefix_map = self._get_module_prefix_map(path)
        module, name = qname.split(':', 1)
        if module not in module_prefix_map:
            raise ModuleFailException(
                'no module mapping for module {0}. loaded modules {1}'.format(
                    module, ','.join(sorted(module_prefix_map.keys()))))

        return '{0}:{1}'.format(module_prefix_map[module], name), name

    def _get_schema(self, path):
        return self._ensure_schema_cached(path)['data']

    def _get_child_type(self, parent_path, key):
        all_schema = self._ensure_schema_cached(parent_path)
        parent_schema = all_schema['data']
        meta = all_schema['meta']
        schema = self._find_child(parent_path, parent_schema, key)
        return self.get_type(parent_path, schema, meta)

    def get_type(self, path, schema=None, meta=None):
        if schema is None or meta is None:
            all_schema = self._ensure_schema_cached(path)
            schema = all_schema['data']
            meta = all_schema['meta']

        if self._is_leaf(schema):
            def get_type(meta, curr_type):
                if curr_type.get('primitive', False):
                    return [curr_type['name']]
                if 'namespace' in curr_type:
                    curr_type_key = '{0}:{1}'.format(
                        curr_type['namespace'], curr_type['name'])
                    type_info = meta['types'][curr_type_key][-1]
                    return get_type(meta, type_info)
                if 'leaf_type' in curr_type:
                    return get_type(meta, curr_type['leaf_type'][-1])
                if 'union' in curr_type:
                    union_types = []
                    for union_type in curr_type['union']:
                        union_types.extend(get_type(meta, union_type[-1]))
                    return union_types
                return [curr_type.get('name', 'unknown')]

            return get_type(meta, schema['type'])
        return None

    def _ensure_schema_cached(self, path):
        if not self._delay and is_version(self._client, [(5, 0)]):
            # newer versions of NSO support multiple different schemas
            # for different devices, thus the device is required to
            # look up the schema. Remove the key entry to get schema
            # logic working ok.
            path = ValueBuilder.PATH_RE_50.sub('', path)
        else:
            path = ValueBuilder.PATH_RE.sub('', path)

        if path not in self._schema_cache:
            schema = self._client.get_schema(path=path, levels=1)
            self._schema_cache[path] = schema
        return self._schema_cache[path]

    def _get_module_prefix_map(self, path):
        # newer versions of NSO support multiple mappings from module
        # to prefix depending on which device is used.
        if path != '' and is_version(self._client, [(5, 0)]):
            if path not in self._module_prefix_map_cache:
                self._module_prefix_map_cache[path] = self._client.get_module_prefix_map(path)
            return self._module_prefix_map_cache[path]

        if '' not in self._module_prefix_map_cache:
            self._module_prefix_map_cache[''] = self._client.get_module_prefix_map()
        return self._module_prefix_map_cache['']

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

    def _is_leaf_list(self, schema):
        return schema.get('kind', None) == 'leaf-list'

    def _is_leaf(self, schema):
        # still checking for leaf-list here to be compatible with pre
        # 4.5 versions of NSO.
        return schema.get('kind', None) in ('key', 'leaf', 'leaf-list')

    def _is_empty_leaf(self, schema):
        return (schema.get('kind', None) == 'leaf' and
                schema['type'].get('primitive', False) and
                schema['type'].get('name', '') == 'empty')


def connect(params):
    client = JsonRpc(params['url'],
                     params['timeout'],
                     params['validate_certs'])
    client.login(params['username'], params['password'])
    return client


def verify_version(client, required_versions):
    version_str = client.get_system_setting('version')
    if not verify_version_str(version_str, required_versions):
        supported_versions = ', '.join(
            ['.'.join([str(p) for p in required_version])
             for required_version in required_versions])
        raise ModuleFailException(
            'unsupported NSO version {0}. {1} or later supported'.format(
                version_str, supported_versions))


def is_version(client, required_versions):
    version_str = client.get_system_setting('version')
    return verify_version_str(version_str, required_versions)


def verify_version_str(version_str, required_versions):
    version_str = re.sub('_.*', '', version_str)

    version = [int(p) for p in version_str.split('.')]
    if len(version) < 2:
        raise ModuleFailException(
            'unsupported NSO version format {0}'.format(version_str))

    def check_version(required_version, version):
        for pos in range(len(required_version)):
            if pos >= len(version):
                return False
            if version[pos] > required_version[pos]:
                return True
            if version[pos] < required_version[pos]:
                return False
        return True

    for required_version in required_versions:
        if check_version(required_version, version):
            return True
    return False


def normalize_value(expected_value, value, key):
    if value is None:
        return None
    if (isinstance(expected_value, bool) and
            isinstance(value, (str, unicode))):
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
