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
module: nxos_bgp_neighbor_af
version_added: "2.2"
short_description: Manages BGP address-family's neighbors configuration
description:
    - Manages BGP address-family's neighbors configurations on NX-OS switches
author: Gabriele Gerbino (@GGabriele)
extends_documentation_fragment: nxos
notes:
    - State 'absent' removes the whole BGP address-family's
      neighbor configuration
    - default, when supported, removes properties
    - to defaults maximum-prefix configuration, only
      max_prefix_limit=default is needed
options:
    asn:
        description:
            - BGP autonomous system number. Valid values are String,
              Integer in ASPLAIN or ASDOT notation.
        required: true
    vrf:
        description:
            - Name of the VRF. The name 'default' is a valid VRF representing
              the global bgp.
        required: false
        default: default
    neighbor:
        description:
            - Neighbor Identifier. Valid values are string. Neighbors may use
              IPv4 or IPv6 notation, with or without prefix length.
        required: true
    afi:
        description:
            - Address Family Identifie.
        required: true
        choices: ['ipv4','ipv6', 'vpnv4', 'vpnv6', 'l2vpn']
    safi:
        description:
            - Sub Address Family Identifier.
        required: true
        choices: ['unicast','multicast', 'evpn']
    additional_paths_receive:
        description:
            - Valid values are enable for basic command enablement; disable
              for disabling the command at the neighbor_af level
              (it adds the disable keyword to the basic command); and inherit
              to remove the command at this level (the command value is
              inherited from a higher BGP layer).
        required: false
        choices: ['enable','disable', 'inherit']
        default: null
    additional_paths_send:
        description:
            - Valid values are enable for basic command enablement; disable
              for disabling the command at the neighbor_af level
              (it adds the disable keyword to the basic command); and inherit
              to remove the command at this level (the command value is
              inherited from a higher BGP layer).
        required: false
        choices: ['enable','disable', 'inherit']
        default: null
    advertise_map_exist:
        description:
            - Conditional route advertisement. This property requires two
              route maps: an advertise-map and an exist-map. Valid values are
              an array specifying both the advertise-map name and the exist-map
              name, or simply 'default' e.g. ['my_advertise_map',
              'my_exist_map']. This command is mutually exclusive with the
              advertise_map_non_exist property.
        required: false
        default: null
    advertise_map_non_exist:
        description:
            - Conditional route advertisement. This property requires two
              route maps: an advertise-map and an exist-map. Valid values are
              an array specifying both the advertise-map name and the
              non-exist-map name, or simply 'default' e.g.
              ['my_advertise_map', 'my_non_exist_map']. This command is mutually
              exclusive with the advertise_map_exist property.
        required: false
        default: null
    allowas_in:
        description:
            - Activate allowas-in property
        required: false
        default: null
    allowas_in_max:
        description:
            - Optional max-occurrences value for allowas_in. Valid values are
              an integer value or 'default'. Can be used independently or in
              conjunction with allowas_in.
        required: false
        default: null
    as_override:
        description:
            - Activate the as-override feature.
        required: false
        choices: ['true', 'false']
        default: null
    default_originate:
        description:
            - Activate the default-originate feature.
        required: false
        choices: ['true', 'false']
        default: null
    default_originate_route_map:
        description:
            - Optional route-map for the default_originate property. Can be
              used independently or in conjunction with default_originate.
              Valid values are a string defining a route-map name,
              or 'default'.
        required: false
        default: null
    filter_list_in:
        description:
            - Valid values are a string defining a filter-list name,
              or 'default'.
        required: false
        default: null
    filter_list_out:
        description:
            - Valid values are a string defining a filter-list name,
              or 'default'.
        required: false
        default: null
    max_prefix_limit:
        description:
            - maximum-prefix limit value. Valid values are an integer value
              or 'default'.
        required: false
        default: null
    max_prefix_interval:
        description:
            - Optional restart interval. Valid values are an integer.
              Requires max_prefix_limit.
        required: false
        default: null
    max_prefix_threshold:
        description:
            - Optional threshold percentage at which to generate a warning.
              Valid values are an integer value.
              Requires max_prefix_limit.
        required: false
        default: null
    max_prefix_warning:
        description:
            - Optional warning-only keyword. Requires max_prefix_limit.
        required: false
        choices: ['true','false']
        default: null
    next_hop_self:
        description:
            - Activate the next-hop-self feature.
        required: false
        choices: ['true','false']
        default: null
    next_hop_third_party:
        description:
            - Activate the next-hop-third-party feature.
        required: false
        choices: ['true','false']
        default: null
    prefix_list_in:
        description:
            - Valid values are a string defining a prefix-list name,
              or 'default'.
        required: false
        default: null
    prefix_list_out:
        description:
            - Valid values are a string defining a prefix-list name,
              or 'default'.
        required: false
        default: null
    route_map_in:
        description:
            - Valid values are a string defining a route-map name,
              or 'default'.
        required: false
        default: null
    route_map_out:
        description:
            - Valid values are a string defining a route-map name,
              or 'default'.
        required: false
        default: null
    route_reflector_client:
        description:
            - Router reflector client.
        required: false
        choices: ['true','false']
        default: null
    send_community:
        description:
            - send-community attribute.
        required: false
        choices: ['none', 'both', 'extended', 'standard', 'default']
        default: null
    soft_reconfiguration_in:
        description:
            - Valid values are 'enable' for basic command enablement; 'always'
              to add the always keyword to the basic command; and 'inherit' to
              remove the command at this level (the command value is inherited
              from a higher BGP layer).
        required: false
        choices: ['enable','always','inherit']
        default: null
    soo:
        description:
            - Site-of-origin. Valid values are a string defining a VPN
              extcommunity or 'default'.
        required: false
        default: null
    suppress_inactive:
        description:
            - suppress-inactive feature.
        required: false
        choices: ['true','false','default']
        default: null
    unsuppress_map:
        description:
            - unsuppress-map. Valid values are a string defining a route-map
              name or 'default'.
        required: false
        default: null
    weight:
        description:
            - weight value. Valid values are an integer value or 'default'.
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
configure RR client
- nxos_bgp_neighbor_af:
    asn: 65535
    neighbor: '3.3.3.3'
    afi: ipv4
    safi: unicast
    route_reflector_client: true
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
    sample: {"afi": "ipv4", "asn": "65535",
            "neighbor": "3.3.3.3", "route_reflector_client": true,
            "safi": "unicast", "vrf": "default"}
