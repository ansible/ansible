#!/usr/bin/python
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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/> .
#

DOCUMENTATION = '''
---
module: nxos_vlan
version_added: "2.1"
short_description: Manages VLAN resources and attributes
description:
    - Manages VLAN configurations on NX-OS switches
author: Jason Edelman (@jedelman8)
extends_documentation_fragment: nxos
options:
    vlan_id:
        description:
            - single vlan id
        required: false
        default: null
    vlan_range:
        description:
            - range of VLANs such as 2-10 or 2,5,10-15, etc.
        required: false
        default: null
    name:
        description:
            - name of VLAN
        required: false
        default: null
    vlan_state:
        description:
            - Manage the vlan operational state of the VLAN
              (equivalent to state {active | suspend} command
        required: false
        default: active
        choices: ['active','suspend']
    admin_state:
        description:
            - Manage the vlan admin state of the VLAN equivalent
              to shut/no shut in vlan config mode
        required: false
        default: up
        choices: ['up','down']
    mapped_vni:
        description:
            - The Virtual Network Identifier (VNI) id that is mapped to the
              VLAN. Valid values are integer and keyword 'default'.
        required: false
        default: null
        version_added: "2.2"
    state:
        description:
            - Manage the state of the resource
        required: false
        default: present
        choices: ['present','absent']

'''
EXAMPLES = '''
# Ensure a range of VLANs are not present on the switch
- nxos_vlan: vlan_range="2-10,20,50,55-60,100-150" host=68.170.147.165 username=cisco password=cisco state=absent transport=nxapi

# Ensure VLAN 50 exists with the name WEB and is in the shutdown state
- nxos_vlan: vlan_id=50 host=68.170.147.165 admin_state=down name=WEB transport=nxapi username=cisco password=cisco

# Ensure VLAN is NOT on the device
- nxos_vlan: vlan_id=50 host=68.170.147.165 state=absent transport=nxapi username=cisco password=cisco


'''

RETURN = '''

proposed_vlans_list:
    description: list of VLANs being proposed
    returned: always
    type: list
    sample: ["100"]
existing_vlans_list:
    description: list of existing VLANs on the switch prior to making changes
    returned: always
    type: list
    sample: ["1", "2", "3", "4", "5", "20"]
end_state_vlans_list:
    description: list of VLANs after the module is executed
    returned: always
    type: list
    sample:  ["1", "2", "3", "4", "5", "20", "100"]
proposed:
    description: k/v pairs of parameters passed into module (does not include
                 vlan_id or vlan_range)
    returned: always
    type: dict or null
    sample: {"admin_state": "down", "name": "app_vlan",
            "vlan_state": "suspend", "mapped_vni": "5000"}
existing:
    description: k/v pairs of existing vlan or null when using vlan_range
    returned: always
    type: dict
    sample: {"admin_state": "down", "name": "app_vlan",
             "vlan_id": "20", "vlan_state": "suspend", "mapped_vni": ""}
end_state:
    description: k/v pairs of the VLAN after executing module or null
                 when using vlan_range
    returned: always
    type: dict or null
    sample: {"admin_state": "down", "name": "app_vlan", "vlan_id": "20",
             "vlan_state": "suspend", "mapped_vni": "5000"}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "present"
updates:
    description: command string sent to the device
    returned: always
    type: list
    sample: ["vlan 20", "vlan 55", "vn-segment 5000"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true

'''

# COMMON CODE FOR MIGRATION

import re
import time
import collections
import itertools
import shlex
import json

from ansible.module_utils.basic import AnsibleModule, env_fallback, get_exception
from ansible.module_utils.basic import BOOLEANS_TRUE, BOOLEANS_FALSE
from ansible.module_utils.shell import Shell, ShellError, HAS_PARAMIKO
from ansible.module_utils.netcfg import parse
from ansible.module_utils.urls import fetch_url


DEFAULT_COMMENT_TOKENS = ['#', '!']

class ConfigLine(object):

    def __init__(self, text):
        self.text = text
        self.children = list()
        self.parents = list()
        self.raw = None

    @property
    def line(self):
        line = ['set']
        line.extend([p.text for p in self.parents])
        line.append(self.text)
        return ' '.join(line)

    def __str__(self):
        return self.raw

    def __eq__(self, other):
        if self.text == other.text:
            return self.parents == other.parents

    def __ne__(self, other):
        return not self.__eq__(other)

