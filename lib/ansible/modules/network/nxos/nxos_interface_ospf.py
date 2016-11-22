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
module: nxos_interface_ospf
version_added: "2.2"
short_description: Manages configuration of an OSPF interface instance.
description:
    - Manages configuration of an OSPF interface instance.
author: Gabriele Gerbino (@GGabriele)
extends_documentation_fragment: nxos
notes:
    - default, where supported, restores params default value
    - To remove an existing authentication configuration you should use
      message_digest_key_id=default plus all other options matching their
      existing values.
    - State absent remove the whole OSPF interface configuration
options:
    interface:
        description:
            - Name of this cisco_interface resource. Valid value is a string.
        required: true
    ospf:
        description:
            - Name of the ospf instance.
        required: true
    area:
        description:
            - Ospf area associated with this cisco_interface_ospf instance.
              Valid values are a string, formatted as an IP address
              (i.e. "0.0.0.0") or as an integer.
        required: true
    cost:
        description:
            - The cost associated with this cisco_interface_ospf instance.
        required: false
        default: null
    hello_interval:
        description:
            - Time between sending successive hello packets.
              Valid values are an integer or the keyword 'default'.
        required: false
        default: null
    dead_interval:
        description:
            - Time interval an ospf neighbor waits for a hello
              packet before tearing down adjacencies. Valid values are an
              integer or the keyword 'default'.
        required: false
        default: null
    passive_interface:
        description:
            - Setting to true will prevent this interface from receiving
              HELLO packets. Valid values are 'true' and 'false'.
        required: false
        choices: ['true','false']
        default: null
    message_digest:
        description:
            - Enables or disables the usage of message digest authentication.
              Valid values are 'true' and 'false'.
        required: false
        choices: ['true','false']
        default: null
    message_digest_key_id:
        description:
            - md5 authentication key-id associated with the ospf instance.
              If this is present, message_digest_encryption_type,
              message_digest_algorithm_type and message_digest_password are
              mandatory. Valid value is an integer and 'default'.
        required: false
        default: null
    message_digest_algorithm_type:
        description:
            - Algorithm used for authentication among neighboring routers
              within an area. Valid values is 'md5'.
        required: false
        choices: ['md5']
        default: null
    message_digest_encryption_type:
        description:
            - Specifies the scheme used for encrypting message_digest_password.
              Valid values are '3des' or 'cisco_type_7' encryption.
        required: false
        choices: ['cisco_type_7','3des']
        default: null
    message_digest_password:
        description:
            - Specifies the message_digest password. Valid value is a string.
        required: false
        default: null
    state:
        description:
            - Determines whether the config should be present or not on the device.
        required: false
        default: present
        choices: ['present','absent']
    m_facts:
        description:
            - Used to print module facts
        required: false
        default: false
        choices: ['true','false']
'''
EXAMPLES = '''
- nxos_interface_ospf:
    interface: ethernet1/32
    ospf: 1
    area: 1
    cost: default
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"area": "1", "interface": "ethernet1/32", "ospf": "1"}
existing:
    description: k/v pairs of existing OSPF configuration
    type: dict
    sample: {"area": "", "cost": "", "dead_interval": "",
            "hello_interval": "", "interface": "ethernet1/32",
            "message_digest": false, "message_digest_algorithm_type": "",
            "message_digest_encryption_type": "",
            "message_digest_key_id": "", "message_digest_password": "",
            "ospf": "", "passive_interface": false}
end_state:
    description: k/v pairs of OSPF configuration after module execution
    returned: always
    type: dict
    sample: {"area": "0.0.0.1", "cost": "", "dead_interval": "",
            "hello_interval": "", "interface": "ethernet1/32",
            "message_digest": false, "message_digest_algorithm_type": "",
            "message_digest_encryption_type": "", "message_digest_key_id": "",
            "message_digest_password": "", "ospf": "1",
            "passive_interface": false}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface Ethernet1/32", "ip router ospf 1 area 0.0.0.1"]
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

DEFAULT_COMMENT_TOKENS = ['#', '!']
import ansible.module_utils.nxos
from ansible.module_utils.basic import get_exception
from ansible.module_utils.netcfg import NetworkConfig, ConfigLine
from ansible.module_utils.network import NetworkModule
from ansible.module_utils.shell import ShellError


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

