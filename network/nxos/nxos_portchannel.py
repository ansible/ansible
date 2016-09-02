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

module: nxos_portchannel
version_added: "2.2"
short_description: Manages port-channel interfaces
description:
    - Manages port-channel specific configuration parameters
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - Absent removes the portchannel config and interface if it
      already exists. If members to be removed are not explicitly
      passed, all existing members (if any), are removed.
    - Members must be a list
    - LACP needs to be enabled first if active/passive modes are used
options:
    group:
        description:
            - channel-group number for the port-channel
        required: true
    mode:
        description:
            - Mode for the port-channel, i.e. on, active, passive
        required: false
        default: on
        choices: ['active','passive','on']
    min_links:
        description:
            - min links required to keep portchannel up
        required: false
        default: null
    members:
        description:
            - List of interfaces that will be managed in a given portchannel
        required: false
        default: null
    force:
        description:
            - When true it forces port-channel members to match what is
              declared in the members param. This can be used to remove
              members.
        required: false
        choices: ['true', 'false']
        default: false
    state:
        description:
            - Manage the state of the resource
        required: false
        default: present
        choices: ['present','absent']
'''
EXAMPLES = '''
# Ensure port-channel99 is created, add two members, and set to mode on
- nxos_portchannel:
    group: 99
    members: ['Ethernet1/1','Ethernet1/2']
    mode: 'active'
    state: present
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"group": "12", "members": ["Ethernet2/5",
            "Ethernet2/6"], "mode": "on"}
existing:
    description:
        - k/v pairs of existing portchannel
    type: dict
    sample: {"group": "12", "members": ["Ethernet2/5",
            "Ethernet2/6"], "members_detail": {
            "Ethernet2/5": {"mode": "active", "status": "D"},
            "Ethernet2/6": {"mode": "active", "status": "D"}},
            "min_links": null, "mode": "active"}
end_state:
    description: k/v pairs of portchannel info after module execution
    returned: always
    type: dict
    sample: {"group": "12", "members": ["Ethernet2/5",
            "Ethernet2/6"], "members_detail": {
            "Ethernet2/5": {"mode": "on", "status": "D"},
            "Ethernet2/6": {"mode": "on", "status": "D"}},
            "min_links": null, "mode": "on"}
commands:
    description: command string sent to the device
    returned: always
    type: string
    sample: "interface Ethernet2/6 ; no channel-group 12 ;
            interface Ethernet2/5 ; no channel-group 12 ;
            interface Ethernet2/6 ; channel-group 12 mode on ;
            interface Ethernet2/5 ; channel-group 12 mode on ;"
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

WARNINGS = []
PARAM_TO_COMMAND_KEYMAP = {
    'min_links': 'lacp min-links'
}


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def get_value(arg, config, module):
    REGEX = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
    value = ''
    if PARAM_TO_COMMAND_KEYMAP[arg] in config:
        value = REGEX.search(config).group('value')
    return value


def check_interface(module, netcfg):
    config = str(netcfg)
    REGEX = re.compile(r'\s+interface port-channel{0}*$'.format(module.params['group']), re.M)
    value = False
    try:
        if REGEX.search(config):
            value = True
    except TypeError:
        value = False

    return value


def get_custom_value(arg, config, module):
    REGEX = re.compile(r'\s+member vni {0} associate-vrf\s*$'.format(
                                                module.params['vni']), re.M)
    value = False
    try:
        if REGEX.search(config):
            value = True
    except TypeError:
        value = False
    return value


def execute_config_command(commands, module):
    try:
        output = module.configure(commands)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending CLI commands',
                         error=str(clie), commands=commands)
    return output


def get_cli_body_ssh(command, response, module):
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
        if 'show port-channel summary' in command:
            command += ' | json'
        cmds = [command]
        response = execute_show(cmds, module)
        body = get_cli_body_ssh(command, response, module)
    elif module.params['transport'] == 'nxapi':
        cmds = [command]
        body = execute_show(cmds, module, command_type=command_type)

    return body