def ignore_line(text, tokens=None):
    for item in (tokens or DEFAULT_COMMENT_TOKENS):
        if text.startswith(item):
            return True

def get_next(iterable):
    item, next_item = itertools.tee(iterable, 2)
    next_item = itertools.islice(next_item, 1, None)
    return itertools.izip_longest(item, next_item)

def parse(lines, indent, comment_tokens=None):
    toplevel = re.compile(r'\S')
    childline = re.compile(r'^\s*(.+)$')

    ancestors = list()
    config = list()

    for line in str(lines).split('\n'):
        text = str(re.sub(r'([{};])', '', line)).strip()

        cfg = ConfigLine(text)
        cfg.raw = line

        if not text or ignore_line(text, comment_tokens):
            continue

        # handle top level commands
        if toplevel.match(line):
            ancestors = [cfg]

        # handle sub level commands
        else:
            match = childline.match(line)
            line_indent = match.start(1)
            level = int(line_indent / indent)
            parent_level = level - 1

            cfg.parents = ancestors[:level]

            if level > len(ancestors):
                config.append(cfg)
                continue

            for i in range(level, len(ancestors)):
                ancestors.pop()

            ancestors.append(cfg)
            ancestors[parent_level].children.append(cfg)

        config.append(cfg)

    return config