existing:
    description: k/v pairs of existing configuration
    type: dict
    sample: {}
end_state:
    description: k/v pairs of configuration after module execution
    returned: always
    type: dict
    sample: {"additional_paths_receive": "inherit",
            "additional_paths_send": "inherit",
            "advertise_map_exist": [], "advertise_map_non_exist": [],
            "afi": "ipv4", "allowas_in": false,
            "allowas_in_max": "", "as_override": false,
            "asn": "65535", "default_originate": false,
            "default_originate_route_map": "", "filter_list_in": "",
            "filter_list_out": "", "max_prefix_interval": "",
            "max_prefix_limit": "", "max_prefix_threshold": "",
            "max_prefix_warning": "", "neighbor": "3.3.3.3",
            "next_hop_self": false, "next_hop_third_party": true,
            "prefix_list_in": "", "prefix_list_out": "",
            "route_map_in": "", "route_map_out": "",
            "route_reflector_client": true, "safi": "unicast",
            "send_community": "",
            "soft_reconfiguration_in": "inherit", "soo": "",
            "suppress_inactive": false, "unsuppress_map": "",
            "vrf": "default", "weight": ""}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["router bgp 65535", "neighbor 3.3.3.3",
            "address-family ipv4 unicast", "route-reflector-client"]
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
BOOL_PARAMS = [
    'allowas_in',
    'as_override',
    'default_originate',
    'next_hop_self',
    'next_hop_third_party',
    'route_reflector_client',
    'suppress_inactive'
]
PARAM_TO_COMMAND_KEYMAP = {
    'afi': 'address-family',
    'asn': 'router bgp',
    'neighbor': 'neighbor',
    'additional_paths_receive': 'capability additional-paths receive',
    'additional_paths_send': 'capability additional-paths send',
    'advertise_map_exist': 'advertise-map exist',
    'advertise_map_non_exist': 'advertise-map non-exist',
    'allowas_in': 'allowas-in',
    'allowas_in_max': 'allowas-in max',
    'as_override': 'as-override',
    'default_originate': 'default-originate',
    'default_originate_route_map': 'default-originate route-map',
    'filter_list_in': 'filter-list in',
    'filter_list_out': 'filter-list out',
    'max_prefix_limit': 'maximum-prefix',
    'max_prefix_interval': 'maximum-prefix options',
    'max_prefix_threshold': 'maximum-prefix options',
    'max_prefix_warning': 'maximum-prefix options',
    'next_hop_self': 'next-hop-self',
    'next_hop_third_party': 'next-hop-third-party',
    'prefix_list_in': 'prefix-list in',
    'prefix_list_out': 'prefix-list out',
    'route_map_in': 'route-map in',
    'route_map_out': 'route-map out',
    'route_reflector_client': 'route-reflector-client',
    'safi': 'address-family',
    'send_community': 'send-community',
    'soft_reconfiguration_in': 'soft-reconfiguration inbound',
    'soo': 'soo',
    'suppress_inactive': 'suppress-inactive',
    'unsuppress_map': 'unsuppress-map',
    'weight': 'weight',
    'vrf': 'vrf'
}
PARAM_TO_DEFAULT_KEYMAP = {}


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def get_value(arg, config, module):
    if arg in BOOL_PARAMS:
        REGEX = re.compile(r'\s+{0}\s*'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
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


def in_out_param(arg, config, module):
    value = ''
    for line in config:
        if PARAM_TO_COMMAND_KEYMAP[arg].split()[0] in line:
            splitted_line = line.split()
            if splitted_line[-1] == PARAM_TO_COMMAND_KEYMAP[arg].split()[1]:
                value = splitted_line[1]
    return value


def get_custom_value(arg, config, module):
    splitted_config = config.splitlines()
    value = ''

    if (arg.startswith('filter_list') or arg.startswith('prefix_list') or
        arg.startswith('route_map')):
        value = in_out_param(arg, splitted_config, module)
    elif arg == 'send_community':
        for line in splitted_config:
            if PARAM_TO_COMMAND_KEYMAP[arg] in line:
                splitted_line = line.split()
                if len(splitted_line) == 1:
                    value = 'none'
                else:
                    value = splitted_line[1]
    elif arg == 'additional_paths_receive':
        value = 'inherit'
        for line in splitted_config:
            if PARAM_TO_COMMAND_KEYMAP[arg] in line:
                if 'disable' in line:
                    value = 'disable'
                else:
                    value = 'enable'
    elif arg == 'additional_paths_send':
        value = 'inherit'
        for line in splitted_config:
            if PARAM_TO_COMMAND_KEYMAP[arg] in line:
                if 'disable' in line:
                    value = 'disable'
                else:
                    value = 'enable'
    elif arg == 'advertise_map_exist':
        value = []
        for line in splitted_config:
            if 'advertise-map' in line and 'exist-map' in line:
                splitted_line = line.split()
                value = [splitted_line[1], splitted_line[3]]
    elif arg == 'advertise_map_non_exist':
        value = []
        for line in splitted_config:
            if 'advertise-map' in line and 'non-exist-map' in line:
                splitted_line = line.split()
                value = [splitted_line[1], splitted_line[3]]
    elif arg == 'allowas_in_max':
        for line in splitted_config:
            if 'allowas-in' in line:
                splitted_line = line.split()
                if len(splitted_line) == 2:
                    value = splitted_line[-1]
    elif arg.startswith('max_prefix'):
        for line in splitted_config:
            if 'maximum-prefix' in line:
                splitted_line = line.split()
                if arg == 'max_prefix_limit':
                    value = splitted_line[1]
                elif arg == 'max_prefix_interval' and 'restart' in line:
                    value = splitted_line[-1]
                elif arg == 'max_prefix_threshold' and len(splitted_line) > 2:
                    try:
                        int(splitted_line[2])
                        value = splitted_line[2]
                    except ValueError:
                        value = ''
                elif arg == 'max_prefix_warning':
                    if 'warning-only' in line:
                        value = True
                    else:
                        value = False
    elif arg == 'soft_reconfiguration_in':
        value = 'inherit'
        for line in splitted_config:
            if PARAM_TO_COMMAND_KEYMAP[arg] in line:
                if 'always' in line:
                    value = 'always'
                else:
                    value = 'enable'
    elif arg == 'next_hop_third_party':
        PRESENT_REGEX = re.compile(r'\s+{0}\s*'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        ABSENT_REGEX = re.compile(r'\s+no\s+{0}\s*'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        value = False
        try:
            if ABSENT_REGEX.search(config):
                value = False
            elif PRESENT_REGEX.search(config):
                value = True
        except TypeError:
            value = False

    return value


def get_existing(module, args):
    existing = {}
    netcfg = custom_get_config(module)

    custom = [
        'allowas_in_max',
        'send_community',
        'additional_paths_send',
        'additional_paths_receive',
        'advertise_map_exist',
        'advertise_map_non_exist',
        'filter_list_in',
        'filter_list_out',
        'max_prefix_limit',
        'max_prefix_interval',
        'max_prefix_threshold',
        'max_prefix_warning',
        'next_hop_third_party',
        'prefix_list_in',
        'prefix_list_out',
        'route_map_in',
        'route_map_out',
        'soft_reconfiguration_in'
    ]
    try:
        asn_regex = '.*router\sbgp\s(?P<existing_asn>\d+).*'
        match_asn = re.match(asn_regex, str(netcfg), re.DOTALL)
        existing_asn_group = match_asn.groupdict()
        existing_asn = existing_asn_group['existing_asn']
    except AttributeError:
        existing_asn = ''

    if existing_asn:
        parents = ["router bgp {0}".format(existing_asn)]
        if module.params['vrf'] != 'default':
            parents.append('vrf {0}'.format(module.params['vrf']))

        parents.append('neighbor {0}'.format(module.params['neighbor']))
        parents.append('address-family {0} {1}'.format(
                            module.params['afi'], module.params['safi']))
        config = netcfg.get_section(parents)

        if config:
            for arg in args:
                if arg not in ['asn', 'vrf', 'neighbor', 'afi', 'safi']:
                    if arg in custom:
                        existing[arg] = get_custom_value(arg, config, module)
                    else:
                        existing[arg] = get_value(arg, config, module)

            existing['asn'] = existing_asn
            existing['neighbor'] = module.params['neighbor']
            existing['vrf'] = module.params['vrf']
            existing['afi'] = module.params['afi']
            existing['safi'] = module.params['safi']
    else:
        WARNINGS.append("The BGP process didn't exist but the task"
                        " just created it.")

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


def get_address_family_command(key, value, module):
    command = "address-family {0} {1}".format(
                    module.params['afi'], module.params['safi'])
    return command


def get_capability_additional_paths_receive_command(key, value, module):
    command = ''
    if value == 'enable':
        command = key
    elif value == 'disable':
        command = '{0} {1}'.format(key, value)
    return command


def get_capability_additional_paths_send_command(key, value, module):
    command = ''
    if value == 'enable':
        command = key
    elif value == 'disable':
        command = '{0} {1}'.format(key, value)
    return command


def get_advertise_map_exist_command(key, value, module):
    command = 'advertise-map {0} exist-map {1}'.format(
                                                value[0], value[1])
    return command


def get_advertise_map_non_exist_command(key, value, module):
    command = 'advertise-map {0} non-exist-map {1}'.format(
                                                value[0], value[1])
    return command


def get_allowas_in_max_command(key, value, module):
    command = 'allowas-in {0}'.format(value)
    return command


def get_filter_list_in_command(key, value, module):
    command = 'filter-list {0} in'.format(value)
    return command


def get_filter_list_out_command(key, value, module):
    command = 'filter-list {0} out'.format(value)
    return command


def get_prefix_list_in_command(key, value, module):
    command = 'prefix-list {0} in'.format(value)
    return command


def get_prefix_list_out_command(key, value, module):
    command = 'prefix-list {0} out'.format(value)
    return command


def get_route_map_in_command(key, value, module):
    command = 'route-map {0} in'.format(value)
    return command


def get_route_map_out_command(key, value, module):
    command = 'route-map {0} out'.format(value)
    return command


def get_maximum_prefix_command(key, value, module):
    return get_maximum_prefix_options_command(key, value, module)


def get_maximum_prefix_options_command(key, value, module):
    command = 'maximum-prefix {0}'.format(module.params['max_prefix_limit'])
    if module.params['max_prefix_threshold']:
        command += ' {0}'.format(module.params['max_prefix_threshold'])
    if module.params['max_prefix_interval']:
        command += ' restart {0}'.format(module.params['max_prefix_interval'])
    elif module.params['max_prefix_warning']:
        command += ' warning-only'
    return command


def get_soft_reconfiguration_inbound_command(key, value, module):
    command = ''
    if value == 'enable':
        command = key
    elif value == 'always':
        command = '{0} {1}'.format(key, value)
    return command


def get_default_command(key, value, existing_commands):
    command = ''
    if key == 'send-community' and existing_commands.get(key) == 'none':
        command = 'no {0}'.format(key)

    elif existing_commands.get(key):
        existing_value = existing_commands.get(key)
        if value == 'inherit':
            if existing_value != 'inherit':
                command = 'no {0}'.format(key)
        else:
            if key == 'advertise-map exist':
                command = 'no advertise-map {0} exist-map {1}'.format(
                    existing_value[0], existing_value[1])
            elif key == 'advertise-map non-exist':
                command = 'no advertise-map {0} non-exist-map {1}'.format(
                    existing_value[0], existing_value[1])
            elif key == 'filter-list in':
                command = 'no filter-list {0} in'.format(existing_value)
            elif key == 'filter-list out':
                command = 'no filter-list {0} out'.format(existing_value)
            elif key == 'prefix-list in':
                command = 'no prefix-list {0} in'.format(existing_value)
            elif key == 'prefix-list out':
                command = 'no prefix-list {0} out'.format(existing_value)
            elif key == 'route-map in':
                command = 'no route-map {0} in'.format(existing_value)
            elif key == 'route-map out':
                command = 'no route-map {0} out'.format(existing_value)
            elif key.startswith('maximum-prefix'):
                command = 'no maximum-prefix {0}'.format(
                                    existing_commands.get('maximum-prefix'))
            elif key == 'allowas-in max':
                command = ['no allowas-in {0}'.format(existing_value)]
                command.append('allowas-in')
            else:
                command = 'no {0} {1}'.format(key, existing_value)
    else:
        if key.replace(' ', '_').replace('-', '_') in BOOL_PARAMS:
            command = 'no {0}'.format(key)
    return command


def fix_proposed(module, proposed):
    allowas_in = proposed.get('allowas_in')
    allowas_in_max = proposed.get('allowas_in_max')

    if allowas_in is False and allowas_in_max:
        proposed.pop('allowas_in_max')
    elif allowas_in and allowas_in_max:
        proposed.pop('allowas_in')

    return proposed


def state_present(module, existing, proposed, candidate):
    commands = list()

    proposed = fix_proposed(module, proposed)

    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, proposed)
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)

    custom = [
        'address-family',
        'capability additional-paths receive',
        'capability additional-paths send',
        'advertise-map exist',
        'advertise-map non-exist',
        'allowas-in max',
        'filter-list in',
        'filter-list out',
        'maximum-prefix',
        'maximum-prefix options',
        'prefix-list in',
        'prefix-list out',
        'route-map in',
        'route-map out',
        'soft-reconfiguration inbound'
    ]
    for key, value in proposed_commands.iteritems():
        if key == 'send-community' and value == 'none':
            commands.append('{0}'.format(key))

        elif value is True and key != 'maximum-prefix options':
            commands.append(key)

        elif value is False and key != 'maximum-prefix options':
            commands.append('no {0}'.format(key))

        elif value == 'default' or value == 'inherit':
            command = get_default_command(key, value, existing_commands)

            if isinstance(command, str):
                if command and command not in commands:
                    commands.append(command)
            elif isinstance(command, list):
                for cmd in command:
                    if cmd not in commands:
                        commands.append(cmd)

        elif key in custom:
            fixed_key = key.replace(' ', '_').replace('-', '_')
            command = invoke('get_%s_command' % fixed_key, key, value, module)
            if command and command not in commands:
                commands.append(command)
        else:
            command = '{0} {1}'.format(key, value)
            commands.append(command)

    if commands:
        parents = ["router bgp {0}".format(module.params['asn'])]
        if module.params['vrf'] != 'default':
            parents.append('vrf {0}'.format(module.params['vrf']))

        parents.append('neighbor {0}'.format(module.params['neighbor']))

        if len(commands) == 1:
            candidate.add(commands, parents=parents)
        elif len(commands) > 1:
            af_command = 'address-family {0} {1}'.format(
                                module.params['afi'], module.params['safi'])
            if af_command in commands:
                commands.remove(af_command)
                parents.append('address-family {0} {1}'.format(
                                module.params['afi'], module.params['safi']))
                candidate.add(commands, parents=parents)


def state_absent(module, existing, proposed, candidate):
    commands = []
    parents = ["router bgp {0}".format(module.params['asn'])]
    if module.params['vrf'] != 'default':
        parents.append('vrf {0}'.format(module.params['vrf']))

    parents.append('neighbor {0}'.format(module.params['neighbor']))
    commands.append('no address-family {0} {1}'.format(
                        module.params['afi'], module.params['safi']))
    candidate.add(commands, parents=parents)


def main():
    argument_spec = dict(
            asn=dict(required=True, type='str'),
            vrf=dict(required=False, type='str', default='default'),
            neighbor=dict(required=True, type='str'),
            afi=dict(required=True, type='str'),
            safi=dict(required=True, type='str'),
            additional_paths_receive=dict(required=False, type='str',
                                choices=['enable', 'disable', 'inherit']),
            additional_paths_send=dict(required=False, type='str',
                                choices=['enable', 'disable', 'inherit']),
            advertise_map_exist=dict(required=False, type='list'),
            advertise_map_non_exist=dict(required=False, type='list'),
            allowas_in=dict(required=False, type='bool'),
            allowas_in_max=dict(required=False, type='str'),
            as_override=dict(required=False, type='bool'),
            default_originate=dict(required=False, type='bool'),
            default_originate_route_map=dict(required=False, type='str'),
            filter_list_in=dict(required=False, type='str'),
            filter_list_out=dict(required=False, type='str'),
            max_prefix_limit=dict(required=False, type='str'),
            max_prefix_interval=dict(required=False, type='str'),
            max_prefix_threshold=dict(required=False, type='str'),
            max_prefix_warning=dict(required=False, type='bool'),
            next_hop_self=dict(required=False, type='bool'),
            next_hop_third_party=dict(required=False, type='bool'),
            prefix_list_in=dict(required=False, type='str'),
            prefix_list_out=dict(required=False, type='str'),
            route_map_in=dict(required=False, type='str'),
            route_map_out=dict(required=False, type='str'),
            route_reflector_client=dict(required=False, type='bool'),
            send_community=dict(required=False, choices=['none',
                                                         'both',
                                                         'extended',
                                                         'standard',
                                                         'default']),
            soft_reconfiguration_in=dict(required=False, type='str',
                                choices=['enable', 'always', 'inherit']),
            soo=dict(required=False, type='str'),
            suppress_inactive=dict(required=False, type='bool'),
            unsuppress_map=dict(required=False, type='str'),
            weight=dict(required=False, type='str'),
            m_facts=dict(required=False, default=False, type='bool'),
            state=dict(choices=['present', 'absent'], default='present',
                       required=False),
            include_defaults=dict(default=True)
    )
    argument_spec.update(nxos_argument_spec)
    module = get_module(argument_spec=argument_spec,
                        mutually_exclusive=[['advertise_map_exist',
                                             'advertise_map_non_exist']],
                        supports_check_mode=True)

    state = module.params['state']
    if ((module.params['max_prefix_interval'] or
        module.params['max_prefix_warning'] or
        module.params['max_prefix_threshold']) and
        not module.params['max_prefix_limit']):
        module.fail_json(msg='max_prefix_limit is required when using '
                             'max_prefix_warning, max_prefix_limit or '
                             'max_prefix_threshold.')
    if module.params['vrf'] == 'default' and module.params['soo']:
        module.fail_json(msg='SOO is only allowed in non-default VRF')

    args =  [
            'afi',
            'asn',
            'neighbor',
            'additional_paths_receive',
            'additional_paths_send',
            'advertise_map_exist',
            'advertise_map_non_exist',
            'allowas_in',
            'allowas_in_max',
            'as_override',
            'default_originate',
            'default_originate_route_map',
            'filter_list_in',
            'filter_list_out',
            'max_prefix_limit',
            'max_prefix_interval',
            'max_prefix_threshold',
            'max_prefix_warning',
            'next_hop_self',
            'next_hop_third_party',
            'prefix_list_in',
            'prefix_list_out',
            'route_map_in',
            'route_map_out',
            'soft_reconfiguration_in',
            'soo',
            'suppress_inactive',
            'unsuppress_map',
            'weight',
            'route_reflector_client',
            'safi',
            'send_community',
            'vrf'
        ]

    existing = invoke('get_existing', module, args)
    if existing.get('asn'):
        if (existing.get('asn') != module.params['asn'] and
            state == 'present'):
            module.fail_json(msg='Another BGP ASN already exists.',
                             proposed_asn=module.params['asn'],
                             existing_asn=existing.get('asn'))

    if module.params['advertise_map_exist'] == ['default']:
        module.params['advertise_map_exist'] = 'default'
    if module.params['advertise_map_non_exist'] == ['default']:
        module.params['advertise_map_non_exist'] = 'default'

    end_state = existing
    proposed_args = dict((k, v) for k, v in module.params.iteritems()
                    if v is not None and k in args)

    proposed = {}
    for key, value in proposed_args.iteritems():
        if key not in ['asn', 'vrf', 'neighbor']:
            if not isinstance(value, list):
                if str(value).lower() == 'true':
                    value = True
                elif str(value).lower() == 'false':
                    value = False
                elif str(value).lower() == 'default':
                    value = PARAM_TO_DEFAULT_KEYMAP.get(key)
                    if value is None:
                        if key in BOOL_PARAMS:
                            value = False
                        else:
                            value = 'default'
            if existing.get(key) or (not existing.get(key) and value):
                proposed[key] = value

    result = {}
    if state == 'present' or (state == 'absent' and existing):
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

    if WARNINGS:
        result['warnings'] = WARNINGS

    module.exit_json(**result)


if __name__ == '__main__':
    main()