def get_portchannel_members(pchannel):
    try:
        members = pchannel['TABLE_member']['ROW_member']
    except KeyError:
        members = []

    return members


def get_portchannel_mode(interface, protocol, module, netcfg):
    if protocol != 'LACP':
        mode = 'on'
    else:
        netcfg = custom_get_config(module)
        parents = ['interface {0}'.format(interface.capitalize())]
        body = netcfg.get_section(parents)

        mode_list = body.split('\n')

        for line in mode_list:
            this_line = line.strip()
            if this_line.startswith('channel-group'):
                find = this_line
        if 'mode' in find:
            if 'passive' in find:
                mode = 'passive'
            elif 'active' in find:
                mode = 'active'

    return mode


def get_portchannel(module, netcfg=None):
    command = 'show port-channel summary'
    portchannel = {}
    portchannel_table = {}
    members = []

    body = execute_show_command(command, module)

    try:
        pc_table = body[0]['TABLE_channel']['ROW_channel']

        if isinstance(pc_table, dict):
            pc_table = [pc_table]

        for pc in pc_table:
            if pc['group'] == module.params['group']:
                portchannel_table = pc
    except (KeyError, AttributeError, TypeError, IndexError):
        return {}

    if portchannel_table:
        portchannel['group'] = portchannel_table['group']
        protocol = portchannel_table['prtcl']
        members_list = get_portchannel_members(portchannel_table)

        if isinstance(members_list, dict):
            members_list = [members_list]

        member_dictionary = {}
        for each_member in members_list:
            interface = each_member['port']
            members.append(interface)

            pc_member = {}
            pc_member['status'] = str(each_member['port-status'])
            pc_member['mode'] = get_portchannel_mode(interface,
                                                     protocol, module, netcfg)

            member_dictionary[interface] = pc_member
            portchannel['members'] = members
            portchannel['members_detail'] = member_dictionary

        # Ensure each member have the same mode.
        modes = set()
        for each, value in member_dictionary.iteritems():
            modes.update([value['mode']])
        if len(modes) == 1:
            portchannel['mode'] = value['mode']
        else:
            portchannel['mode'] = 'unknown'
    return portchannel


def get_existing(module, args):
    existing = {}
    netcfg = custom_get_config(module)

    interface_exist = check_interface(module, netcfg)
    if interface_exist:
        parents = ['interface port-channel{0}'.format(module.params['group'])]
        config = netcfg.get_section(parents)

        if config:
            existing['min_links'] = get_value('min_links', config, module)
            existing.update(get_portchannel(module, netcfg=netcfg))

    return existing, interface_exist


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


def config_portchannel(proposed, mode, group):
    commands = []
    config_args = {
        'mode': 'channel-group {group} mode {mode}',
        'min_links': 'lacp min-links {min_links}',
    }

    for member in proposed.get('members', []):
        commands.append('interface {0}'.format(member))
        commands.append(config_args.get('mode').format(group=group, mode=mode))

    min_links = proposed.get('min_links', None)
    if min_links:
        command = 'interface port-channel {0}'.format(group)
        commands.append(command)
        commands.append(config_args.get('min_links').format(
                                                    min_links=min_links))

    return commands


def get_commands_to_add_members(proposed, existing, module):
    try:
        proposed_members = proposed['members']
    except KeyError:
        proposed_members = []

    try:
        existing_members = existing['members']
    except KeyError:
        existing_members = []

    members_to_add = list(set(proposed_members).difference(existing_members))

    commands = []
    if members_to_add:
        for member in members_to_add:
            commands.append('interface {0}'.format(member))
            commands.append('channel-group {0} mode {1}'.format(
                existing['group'], proposed['mode']))

    return commands


def get_commands_to_remove_members(proposed, existing, module):
    try:
        proposed_members = proposed['members']
    except KeyError:
        proposed_members = []

    try:
        existing_members = existing['members']
    except KeyError:
        existing_members = []

    members_to_remove = list(set(existing_members).difference(proposed_members))
    commands = []
    if members_to_remove:
        for member in members_to_remove:
            commands.append('interface {0}'.format(member))
            commands.append('no channel-group {0}'.format(existing['group']))

    return commands


