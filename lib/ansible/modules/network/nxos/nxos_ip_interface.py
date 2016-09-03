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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

DOCUMENTATION = '''
---
module: nxos_ip_interface
version_added: "2.1"
short_description: Manages L3 attributes for IPv4 and IPv6 interfaces
description:
    - Manages Layer 3 attributes for IPv4 and IPv6 interfaces
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - Interface must already be a L3 port when using this module
    - Logical interfaces (po, loop, svi) must be created first
    - I(mask) must be inserted in decimal format (i.e. 24) for
      both IPv6 and IPv4.
    - A single interface can have multiple IPv6 configured.

options:
    interface:
        description:
            - Full name of interface, i.e. Ethernet1/1, vlan10
        required: true
    addr:
        description:
            - IPv4 or IPv6 Address
        required: false
        default: null
    mask:
        description:
            - Subnet mask for IPv4 or IPv6 Address in decimal format
        required: false
        default: null
    state:
        description:
            - Specify desired state of the resource
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# ensure ipv4 address is configured on Ethernet1/32
- nxos_ip_interface: interface=Ethernet1/32 transport=nxapi version=v4 state=present addr=20.20.20.20 mask=24
# ensure ipv6 address is configured on Ethernet1/31
- nxos_ip_interface: interface=Ethernet1/31 transport=cli version=v6 state=present addr=2001::db8:800:200c:cccb mask=64
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"addr": "20.20.20.20", "interface": "ethernet1/32", "mask": "24"}
existing:
    description: k/v pairs of existing IP attributes on the interface
    type: dict
    sample: {"addresses": [{"addr": "11.11.11.11", "mask": 17}],
            "interface": "ethernet1/32", "prefix": "11.11.0.0",
            "type": "ethernet", "vrf": "default"}
end_state:
    description: k/v pairs of IP attributes after module execution
    returned: always
    type: dict
    sample: {"addresses": [{"addr": "20.20.20.20", "mask": 24}],
            "interface": "ethernet1/32", "prefix": "20.20.20.0",
            "type": "ethernet", "vrf": "default"}
state:
    description: state as sent in from the playbook
    returned: always
    type: string
    sample: "present"
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface ethernet1/32", "ip address 20.20.20.20/24"]
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

def execute_config_command(commands, module):
    try:
        module.configure(commands)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending CLI commands',
                         error=str(clie), commands=commands)


def get_cli_body_ssh(command, response, module):
    """Get response for when transport=cli.  This is kind of a hack and mainly
    needed because these modules were originally written for NX-API.  And
    not every command supports "| json" when using cli/ssh.  As such, we assume
    if | json returns an XML string, it is a valid command, but that the
    resource doesn't exist yet. Instead, we assume if '^' is found in response,
    it is an invalid command.
    """
    if 'xml' in response[0]:
        body = []
    elif '^' in response[0] or 'show run' in response[0] or response[0] == '\n':
        body = response
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
        module.fail_json(msg='Error sending {0}'.format(cmds),
                         error=str(clie))
    return response


def execute_show_command(command, module, command_type='cli_show'):
    if module.params['transport'] == 'cli':
        command += ' | json'
        cmds = [command]
        response = execute_show(cmds, module)
        body = get_cli_body_ssh(command, response, module)
    elif module.params['transport'] == 'nxapi':
        cmds = [command]
        body = execute_show(cmds, module, command_type=command_type)

    return body


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
            value = table.get(key)
            if value:
                new_dict[new_key] = str(value)
            else:
                new_dict[new_key] = value
    return new_dict


def get_interface_type(interface):
    if interface.upper().startswith('ET'):
        return 'ethernet'
    elif interface.upper().startswith('VL'):
        return 'svi'
    elif interface.upper().startswith('LO'):
        return 'loopback'
    elif interface.upper().startswith('MG'):
        return 'management'
    elif interface.upper().startswith('MA'):
        return 'management'
    elif interface.upper().startswith('PO'):
        return 'portchannel'
    else:
        return 'unknown'


def is_default(interface, module):
    command = 'show run interface {0}'.format(interface)

    try:
        body = execute_show_command(command, module)[0]
        if 'invalid' in body.lower():
            return 'DNE'
        else:
            raw_list = body.split('\n')
            if raw_list[-1].startswith('interface'):
                return True
            else:
                return False
    except (KeyError):
        return 'DNE'


def get_interface_mode(interface, intf_type, module):
    command = 'show interface {0}'.format(interface)
    mode = 'unknown'

    if intf_type in ['ethernet', 'portchannel']:
        body = execute_show_command(command, module)[0]

        if isinstance(body, str):
            if 'invalid interface format' in body.lower():
                module.fail_json(msg='Invalid interface name. Please check '
                                     'its format.', interface=interface)

        interface_table = body['TABLE_interface']['ROW_interface']
        mode = str(interface_table.get('eth_mode', 'layer3'))
        if mode == 'access' or mode == 'trunk':
            mode = 'layer2'
    elif intf_type == 'svi':
        mode = 'layer3'
    return mode


def send_show_command(interface_name, version, module):
    if version == 'v4':
        command = 'show ip interface {0}'.format(interface_name)
    elif version == 'v6':
        command = 'show ipv6 interface {0}'.format(interface_name)

    if module.params['transport'] == 'nxapi' and version == 'v6':
        body = execute_show_command(command, module,
                                    command_type='cli_show_ascii')
    else:
        body = execute_show_command(command, module)
    return body


def parse_structured_data(body, interface_name, version, module):
    address_list = []

    interface_key = {
        'subnet': 'prefix',
        'prefix': 'prefix'
    }

    try:
        interface_table = body[0]['TABLE_intf']['ROW_intf']
        try:
            vrf_table = body[0]['TABLE_vrf']['ROW_vrf']
            vrf = vrf_table['vrf-name-out']
        except KeyError:
            vrf = None
    except (KeyError, AttributeError):
        return {}

    interface = apply_key_map(interface_key, interface_table)
    interface['interface'] = interface_name
    interface['type'] = get_interface_type(interface_name)
    interface['vrf'] = vrf

    if version == 'v4':
        address = {}
        address['addr'] = interface_table.get('prefix', None)
        if address['addr'] is not None:
            address['mask'] = str(interface_table.get('masklen', None))
            interface['addresses'] = [address]
            prefix = "{0}/{1}".format(address['addr'], address['mask'])
            address_list.append(prefix)
        else:
            interface['addresses'] = []

    elif version == 'v6':
        address_list = interface_table.get('addr', [])
        interface['addresses'] = []

        if address_list:
            if not isinstance(address_list, list):
                address_list = [address_list]

            for ipv6 in address_list:
                address = {}
                splitted_address = ipv6.split('/')
                address['addr'] = splitted_address[0]
                address['mask'] = splitted_address[1]
                interface['addresses'].append(address)
        else:
            interface['addresses'] = []

    return interface, address_list


def parse_unstructured_data(body, interface_name, module):
    interface = {}
    address_list = []
    vrf = None

    body = body[0]
    if "ipv6 is disabled" not in body.lower():
        splitted_body = body.split('\n')

        # We can have multiple IPv6 on the same interface.
        # We need to parse them manually from raw output.
        for index in range(0, len(splitted_body) - 1):
            if "IPv6 address:" in splitted_body[index]:
                first_reference_point = index + 1
            elif "IPv6 subnet:" in splitted_body[index]:
                last_reference_point = index
                prefix_line = splitted_body[last_reference_point]
                prefix = prefix_line.split('IPv6 subnet:')[1].strip()
                interface['prefix'] = prefix

        interface_list_table = splitted_body[
                            first_reference_point:last_reference_point]

        for each_line in interface_list_table:
            address = each_line.strip().split(' ')[0]
            if address not in address_list:
                address_list.append(address)

        interface['addresses'] = []
        if address_list:
            for ipv6 in address_list:
                address = {}
                splitted_address = ipv6.split('/')
                address['addr'] = splitted_address[0]
                address['mask'] = splitted_address[1]
                interface['addresses'].append(address)

        try:
            vrf_regex = '.*VRF\s+(?P<vrf>\S+).*'
            match_vrf = re.match(vrf_regex, body, re.DOTALL)
            group_vrf = match_vrf.groupdict()
            vrf = group_vrf["vrf"]
        except AttributeError:
            vrf = None

    else:
        # IPv6's not been configured on this interface yet.
        interface['addresses'] = []

    interface['interface'] = interface_name
    interface['type'] = get_interface_type(interface_name)
    interface['vrf'] = vrf

    return interface, address_list


def get_ip_interface(interface_name, version, module):
    body = send_show_command(interface_name, version, module)

    # nxapi default response doesn't reflect the actual interface state
    # when dealing with IPv6. That's why we need to get raw output instead
    # and manually parse it.
    if module.params['transport'] == 'nxapi' and version == 'v6':
        interface, address_list = parse_unstructured_data(
                                        body, interface_name, module)
    else:
        interface, address_list = parse_structured_data(
                                        body, interface_name, version, module)

    return interface, address_list


def get_remove_ip_config_commands(interface, addr, mask, version):
    commands = []
    commands.append('interface {0}'.format(interface))
    if version == 'v4':
        commands.append('no ip address')
    else:
        commands.append('no ipv6 address {0}/{1}'.format(addr, mask))

    return commands


def get_config_ip_commands(delta, interface, existing, version):
    commands = []
    delta = dict(delta)

    # loop used in the situation that just an IP address or just a
    # mask is changing, not both.
    for each in ['addr', 'mask']:
        if each not in delta.keys():
            delta[each] = existing[each]

    if version == 'v4':
        command = 'ip address {addr}/{mask}'.format(**delta)
    else:
        command = 'ipv6 address {addr}/{mask}'.format(**delta)
    commands.append(command)
    commands.insert(0, 'interface {0}'.format(interface))

    return commands


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def validate_params(addr, interface, mask, version, state, intf_type, module):
    if state == "present":
        if addr is None or mask is None:
            module.fail_json(msg="An IP address AND a mask must be provided "
                                 "when state=present.")
    elif state == "absent" and version == "v6":
        if addr is None or mask is None:
            module.fail_json(msg="IPv6 address and mask must be provided when "
                                 "state=absent.")

    if (intf_type != "ethernet" and module.params["transport"] == "cli"):
        if is_default(interface, module) == "DNE":
            module.fail_json(msg="That interface does not exist yet. Create "
                                 "it first.", interface=interface)
    if mask is not None:
        try:
            if (int(mask) < 1 or int(mask) > 32) and version == "v4":
                raise ValueError
            elif int(mask) < 1 or int(mask) > 128:
                raise ValueError
        except ValueError:
            module.fail_json(msg="Warning! 'mask' must be an integer between"
                                 " 1 and 32 when version v4 and up to 128 "
                                 "when version v6.", version=version,
                                 mask=mask)


def main():
    argument_spec = dict(
            interface=dict(required=True),
            addr=dict(required=False),
            version=dict(required=False, choices=['v4', 'v6'],
                         default='v4'),
            mask=dict(type='str', required=False),
            state=dict(required=False, default='present',
                       choices=['present', 'absent']),
            include_defaults=dict(default=True)
    )
    module = get_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    addr = module.params['addr']
    version = module.params['version']
    mask = module.params['mask']
    interface = module.params['interface'].lower()
    state = module.params['state']

    intf_type = get_interface_type(interface)
    validate_params(addr, interface, mask, version, state, intf_type, module)

    mode = get_interface_mode(interface, intf_type, module)
    if mode == 'layer2':
        module.fail_json(msg='That interface is a layer2 port.\nMake it '
                             'a layer 3 port first.', interface=interface)

    existing, address_list = get_ip_interface(interface, version, module)

    args = dict(addr=addr, mask=mask, interface=interface)
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)
    commands = []
    changed = False
    end_state = existing

    if state == 'absent' and existing['addresses']:
        if version == 'v6':
            for address in existing['addresses']:
                if address['addr'] == addr and address['mask'] == mask:
                    command = get_remove_ip_config_commands(interface, addr,
                                                            mask, version)
                    commands.append(command)

        else:
            command = get_remove_ip_config_commands(interface, addr,
                                                    mask, version)
            commands.append(command)

    elif state == 'present':
        if not existing['addresses']:
            command = get_config_ip_commands(proposed, interface,
                                             existing, version)
            commands.append(command)
        else:
            prefix = "{0}/{1}".format(addr, mask)
            if prefix not in address_list:
                command = get_config_ip_commands(proposed, interface,
                                                 existing, version)
                commands.append(command)
            else:
                for address in existing['addresses']:
                    if (address['addr'] == addr and
                            int(address['mask']) != int(mask)):
                        command = get_config_ip_commands(proposed, interface,
                                                         existing, version)
                        commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            execute_config_command(cmds, module)
            changed = True
            end_state, address_list = get_ip_interface(interface, version,
                                                       module)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['updates'] = cmds
    results['changed'] = changed

    module.exit_json(**results)


if __name__ == '__main__':
    main()