class CustomNetworkConfig(object):

    def __init__(self, indent=None, contents=None, device_os=None):
        self.indent = indent or 1
        self._config = list()
        self._device_os = device_os

        if contents:
            self.load(contents)

    @property
    def items(self):
        return self._config

    @property
    def lines(self):
        lines = list()
        for item, next_item in get_next(self.items):
            if next_item is None:
                lines.append(item.line)
            elif not next_item.line.startswith(item.line):
                lines.append(item.line)
        return lines

    def __str__(self):
        text = ''
        for item in self.items:
            if not item.parents:
                expand = self.get_section(item.text)
                text += '%s\n' % self.get_section(item.text)
        return str(text).strip()

    def load(self, contents):
        self._config = parse(contents, indent=self.indent)

    def load_from_file(self, filename):
        self.load(open(filename).read())

    def get(self, path):
        if isinstance(path, basestring):
            path = [path]
        for item in self._config:
            if item.text == path[-1]:
                parents = [p.text for p in item.parents]
                if parents == path[:-1]:
                    return item

    def search(self, regexp, path=None):
        regex = re.compile(r'^%s' % regexp, re.M)

        if path:
            parent = self.get(path)
            if not parent or not parent.children:
                return
            children = [c.text for c in parent.children]
            data = '\n'.join(children)
        else:
            data = str(self)

        match = regex.search(data)
        if match:
            if match.groups():
                values = match.groupdict().values()
                groups = list(set(match.groups()).difference(values))
                return (groups, match.groupdict())
            else:
                return match.group()

    def findall(self, regexp):
        regexp = r'%s' % regexp
        return re.findall(regexp, str(self))

    def expand(self, obj, items):
        block = [item.raw for item in obj.parents]
        block.append(obj.raw)

        current_level = items
        for b in block:
            if b not in current_level:
                current_level[b] = collections.OrderedDict()
            current_level = current_level[b]
        for c in obj.children:
            if c.raw not in current_level:
                current_level[c.raw] = collections.OrderedDict()

    def to_lines(self, section):
        lines = list()
        for entry in section[1:]:
            line = ['set']
            line.extend([p.text for p in entry.parents])
            line.append(entry.text)
            lines.append(' '.join(line))
        return lines

    def to_block(self, section):
        return '\n'.join([item.raw for item in section])

    def get_section(self, path):
        try:
            section = self.get_section_objects(path)
            if self._device_os == 'junos':
                return self.to_lines(section)
            return self.to_block(section)
        except ValueError:
            return list()

    def get_section_objects(self, path):
        if not isinstance(path, list):
            path = [path]
        obj = self.get_object(path)
        if not obj:
            raise ValueError('path does not exist in config')
        return self.expand_section(obj)

    def expand_section(self, configobj, S=None):
        if S is None:
            S = list()
        S.append(configobj)
        for child in configobj.children:
            if child in S:
                continue
            self.expand_section(child, S)
        return S

    def flatten(self, data, obj=None):
        if obj is None:
            obj = list()
        for k, v in data.items():
            obj.append(k)
            self.flatten(v, obj)
        return obj

    def get_object(self, path):
        for item in self.items:
            if item.text == path[-1]:
                parents = [p.text for p in item.parents]
                if parents == path[:-1]:
                    return item

    def get_children(self, path):
        obj = self.get_object(path)
        if obj:
            return obj.children

    def difference(self, other, path=None, match='line', replace='line'):
        updates = list()

        config = self.items
        if path:
            config = self.get_children(path) or list()

        if match == 'line':
            for item in config:
                if item not in other.items:
                    updates.append(item)

        elif match == 'strict':
            if path:
                current = other.get_children(path) or list()
            else:
                current = other.items

            for index, item in enumerate(config):
                try:
                    if item != current[index]:
                        updates.append(item)
                except IndexError:
                    updates.append(item)

        elif match == 'exact':
            if path:
                current = other.get_children(path) or list()
            else:
                current = other.items

            if len(current) != len(config):
                updates.extend(config)
            else:
                for ours, theirs in itertools.izip(config, current):
                    if ours != theirs:
                        updates.extend(config)
                        break

        if self._device_os == 'junos':
            return updates

        diffs = collections.OrderedDict()
        for update in updates:
            if replace == 'block' and update.parents:
                update = update.parents[-1]
            self.expand(update, diffs)

        return self.flatten(diffs)

    def replace(self, replace, text=None, regex=None, parents=None,
            add_if_missing=False, ignore_whitespace=False):
        match = None

        parents = parents or list()
        if text is None and regex is None:
            raise ValueError('missing required arguments')

        if not regex:
            regex = ['^%s$' % text]

        patterns = [re.compile(r, re.I) for r in to_list(regex)]

        for item in self.items:
            for regexp in patterns:
                if ignore_whitespace is True:
                    string = item.text
                else:
                    string = item.raw
                if regexp.search(item.text):
                    if item.text != replace:
                        if parents == [p.text for p in item.parents]:
                            match = item
                            break

        if match:
            match.text = replace
            indent = len(match.raw) - len(match.raw.lstrip())
            match.raw = replace.rjust(len(replace) + indent)

        elif add_if_missing:
            self.add(replace, parents=parents)


    def add(self, lines, parents=None):
        """Adds one or lines of configuration
        """

        ancestors = list()
        offset = 0
        obj = None

        ## global config command
        if not parents:
            for line in to_list(lines):
                item = ConfigLine(line)
                item.raw = line
                if item not in self.items:
                    self.items.append(item)

        else:
            for index, p in enumerate(parents):
                try:
                    i = index + 1
                    obj = self.get_section_objects(parents[:i])[0]
                    ancestors.append(obj)

                except ValueError:
                    # add parent to config
                    offset = index * self.indent
                    obj = ConfigLine(p)
                    obj.raw = p.rjust(len(p) + offset)
                    if ancestors:
                        obj.parents = list(ancestors)
                        ancestors[-1].children.append(obj)
                    self.items.append(obj)
                    ancestors.append(obj)

            # add child objects
            for line in to_list(lines):
                # check if child already exists
                for child in ancestors[-1].children:
                    if child.text == line:
                        break
                else:
                    offset = len(parents) * self.indent
                    item = ConfigLine(line)
                    item.raw = line.rjust(len(line) + offset)
                    item.parents = ancestors
                    ancestors[-1].children.append(item)
                    self.items.append(item)


def argument_spec():
    return dict(
        # config options
        running_config=dict(aliases=['config']),
        save_config=dict(type='bool', default=False, aliases=['save'])
    )
nxos_argument_spec = argument_spec()


NET_PASSWD_RE = re.compile(r"[\r\n]?password: $", re.I)