BOOL_PARAMS = [
    'passive_interface',
    'message_digest'
]
PARAM_TO_COMMAND_KEYMAP = {
    'cost': 'ip ospf cost',
    'ospf': 'ip router ospf',
    'area': 'ip router ospf',
    'hello_interval': 'ip ospf hello-interval',
    'dead_interval': 'ip ospf dead-interval',
    'passive_interface': 'ip ospf passive-interface',
    'message_digest': 'ip ospf authentication message-digest',
    'message_digest_key_id': 'ip ospf message-digest-key',
    'message_digest_algorithm_type': 'ip ospf message-digest-key options',
    'message_digest_encryption_type': 'ip ospf message-digest-key options',
    'message_digest_password': 'ip ospf message-digest-key options',
}
PARAM_TO_DEFAULT_KEYMAP = {
}


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def get_custom_value(arg, config, module):
    value = ''
    if arg == 'ospf':
        REGEX = re.compile(r'(?:ip router ospf\s)(?P<value>.*)$', re.M)
        value = ''
        if 'ip router ospf' in config:
            parsed = REGEX.search(config).group('value').split()
            value = parsed[0]

    elif arg == 'area':
        REGEX = re.compile(r'(?:ip router ospf\s)(?P<value>.*)$', re.M)
        value = ''
        if 'ip router ospf' in config:
            parsed = REGEX.search(config).group('value').split()
            value = parsed[2]

    elif arg.startswith('message_digest_'):
        REGEX = re.compile(r'(?:ip ospf message-digest-key\s)(?P<value>.*)$', re.M)
        value = ''
        if 'ip ospf message-digest-key' in config:
            value_list = REGEX.search(config).group('value').split()
            if arg == 'message_digest_key_id':
                value = value_list[0]
            elif arg == 'message_digest_algorithm_type':
                value = value_list[1]
            elif arg == 'message_digest_encryption_type':
                value = value_list[2]
                if value == '3':
                    value = '3des'
                elif value == '7':
                    value = 'cisco_type_7'
            elif arg == 'message_digest_password':
                value = value_list[3]

    elif arg == 'passive_interface':
        REGEX = re.compile(r'\s+{0}\s*$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        NO_REGEX = re.compile(r'\s+no\s+{0}\s*$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        value = False
        try:
            if NO_REGEX.search(config):
                value = False
            elif REGEX.search(config):
                value = True
        except TypeError:
            value = False

    return value


def get_value(arg, config, module):
    custom = [
        'ospf',
        'area',
        'message_digest_key_id',
        'message_digest_algorithm_type',
        'message_digest_encryption_type',
        'message_digest_password',
        'passive_interface'
    ]

    if arg in custom:
        value = get_custom_value(arg, config, module)
    elif arg in BOOL_PARAMS:
        REGEX = re.compile(r'\s+{0}\s*$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        value = False
        try:
            if REGEX.search(config):
                value = True
        except TypeError:
            value = False
    else:
        REGEX = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        value = ''
        if PARAM_TO_COMMAND_KEYMAP[arg] in config:
            value = REGEX.search(config).group('value')
    return value


def get_existing(module, args):
    existing = {}
    netcfg = custom_get_config(module)
    parents = ['interface {0}'.format(module.params['interface'].capitalize())]
    config = netcfg.get_section(parents)
    if 'ospf' in config:
        for arg in args:
            if arg not in ['interface']:
                existing[arg] = get_value(arg, config, module)
        existing['interface'] = module.params['interface']
    return existing


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
            value = table.get(key)
            if value:
                new_dict[new_key] = value
            else:
                new_dict[new_key] = value
    return new_dict


def get_default_commands(existing, proposed, existing_commands, key, module):
    commands = list()
    existing_value = existing_commands.get(key)
    if key.startswith('ip ospf message-digest-key'):
        check = False
        for param in ['message_digest_encryption_type',
                      'message_digest_algorithm_type',
                      'message_digest_password']:
            if existing[param] == proposed[param]:
                check = True
        if check:
            if existing['message_digest_encryption_type'] == '3des':
                encryption_type = '3'
            elif existing['message_digest_encryption_type'] == 'cisco_type_7':
                encryption_type = '7'
            command = 'no {0} {1} {2} {3} {4}'.format(
                        key,
                        existing['message_digest_key_id'],
                        existing['message_digest_algorithm_type'],
                        encryption_type,
                        existing['message_digest_password'])
            commands.append(command)
    else:
        commands.append('no {0} {1}'.format(key, existing_value))
    return commands


def get_custom_command(existing_cmd, proposed, key, module):
    commands = list()

    if key == 'ip router ospf':
        command = '{0} {1} area {2}'.format(key, proposed['ospf'],
                                            proposed['area'])
        if command not in existing_cmd:
            commands.append(command)

    elif key.startswith('ip ospf message-digest-key'):
        if (proposed['message_digest_key_id'] != 'default' and
            'options' not in key):
            if proposed['message_digest_encryption_type'] == '3des':
                encryption_type = '3'
            elif proposed['message_digest_encryption_type'] == 'cisco_type_7':
                encryption_type = '7'
            command = '{0} {1} {2} {3} {4}'.format(
                                key,
                                proposed['message_digest_key_id'],
                                proposed['message_digest_algorithm_type'],
                                encryption_type,
                                proposed['message_digest_password'])
            commands.append(command)
    return commands


def state_present(module, existing, proposed, candidate):
    commands = list()
    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, proposed)
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)

    for key, value in proposed_commands.iteritems():
        if value is True:
            commands.append(key)
        elif value is False:
            commands.append('no {0}'.format(key))
        elif value == 'default':
            if existing_commands.get(key):
                commands.extend(get_default_commands(existing, proposed,
                                                     existing_commands, key,
                                                     module))
        else:
            if (key == 'ip router ospf' or
                    key.startswith('ip ospf message-digest-key')):
                commands.extend(get_custom_command(commands, proposed,
                                                   key, module))
            else:
                command = '{0} {1}'.format(key, value.lower())
                commands.append(command)

    if commands:
        parents = ['interface {0}'.format(module.params['interface'].capitalize())]
        candidate.add(commands, parents=parents)