def get_commands_if_mode_change(proposed, existing, group, mode, module):
    try:
        proposed_members = proposed['members']
    except KeyError:
        proposed_members = []

    try:
        existing_members = existing['members']
    except KeyError:
        existing_members = []

    try:
        members_dict = existing['members_detail']
    except KeyError:
        members_dict = {}

    members_to_remove = set(existing_members).difference(proposed_members)
    members_with_mode_change = []
    if members_dict:
        for interface, values in members_dict.iteritems():
            if (interface in proposed_members and
                    (interface not in members_to_remove)):
                if values['mode'] != mode:
                    members_with_mode_change.append(interface)

    commands = []
    if members_with_mode_change:
        for member in members_with_mode_change:
            commands.append('interface {0}'.format(member))
            commands.append('no channel-group {0}'.format(group))

        for member in members_with_mode_change:
            commands.append('interface {0}'.format(member))
            commands.append('channel-group {0} mode {1}'.format(group, mode))

    return commands


def get_commands_min_links(existing, proposed, group, min_links, module):
    commands = []
    try:
        if (existing['min_links'] is None or
                (existing['min_links'] != proposed['min_links'])):
            commands.append('interface port-channel{0}'.format(group))
            commands.append('lacp min-link {0}'.format(min_links))
    except KeyError:
        commands.append('interface port-channel{0}'.format(group))
        commands.append('lacp min-link {0}'.format(min_links))
    return commands


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def main():
    argument_spec = dict(
            group=dict(required=True, type='str'),
            mode=dict(required=False, choices=['on', 'active', 'passive'],
                      default='on', type='str'),
            min_links=dict(required=False, default=None, type='str'),
            members=dict(required=False, default=None, type='list'),
            force=dict(required=False, default='false', type='str',
                       choices=['true', 'false']),
            state=dict(required=False, choices=['absent', 'present'],
                       default='present'),
            include_defaults=dict(default=False)
    )
    argument_spec.update(nxos_argument_spec)
    module = get_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    group = str(module.params['group'])
    mode = module.params['mode']
    min_links = module.params['min_links']
    members = module.params['members']
    state = module.params['state']

    if str(module.params['force']).lower() == 'true':
        force = True
    elif module.params['force'] == 'false':
        force = False

    if ((min_links or mode) and
            (not members and state == 'present')):
        module.fail_json(msg='"members" is required when state=present and '
                             '"min_links" or "mode" are provided')

    changed = False
    args =  [
            'group',
            'members',
            'min_links',
            'mode'
        ]

    existing, interface_exist = invoke('get_existing', module, args)
    end_state = existing
    proposed = dict((k, v) for k, v in module.params.iteritems()
                    if v is not None and k in args)

    result = {}
    commands = []
    if state == 'absent':
        if existing:
            commands.append(['no interface port-channel{0}'.format(group)])
    elif state == 'present':
        if not interface_exist:
            command = config_portchannel(proposed, mode, group)
            commands.append(command)
            commands.insert(0, 'interface port-channel{0}'.format(group))
            WARNINGS.append("The proposed port-channel interface did not "
                            "exist. It's recommended to use nxos_interface to "
                            "create all logical interfaces.")

        elif existing and interface_exist:
            if force:
                command = get_commands_to_remove_members(proposed, existing, module)
                commands.append(command)

            command = get_commands_to_add_members(proposed, existing, module)
            commands.append(command)

            mode_command = get_commands_if_mode_change(proposed, existing,
                                                       group, mode, module)

            commands.insert(0, mode_command)

            if min_links:
                command = get_commands_min_links(existing, proposed,
                                                 group, min_links, module)
                commands.append(command)

    cmds = flatten_list(commands)
    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            output = execute_config_command(cmds, module)
            changed = True
            end_state, interface_exist = get_existing(module, args)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['state'] = state
    results['updates'] = cmds
    results['changed'] = changed

    if WARNINGS:
        results['warnings'] = WARNINGS

    module.exit_json(**results)


if __name__ == '__main__':
    main()