NET_COMMON_ARGS = dict(
    host=dict(required=True),
    port=dict(type='int'),
    username=dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    password=dict(no_log=True, fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD'])),
    ssh_keyfile=dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
    transport=dict(default='cli', choices=['cli', 'nxapi']),
    use_ssl=dict(default=False, type='bool'),
    validate_certs=dict(default=True, type='bool'),
    provider=dict(type='dict'),
    timeout=dict(default=10, type='int')
)

NXAPI_COMMAND_TYPES = ['cli_show', 'cli_show_ascii', 'cli_conf', 'bash']

NXAPI_ENCODINGS = ['json', 'xml']

CLI_PROMPTS_RE = [
    re.compile(r'[\r\n]?[a-zA-Z]{1}[a-zA-Z0-9-]*[>|#|%](?:\s*)$'),
    re.compile(r'[\r\n]?[a-zA-Z]{1}[a-zA-Z0-9-]*\(.+\)#(?:\s*)$')
]

CLI_ERRORS_RE = [
    re.compile(r"% ?Error"),
    re.compile(r"^% \w+", re.M),
    re.compile(r"% ?Bad secret"),
    re.compile(r"invalid input", re.I),
    re.compile(r"(?:incomplete|ambiguous) command", re.I),
    re.compile(r"connection timed out", re.I),
    re.compile(r"[^\r\n]+ not found", re.I),
    re.compile(r"'[^']' +returned error code: ?\d+"),
    re.compile(r"syntax error"),
    re.compile(r"unknown command")
]


def to_list(val):
    if isinstance(val, (list, tuple)):
        return list(val)
    elif val is not None:
        return [val]
    else:
        return list()


class Nxapi(object):

    def __init__(self, module):
        self.module = module

        # sets the module_utils/urls.py req parameters
        self.module.params['url_username'] = module.params['username']
        self.module.params['url_password'] = module.params['password']

        self.url = None
        self._nxapi_auth = None

    def _get_body(self, commands, command_type, encoding, version='1.0', chunk='0', sid=None):
        """Encodes a NXAPI JSON request message
        """
        if isinstance(commands, (list, set, tuple)):
            commands = ' ;'.join(commands)

        if encoding not in NXAPI_ENCODINGS:
            msg = 'invalid encoding, received %s, exceped one of %s' % \
                    (encoding, ','.join(NXAPI_ENCODINGS))
            self.module_fail_json(msg=msg)

        msg = {
            'version': version,
            'type': command_type,
            'chunk': chunk,
            'sid': sid,
            'input': commands,
            'output_format': encoding
        }
        return dict(ins_api=msg)

    def connect(self):
        host = self.module.params['host']
        port = self.module.params['port']

        if self.module.params['use_ssl']:
            proto = 'https'
            if not port:
                port = 443
        else:
            proto = 'http'
            if not port:
                port = 80

        self.url = '%s://%s:%s/ins' % (proto, host, port)

    def send(self, commands, command_type='cli_show_ascii', encoding='json'):
        """Send commands to the device.
        """
        clist = to_list(commands)

        if command_type not in NXAPI_COMMAND_TYPES:
            msg = 'invalid command_type, received %s, exceped one of %s' % \
                    (command_type, ','.join(NXAPI_COMMAND_TYPES))
            self.module_fail_json(msg=msg)

        data = self._get_body(clist, command_type, encoding)
        data = self.module.jsonify(data)

        headers = {'Content-Type': 'application/json'}
        if self._nxapi_auth:
            headers['Cookie'] = self._nxapi_auth

        response, headers = fetch_url(self.module, self.url, data=data,
                headers=headers, method='POST')

        self._nxapi_auth = headers.get('set-cookie')

        if headers['status'] != 200:
            self.module.fail_json(**headers)

        response = self.module.from_json(response.read())
        result = list()

        output = response['ins_api']['outputs']['output']
        for item in to_list(output):
            if item['code'] != '200':
                self.module.fail_json(**item)
            else:
                result.append(item['body'])

        return result


class Cli(object):

    def __init__(self, module):
        self.module = module
        self.shell = None

    def connect(self, **kwargs):
        host = self.module.params['host']
        port = self.module.params['port'] or 22

        username = self.module.params['username']
        password = self.module.params['password']
        timeout = self.module.params['timeout']
        key_filename = self.module.params['ssh_keyfile']

        allow_agent = (key_filename is not None) or (key_filename is None and password is None)

        try:
            self.shell = Shell(kickstart=False, prompts_re=CLI_PROMPTS_RE,
                    errors_re=CLI_ERRORS_RE)
            self.shell.open(host, port=port, username=username,
                    password=password, key_filename=key_filename,
                    allow_agent=allow_agent, timeout=timeout)
        except ShellError:
            e = get_exception()
            msg = 'failed to connect to %s:%s - %s' % (host, port, str(e))
            self.module.fail_json(msg=msg)

    def send(self, commands, encoding='text'):
        try:
            return self.shell.send(commands)
        except ShellError:
            e = get_exception()
            self.module.fail_json(msg=e.message, commands=commands)


class NetworkModule(AnsibleModule):

    def __init__(self, *args, **kwargs):
        super(NetworkModule, self).__init__(*args, **kwargs)
        self.connection = None
        self._config = None
        self._connected = False

    @property
    def connected(self):
        return self._connected

    @property
    def config(self):
        if not self._config:
            self._config = self.get_config()
        return self._config

    def _load_params(self):
        super(NetworkModule, self)._load_params()
        provider = self.params.get('provider') or dict()
        for key, value in provider.items():
            if key in NET_COMMON_ARGS:
                if self.params.get(key) is None and value is not None:
                    self.params[key] = value

    def connect(self):
        cls = globals().get(str(self.params['transport']).capitalize())
        try:
            self.connection = cls(self)
        except TypeError:
            e = get_exception()
            self.fail_json(msg=e.message)

        self.connection.connect()

        if self.params['transport'] == 'cli':
            self.connection.send('terminal length 0')

        self._connected = True

    def configure(self, commands):
        commands = to_list(commands)
        if self.params['transport'] == 'cli':
            return self.configure_cli(commands)
        else:
            return self.execute(commands, command_type='cli_conf')

    def configure_cli(self, commands):
        commands = to_list(commands)
        commands.insert(0, 'configure')
        responses = self.execute(commands)
        responses.pop(0)
        return responses

    def execute(self, commands, **kwargs):
        if not self.connected:
            self.connect()
        return self.connection.send(commands, **kwargs)

    def disconnect(self):
        self.connection.close()
        self._connected = False

    def parse_config(self, cfg):
        return parse(cfg, indent=2)

    def get_config(self):
        cmd = 'show running-config'
        if self.params.get('include_defaults'):
            cmd += ' all'
        response = self.execute(cmd)
        return response[0]


def get_module(**kwargs):
    """Return instance of NetworkModule
    """
    argument_spec = NET_COMMON_ARGS.copy()
    if kwargs.get('argument_spec'):
        argument_spec.update(kwargs['argument_spec'])
    kwargs['argument_spec'] = argument_spec

    module = NetworkModule(**kwargs)

    if module.params['transport'] == 'cli' and not HAS_PARAMIKO:
        module.fail_json(msg='paramiko is required but does not appear to be installed')

    return module


def custom_get_config(module, include_defaults=False):
    config = module.params['running_config']
    if not config:
        cmd = 'show running-config'
        if module.params['include_defaults']:
            cmd += ' all'
        if module.params['transport'] == 'nxapi':
            config = module.execute([cmd], command_type='cli_show_ascii')[0]
        else:
            config = module.execute([cmd])[0]

    return CustomNetworkConfig(indent=2, contents=config)

def load_config(module, candidate):
    config = custom_get_config(module)

    commands = candidate.difference(config)
    commands = [str(c).strip() for c in commands]

    save_config = module.params['save_config']

    result = dict(changed=False)

    if commands:
        if not module.check_mode:
            module.configure(commands)
            if save_config:
                module.config.save_config()

        result['changed'] = True
        result['updates'] = commands

    return result
# END OF COMMON CODE

def vlan_range_to_list(vlans):
    result = []
    if vlans:
        for part in vlans.split(','):
            if part == 'none':
                break
            if '-' in part:
                a, b = part.split('-')
                a, b = int(a), int(b)
                result.extend(range(a, b + 1))
            else:
                a = int(part)
                result.append(a)
        return numerical_sort(result)
    return result


def numerical_sort(string_int_list):
    """Sort list of strings (VLAN IDs) that are digits in numerical order.
    """

    as_int_list = []
    as_str_list = []
    for vlan in string_int_list:
        as_int_list.append(int(vlan))
    as_int_list.sort()
    for vlan in as_int_list:
        as_str_list.append(str(vlan))
    return as_str_list


def build_commands(vlans, state):
    commands = []
    for vlan in vlans:
        if state == 'present':
            command = 'vlan {0}'.format(vlan)
            commands.append(command)
        elif state == 'absent':
            command = 'no vlan {0}'.format(vlan)
            commands.append(command)
    return commands


def get_vlan_config_commands(vlan, vid):
    """Build command list required for VLAN configuration
    """

    reverse_value_map = {
        "admin_state": {
            "down": "shutdown",
            "up": "no shutdown"
        }
    }

    if vlan.get('admin_state'):
        # apply value map when making change to the admin state
        # note: would need to be a loop or more in depth check if
        # value map has more than 1 key
        vlan = apply_value_map(reverse_value_map, vlan)

    VLAN_ARGS = {
        'name': 'name {0}',
        'vlan_state': 'state {0}',
        'admin_state': '{0}',
        'mode': 'mode {0}',
        'mapped_vni': 'vn-segment {0}'
    }

    commands = []

    for param, value in vlan.iteritems():
        if param == 'mapped_vni' and value == 'default':
            command = 'no vn-segment'
        else:
            command = VLAN_ARGS.get(param).format(vlan.get(param))
        if command:
            commands.append(command)

    commands.insert(0, 'vlan ' + vid)
    commands.append('exit')

    return commands


def get_list_of_vlans(module):
    command = 'show vlan'
    body = execute_show_command(command, module)
    vlan_list = []
    vlan_table = body[0].get('TABLE_vlanbrief')['ROW_vlanbrief']

    if isinstance(vlan_table, list):
        for vlan in vlan_table:
            vlan_list.append(str(vlan['vlanshowbr-vlanid-utf']))
    else:
        vlan_list.append('1')

    return vlan_list


def get_vni(vlanid, module):
    command = 'show run all | section vlan.{0}'.format(vlanid)
    body = execute_show_command(command, module, command_type='cli_show_ascii')[0]
    value = ''
    if body:
        REGEX = re.compile(r'(?:vn-segment\s)(?P<value>.*)$', re.M)
        if 'vn-segment' in body:
            value = REGEX.search(body).group('value')
    return value


def get_vlan(vlanid, module):
    """Get instance of VLAN as a dictionary
    """

    command = 'show vlan id ' + vlanid

    body = execute_show_command(command, module)

    try:
        vlan_table = body[0]['TABLE_vlanbriefid']['ROW_vlanbriefid']
    except (TypeError, IndexError):
        return {}

    key_map = {
        "vlanshowbr-vlanid-utf": "vlan_id",
        "vlanshowbr-vlanname": "name",
        "vlanshowbr-vlanstate": "vlan_state",
        "vlanshowbr-shutstate": "admin_state"
    }

    vlan = apply_key_map(key_map, vlan_table)

    value_map = {
        "admin_state": {
            "shutdown": "down",
            "noshutdown": "up"
        }
    }

    vlan = apply_value_map(value_map, vlan)
    vlan['mapped_vni'] = get_vni(vlanid, module)
    return vlan


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
            new_dict[new_key] = str(value)
    return new_dict


def apply_value_map(value_map, resource):
    for key, value in value_map.items():
        resource[key] = value[resource.get(key)]
    return resource


def execute_config_command(commands, module):
    try:
        module.configure(commands)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending CLI commands',
                         error=str(clie), commands=commands)
    except AttributeError:
        try:
            commands.insert(0, 'configure')
            module.cli.add_commands(commands, output='config')
            module.cli.run_commands()
        except ShellError:
            clie = get_exception()
            module.fail_json(msg='Error sending CLI commands',
                             error=str(clie), commands=commands)