def state_absent(module, existing, proposed, candidate):
    commands = []
    parents = ['interface {0}'.format(module.params['interface'].capitalize())]
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)

    for key, value in existing_commands.iteritems():
        if value:
            if key.startswith('ip ospf message-digest-key'):
                if 'options' not in key:
                    if existing['message_digest_encryption_type'] == '3des':
                        encryption_type = '3'
                    elif existing['message_digest_encryption_type'] == 'cisco_type_7':
                        encryption_type = '7'
                    command = 'no {0} {1} {2} {3} {4}'.format(
                                        key,
                                        existing['message_digest_key_id'],
                                        existing['message_digest_algorithm_type'],
                                        encryption_type,
                                        existing['message_digest_password'])
                    commands.append(command)
            elif key in ['ip ospf authentication message-digest',
                         'ip ospf passive-interface']:
                if value:
                    commands.append('no {0}'.format(key))
            elif key == 'ip router ospf':
                command = 'no {0} {1} area {2}'.format(key, proposed['ospf'],
                                                    proposed['area'])
                if command not in commands:
                    commands.append(command)
            else:
                existing_value = existing_commands.get(key)
                commands.append('no {0} {1}'.format(key, existing_value))

    candidate.add(commands, parents=parents)


def normalize_area(area, module):
    try:
        area = int(area)
        area = '0.0.0.{0}'.format(area)
    except ValueError:
        splitted_area = area.split('.')
        if len(splitted_area) != 4:
            module.fail_json(msg='Incorrect Area ID format', area=area)
    return area


def main():
    argument_spec = dict(
            interface=dict(required=True, type='str'),
            ospf=dict(required=True, type='str'),
            area=dict(required=True, type='str'),
            cost=dict(required=False, type='str'),
            hello_interval=dict(required=False, type='str'),
            dead_interval=dict(required=False, type='str'),
            passive_interface=dict(required=False, type='bool'),
            message_digest=dict(required=False, type='bool'),
            message_digest_key_id=dict(required=False, type='str'),
            message_digest_algorithm_type=dict(required=False, type='str',
                                               choices=['md5']),
            message_digest_encryption_type=dict(required=False, type='str',
                                                choices=['cisco_type_7','3des']),
            message_digest_password=dict(required=False, type='str'),
            m_facts=dict(required=False, default=False, type='bool'),
            state=dict(choices=['present', 'absent'], default='present',
                       required=False),
            include_defaults=dict(default=True)
    )
    argument_spec.update(nxos_argument_spec)
    module = get_module(argument_spec=argument_spec,
                        required_together=[['message_digest_key_id',
                                            'message_digest_algorithm_type',
                                            'message_digest_encryption_type',
                                            'message_digest_password']],
                        supports_check_mode=True)

    for param in ['message_digest_encryption_type',
                  'message_digest_algorithm_type',
                  'message_digest_password']:
        if module.params[param] == 'default':
            module.exit_json(msg='Use message_digest_key_id=default to remove'
                                 ' an existing authentication configuration')

    state = module.params['state']
    args =  [
            'interface',
            'ospf',
            'area',
            'cost',
            'hello_interval',
            'dead_interval',
            'passive_interface',
            'message_digest',
            'message_digest_key_id',
            'message_digest_algorithm_type',
            'message_digest_encryption_type',
            'message_digest_password'
        ]

    existing = invoke('get_existing', module, args)
    end_state = existing
    proposed_args = dict((k, v) for k, v in module.params.iteritems()
                    if v is not None and k in args)

    proposed = {}
    for key, value in proposed_args.iteritems():
        if key != 'interface':
            if str(value).lower() == 'true':
                value = True
            elif str(value).lower() == 'false':
                value = False
            elif str(value).lower() == 'default':
                value = PARAM_TO_DEFAULT_KEYMAP.get(key)
                if value is None:
                    value = 'default'
            if existing.get(key) or (not existing.get(key) and value):
                proposed[key] = value

    proposed['area'] = normalize_area(proposed['area'], module)
    result = {}
    if (state == 'present' or (state == 'absent' and
        existing.get('ospf') == proposed['ospf'] and
        existing.get('area') == proposed['area'])):

        candidate = CustomNetworkConfig(indent=3)
        invoke('state_%s' % state, module, existing, proposed, candidate)

        try:
            response = load_config(module, candidate)
            result.update(response)
        except ShellError:
            exc = get_exception()
            module.fail_json(msg=str(exc))
    else:
        result['updates'] = []

    result['connected'] = module.connected
    if module.params['m_facts']:
        end_state = invoke('get_existing', module, args)
        result['end_state'] = end_state
        result['existing'] = existing
        result['proposed'] = proposed_args

    module.exit_json(**result)


if __name__ == '__main__':
    main()