def get_cli_body_ssh(command, response, module):
    """Get response for when transport=cli.  This is kind of a hack and mainly
    needed because these modules were originally written for NX-API.  And
    not every command supports "| json" when using cli/ssh.  As such, we assume
    if | json returns an XML string, it is a valid command, but that the
    resource doesn't exist yet.
    """
    if 'show run' in command or response[0] == '\n':
        body = response
    elif 'xml' in response[0]:
        body = []
    else:
        try:
            body = [json.loads(response[0])]
        except ValueError:
            module.fail_json(msg='Command does not support JSON output',
                             command=command)
    return body


def execute_show(cmds, module, command_type=None):
    try:
        if command_type:
            response = module.execute(cmds, command_type=command_type)
        else:
            response = module.execute(cmds)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending {0}'.format(command),
                         error=str(clie))
    except AttributeError:
        try:
            if command_type:
                command_type = command_type_map.get(command_type)
                module.cli.add_commands(cmds, output=command_type)
                response = module.cli.run_commands()
            else:
                module.cli.add_commands(cmds, raw=True)
                response = module.cli.run_commands()
        except ShellError:
            clie = get_exception()
            module.fail_json(msg='Error sending {0}'.format(cmds),
                             error=str(clie))
    return response


def execute_show_command(command, module, command_type='cli_show'):
    if module.params['transport'] == 'cli':
        if 'show run' not in command:
            command += ' | json'
        cmds = [command]
        response = execute_show(cmds, module)
        body = get_cli_body_ssh(command, response, module)
    elif module.params['transport'] == 'nxapi':
        cmds = [command]
        body = execute_show(cmds, module, command_type=command_type)

    return body


def main():
    argument_spec = dict(
            vlan_id=dict(required=False, type='str'),
            vlan_range=dict(required=False),
            name=dict(required=False),
            vlan_state=dict(choices=['active', 'suspend'], required=False),
            mapped_vni=dict(required=False, type='str'),
            state=dict(choices=['present', 'absent'], default='present',
                       required=False),
            admin_state=dict(choices=['up', 'down'], required=False),
    )
    module = get_module(argument_spec=argument_spec,
                        mutually_exclusive=[['vlan_range', 'name'],
                                            ['vlan_id', 'vlan_range']],
                        supports_check_mode=True)

    vlan_range = module.params['vlan_range']
    vlan_id = module.params['vlan_id']
    name = module.params['name']
    vlan_state = module.params['vlan_state']
    admin_state = module.params['admin_state']
    mapped_vni = module.params['mapped_vni']
    state = module.params['state']

    changed = False

    if vlan_id:
        if not vlan_id.isdigit():
            module.fail_json(msg='vlan_id must be a valid VLAN ID')

    args = dict(name=name, vlan_state=vlan_state,
                admin_state=admin_state, mapped_vni=mapped_vni)

    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)

    proposed_vlans_list = numerical_sort(vlan_range_to_list(
        vlan_id or vlan_range))
    existing_vlans_list = numerical_sort(get_list_of_vlans(module))
    commands = []
    existing = None

    if vlan_range:
        if state == 'present':
            # These are all of the VLANs being proposed that don't
            # already exist on the switch
            vlans_delta = list(
                set(proposed_vlans_list).difference(existing_vlans_list))
            commands = build_commands(vlans_delta, state)
        elif state == 'absent':
            # VLANs that are common between what is being proposed and
            # what is on the switch
            vlans_common = list(
                set(proposed_vlans_list).intersection(existing_vlans_list))
            commands = build_commands(vlans_common, state)
    else:
        existing = get_vlan(vlan_id, module)
        if state == 'absent':
            if existing:
                commands = ['no vlan ' + vlan_id]
        elif state == 'present':
            if (existing.get('mapped_vni') == '0' and
                proposed.get('mapped_vni') == 'default'):
                proposed.pop('mapped_vni')
            delta = dict(set(
                proposed.iteritems()).difference(existing.iteritems()))
            if delta or not existing:
                commands = get_vlan_config_commands(delta, vlan_id)

    end_state = existing
    end_state_vlans_list = existing_vlans_list

    if commands:
        if existing.get('mapped_vni'):
            if (existing.get('mapped_vni') != proposed.get('mapped_vni') and
                existing.get('mapped_vni') != '0' and proposed.get('mapped_vni') != 'default'):
                commands.insert(1, 'no vn-segment')
        if module.check_mode:
            module.exit_json(changed=True,
                             commands=commands)
        else:
            execute_config_command(commands, module)
            changed = True
            end_state_vlans_list = numerical_sort(get_list_of_vlans(module))
            if 'configure' in commands:
                commands.pop(0)
            if vlan_id:
                end_state = get_vlan(vlan_id, module)

    results = {}
    results['proposed_vlans_list'] = proposed_vlans_list
    results['existing_vlans_list'] = existing_vlans_list
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['end_state_vlans_list'] = end_state_vlans_list
    results['updates'] = commands
    results['changed'] = changed

    module.exit_json(**results)


if __name__ == '__main__':
    main()
