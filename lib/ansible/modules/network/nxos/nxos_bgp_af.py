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
module: nxos_bgp_af
version_added: "2.2"
short_description: Manages BGP Address-family configuration
description:
    - Manages BGP Address-family configurations on NX-OS switches
author: Gabriele Gerbino (@GGabriele)
extends_documentation_fragment: nxos
notes:
    - State 'absent' removes the whole BGP ASN configuration
    - default, where supported, restores params default value
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
    additional_paths_install:
        description:
            - Install a backup path into the forwarding table and provide
              prefix 'independent convergence (PIC) in case of a PE-CE link
              failure.
        required: false
        choices: ['true','false']
        default: null
    additional_paths_receive:
        description:
            - Enables the receive capability of additional paths for all of
              the neighbors under this address family for which the capability
              has not been disabled.
        required: false
        choices: ['true','false']
        default: null
    additional_paths_selection:
        description:
            - Configures the capability of selecting additional paths for
              a prefix. Valid values are a string defining the name of
              the route-map.
        required: false
        default: null
    additional_paths_send:
        description:
            - Enables the send capability of additional paths for all of
              the neighbors under this address family for which the capability
              has not been disabled.
        required: false
        choices: ['true','false']
        default: null
    advertise_l2vpn_evpn:
        description:
            - Advertise evpn routes.
        required: false
        choices: ['true','false']
        default: null
    client_to_client:
        description:
            - Configure client-to-client route reflection.
        required: false
        choices: ['true','false']
        default: null
    dampen_igp_metric:
        description:
            - Specify dampen value for IGP metric-related changes, in seconds.
              Valid values are integer and keyword 'default'.
        required: false
        default: null
    dampening_state:
        description:
            - Enable/disable route-flap dampening.
        required: false
        choices: ['true','false']
        default: null
    dampening_half_time:
        description:
            - Specify decay half-life in minutes for route-flap dampening.
              Valid values are integer and keyword 'default'.
        required: false
        default: null
    dampening_max_suppress_time:
        description:
            - Specify max suppress time for route-flap dampening stable route.
              Valid values are integer and keyword 'default'.
        required: false
        default: null
    dampening_reuse_time:
        description:
            - Specify route reuse time for route-flap dampening.
              Valid values are integer and keyword 'default'.
        required: false
    dampening_routemap:
        description:
            - Specify route-map for route-flap dampening. Valid values are a
              string defining the name of the route-map.
        required: false
        default: null
    dampening_suppress_time:
        description:
            - Specify route suppress time for route-flap dampening.
              Valid values are integer and keyword 'default'.
        required: false
        default: null
    default_information_originate:
        description:
            - Default information originate.
        required: false
        choices: ['true','false']
        default: null
    default_metric:
        description:
            - Sets default metrics for routes redistributed into BGP.
              Valid values are Integer or keyword 'default'
        required: false
        default: null
    distance_ebgp:
        description:
            - Sets the administrative distance for eBGP routes.
              Valid values are Integer or keyword 'default'.
        required: false
        default: null
    distance_ibgp:
        description:
            - Sets the administrative distance for iBGP routes.
              Valid values are Integer or keyword 'default'.
        required: false
        default: null
    distance_local:
        description:
            - Sets the administrative distance for local BGP routes.
              Valid values are Integer or keyword 'default'.
        required: false
        default: null
    inject_map:
        description:
            - An array of route-map names which will specify prefixes to
              inject. Each array entry must first specify the inject-map name,
              secondly an exist-map name, and optionally the copy-attributes
              keyword which indicates that attributes should be copied from
              the aggregate. For example [['lax_inject_map', 'lax_exist_map'],
              ['nyc_inject_map', 'nyc_exist_map', 'copy-attributes'],
              ['fsd_inject_map', 'fsd_exist_map']]
        required: false
        default: null
    maximum_paths:
        description:
            - Configures the maximum number of equal-cost paths for
              load sharing. Valid value is an integer in the range 1-64.
        default: null
    maximum_paths_ibgp:
        description:
            - Configures the maximum number of ibgp equal-cost paths for
              load sharing. Valid value is an integer in the range 1-64.
        required: false
        default: null
    networks:
        description:
            - Networks to configure. Valid value is a list of network
              prefixes to advertise. The list must be in the form of an array.
              Each entry in the array must include a prefix address and an
              optional route-map. Example: [['10.0.0.0/16', 'routemap_LA'],
              ['192.168.1.1', 'Chicago'], ['192.168.2.0/24],
              ['192.168.3.0/24', 'routemap_NYC']]
        required: false
        default: null
    next_hop_route_map:
        description:
            - Configure a route-map for valid nexthops. Valid values are a
              string defining the name of the route-map.
        required: false
        default: null
    redistribute:
        description:
            - A list of redistribute directives. Multiple redistribute entries
              are allowed. The list must be in the form of a nested array.
              the first entry of each array defines the source-protocol to
              redistribute from; the second entry defines a route-map name.
              A route-map is highly advised but may be optional on some
              platforms, in which case it may be omitted from the array list.
              Example: [['direct', 'rm_direct'], ['lisp', 'rm_lisp']]
        required: false
        default: null
    suppress_inactive:
        description:
            - Advertises only active routes to peers.
        required: false
        choices: ['true','false']
        default: null
    table_map:
        description:
            - Apply table-map to filter routes downloaded into URIB.
              Valid values are a string.
        required: false
        default: null
    table_map_filter:
        description:
            - Filters routes rejected by the route-map and does not download
              them to the RIB.
        required: false
        choices: ['true','false']
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
# configure a simple address-family
- nxos_bgp_af:
    asn: 65535
    vrf: TESTING
    afi: ipv4
    safi: unicast
    advertise_l2vpn_evpn: true
    state: present
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"advertise_l2vpn_evpn": true, "afi": "ipv4",
             "asn": "65535", "safi": "unicast", "vrf": "TESTING"}
existing:
    description: k/v pairs of existing BGP AF configuration
    type: dict
    sample: {}
end_state:
    description: k/v pairs of BGP AF configuration after module execution
    returned: always
    type: dict
    sample: {"additional_paths_install": false,
            "additional_paths_receive": false,
            "additional_paths_selection": "",
            "additional_paths_send": false,
            "advertise_l2vpn_evpn": true, "afi": "ipv4",
            "asn": "65535", "client_to_client": true,
            "dampen_igp_metric": "600", "dampening_half_time": "",
            "dampening_max_suppress_time": "", "dampening_reuse_time": "",
            "dampening_routemap": "", "dampening_state": false,
            "dampening_suppress_time": "",
            "default_information_originate": false, "default_metric": "",
            "distance_ebgp": "20", "distance_ibgp": "200",
            "distance_local": "220", "inject_map": [], "maximum_paths": "1",
            "maximum_paths_ibgp": "1", "networks": [],
            "next_hop_route_map": "", "redistribute": [], "safi": "unicast",
            "suppress_inactive": false, "table_map": "",
            "table_map_filter": false, "vrf": "TESTING"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["router bgp 65535", "vrf TESTING",
            "address-family ipv4 unicast", "advertise l2vpn evpn"]
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
    'additional_paths_install',
    'additional_paths_receive',
    'additional_paths_send',
    'advertise_l2vpn_evpn',
    'client_to_client',
    'dampening_state',
    'default_information_originate',
    'suppress_inactive',
]
PARAM_TO_DEFAULT_KEYMAP = {
    'maximum_paths': '1',
    'maximum_paths_ibgp': '1',
    'client_to_client': True,
    'distance_ebgp': '20',
    'distance_ibgp': '200',
    'distance_local': '220',
    'dampen_igp_metric': '600'
}
PARAM_TO_COMMAND_KEYMAP = {
    'asn': 'router bgp',
    'afi': 'address-family',
    'safi': 'address-family',
    'additional_paths_install': 'additional-paths install backup',
    'additional_paths_receive': 'additional-paths receive',
    'additional_paths_selection': 'additional-paths selection route-map',
    'additional_paths_send': 'additional-paths send',
    'advertise_l2vpn_evpn': 'advertise l2vpn evpn',
    'client_to_client': 'client-to-client reflection',
    'dampen_igp_metric': 'dampen-igp-metric',
    'dampening_state': 'dampening',
    'dampening_half_time': 'dampening',
    'dampening_max_suppress_time': 'dampening',
    'dampening_reuse_time': 'dampening',
    'dampening_routemap': 'dampening route-map',
    'dampening_suppress_time': 'dampening',
    'default_information_originate': 'default-information originate',
    'default_metric': 'default-metric',
    'distance_ebgp': 'distance',
    'distance_ibgp': 'distance',
    'distance_local': 'distance',
    'inject_map': 'inject-map',
    'maximum_paths': 'maximum-paths',
    'maximum_paths_ibgp': 'maximum-paths ibgp',
    'networks': 'network',
    'redistribute': 'redistribute',
    'next_hop_route_map': 'nexthop route-map',
    'suppress_inactive': 'suppress-inactive',
    'table_map': 'table-map',
    'table_map_filter': 'table-map-filter',
    'vrf': 'vrf'
}
DAMPENING_PARAMS = [
        'dampening_half_time',
        'dampening_suppress_time',
        'dampening_reuse_time',
        'dampening_max_suppress_time'
        ]


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def get_custom_list_value(config, arg, module):
    value_list = []
    splitted_config = config.splitlines()
    if arg == 'inject_map':
        REGEX_INJECT = ('.*inject-map\s(?P<inject_map>\S+)'
                       '\sexist-map\s(?P<exist_map>\S+)-*')

        for line in splitted_config:
            value =  []
            inject_group = {}
            try:
                match_inject = re.match(REGEX_INJECT, line, re.DOTALL)
                inject_group = match_inject.groupdict()
                inject_map = inject_group['inject_map']
                exist_map = inject_group['exist_map']
                value.append(inject_map)
                value.append(exist_map)
            except AttributeError:
                value =  []

            if value:
                copy_attributes = False
                inject_map_command = ('inject-map {0} exist-map {1} '
                                      'copy-attributes'.format(
                                      inject_group['inject_map'],
                                      inject_group['exist_map']))

                REGEX = re.compile(r'\s+{0}\s*$'.format(
                                                inject_map_command), re.M)
                try:
                    if REGEX.search(config):
                        copy_attributes = True
                except TypeError:
                    copy_attributes = False

                if copy_attributes:
                    value.append('copy_attributes')
                value_list.append(value)

    elif arg == 'networks':
        REGEX_NETWORK = re.compile(r'(?:network\s)(?P<value>.*)$')

        for line in splitted_config:
            value =  []
            network_group = {}
            if 'network' in line:
                value = REGEX_NETWORK.search(line).group('value').split()

                if value:
                    if len(value) == 3:
                        value.pop(1)
                    value_list.append(value)

    elif arg == 'redistribute':
        RED_REGEX = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(
                                PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        for line in splitted_config:
            value =  []
            redistribute_group = {}
            if 'redistribute' in line:
                value = RED_REGEX.search(line).group('value').split()
                if value:
                    if len(value) == 3:
                        value.pop(1)
                    elif len(value) == 4:
                        value = ['{0} {1}'.format(
                                        value[0], value[1]), value[3]]
                    value_list.append(value)
    return value_list


def get_custom_string_value(config, arg, module):
    value = ''
    if arg.startswith('distance'):
        REGEX_DISTANCE = ('.*distance\s(?P<d_ebgp>\w+)\s(?P<d_ibgp>\w+)'
                          '\s(?P<d_local>\w+)')
        try:
            match_distance = re.match(REGEX_DISTANCE, config, re.DOTALL)
            distance_group = match_distance.groupdict()
        except AttributeError:
            distance_group = {}

        if distance_group:
            if arg == 'distance_ebgp':
                value = distance_group['d_ebgp']
            elif arg == 'distance_ibgp':
                value = distance_group['d_ibgp']
            elif arg == 'distance_local':
                value = distance_group['d_local']

    elif arg.startswith('dampening'):
        REGEX = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(
                                PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        if arg == 'dampen_igp_metric' or  arg == 'dampening_routemap':
            value = ''
            if PARAM_TO_COMMAND_KEYMAP[arg] in config:
                value = REGEX.search(config).group('value')
        else:
            REGEX_DAMPENING = ('.*dampening\s(?P<half>\w+)\s(?P<reuse>\w+)'
                              '\s(?P<suppress>\w+)\s(?P<max_suppress>\w+)')
            try:
                match_dampening = re.match(REGEX_DAMPENING, config, re.DOTALL)
                dampening_group = match_dampening.groupdict()
            except AttributeError:
                dampening_group = {}

            if dampening_group:
                if arg == 'dampening_half_time':
                    value = dampening_group['half']
                elif arg == 'dampening_reuse_time':
                    value = dampening_group['reuse']
                elif arg == 'dampening_suppress_time':
                    value = dampening_group['suppress']
                elif arg == 'dampening_max_suppress_time':
                    value = dampening_group['max_suppress']

    elif arg == 'table_map_filter':
        TMF_REGEX = re.compile(r'\s+table-map.*filter$', re.M)
        value = False
        try:
            if TMF_REGEX.search(config):
                value = True
        except TypeError:
            value = False
    elif arg == 'table_map':
        TM_REGEX = re.compile(r'(?:table-map\s)(?P<value>\S+)(\sfilter)?$', re.M)
        value = ''
        if PARAM_TO_COMMAND_KEYMAP[arg] in config:
            value = TM_REGEX.search(config).group('value')
    return value


def get_value(arg, config, module):
    custom = [
        'inject_map',
        'networks',
        'redistribute'
    ]

    if arg in BOOL_PARAMS:
        REGEX = re.compile(r'\s+{0}\s*$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        value = False
        try:
            if REGEX.search(config):
                value = True
        except TypeError:
            value = False

    elif arg in custom:
        value = get_custom_list_value(config, arg, module)

    elif (arg.startswith('distance') or arg.startswith('dampening') or
            arg.startswith('table_map')):
        value = get_custom_string_value(config, arg, module)

    else:
        REGEX = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        value = ''
        if PARAM_TO_COMMAND_KEYMAP[arg] in config:
            value = REGEX.search(config).group('value')
    return value


def get_existing(module, args):
    existing = {}
    netcfg = custom_get_config(module)

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

        parents.append('address-family {0} {1}'.format(module.params['afi'],
                                                module.params['safi']))
        config = netcfg.get_section(parents)

        if config:
            for arg in args:
                if arg not in ['asn', 'afi', 'safi', 'vrf']:
                    existing[arg] = get_value(arg, config, module)

            existing['asn'] = existing_asn
            existing['afi'] = module.params['afi']
            existing['safi'] = module.params['safi']
            existing['vrf'] = module.params['vrf']
    else:
        WARNINGS.append("The BGP process {0} didn't exist but the task"
                        " just created it.".format(module.params['asn']))

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


def fix_proposed(module, proposed, existing):
    commands = list()
    command = ''
    fixed_proposed = {}
    for key, value in proposed.iteritems():
        if key in DAMPENING_PARAMS:
            if value != 'default':
                command = 'dampening {0} {1} {2} {3}'.format(
                    proposed.get('dampening_half_time'),
                    proposed.get('dampening_reuse_time'),
                    proposed.get('dampening_suppress_time'),
                    proposed.get('dampening_max_suppress_time'))
            else:
                if existing.get(key):
                    command = ('no dampening {0} {1} {2} {3}'.format(
                        existing['dampening_half_time'],
                        existing['dampening_reuse_time'],
                        existing['dampening_suppress_time'],
                        existing['dampening_max_suppress_time']))
            if 'default' in command:
                command = ''
        elif key.startswith('distance'):
            command = 'distance {0} {1} {2}'.format(
                proposed.get('distance_ebgp'),
                proposed.get('distance_ibgp'),
                proposed.get('distance_local'))
        else:
            fixed_proposed[key] = value

        if command:
            if command not in commands:
                commands.append(command)

    return fixed_proposed, commands


def default_existing(existing_value, key, value):
    commands = []
    if key == 'network':
        for network in existing_value:
            if len(network) == 2:
                commands.append('no network {0} route-map {1}'.format(
                        network[0], network[1]))
            elif len(network) == 1:
                commands.append('no network {0}'.format(
                        network[0]))

    elif key == 'inject-map':
        for maps in existing_value:
            if len(maps) == 2:
                commands.append('no inject-map {0} exist-map {1}'.format(
                                maps[0], maps[1]))
            elif len(maps) == 3:
                commands.append('no inject-map {0} exist-map {1} '
                                'copy-attributes'.format(
                                maps[0], maps[1]))
    else:
        commands.append('no {0} {1}'.format(key, existing_value))
    return commands


def get_network_command(existing, key, value):
    commands = []
    existing_networks = existing.get('networks', [])
    for inet in value:
        if not isinstance(inet, list):
            inet = [inet]
        if inet not in existing_networks:
            if len(inet) == 1:
                command = '{0} {1}'.format(key, inet[0])
            elif len(inet) == 2:
                command = '{0} {1} route-map {2}'.format(key,
                                                inet[0], inet[1])
            commands.append(command)
    return commands


def get_inject_map_command(existing, key, value):
    commands = []
    existing_maps = existing.get('inject_map', [])
    for maps in value:
        if not isinstance(maps, list):
            maps = [maps]
        if maps not in existing_maps:
            if len(maps) == 2:
                command = ('inject-map {0} exist-map {1}'.format(
                            maps[0], maps[1]))
            elif len(maps) == 3:
                command = ('inject-map {0} exist-map {1} '
                           'copy-attributes'.format(maps[0],
                                                    maps[1]))
            commands.append(command)
    return commands


def get_redistribute_command(existing, key, value):
    commands = []
    for rule in value:
        if rule[1] == 'default':
            existing_rule = existing.get('redistribute', [])
            for each_rule in existing_rule:
                if rule[0] in each_rule:
                    command = 'no {0} {1} route-map {2}'.format(
                                    key, each_rule[0], each_rule[1])
                    commands.append(command)
        else:
            command = '{0} {1} route-map {2}'.format(key, rule[0], rule[1])
            commands.append(command)
    return commands


def get_table_map_command(module, existing, key, value):
    commands = []
    if key == 'table-map':
        if value != 'default':
            command = '{0} {1}'.format(key, module.params['table_map'])
            if (module.params['table_map_filter'] is not None and
                module.params['table_map_filter'] != 'default'):
                command += ' filter'
            commands.append(command)
        else:
            if existing.get('table_map'):
                command = 'no {0} {1}'.format(key, existing.get('table_map'))
                commands.append(command)
    return commands


def get_default_table_map_filter(existing):
    commands = []
    existing_table_map_filter = existing.get('table_map_filter')
    if existing_table_map_filter:
        existing_table_map = existing.get('table_map')
        if existing_table_map:
            command = 'table-map {0}'.format(existing_table_map)
            commands.append(command)
    return commands


def state_present(module, existing, proposed, candidate):
    fixed_proposed, commands = fix_proposed(module, proposed, existing)
    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, fixed_proposed)
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)
    for key, value in proposed_commands.iteritems():
        if key == 'address-family':
            addr_family_command = "address-family {0} {1}".format(
                            module.params['afi'], module.params['safi'])
            if addr_family_command not in commands:
                commands.append(addr_family_command)

        elif key.startswith('table-map'):
            table_map_commands = get_table_map_command(module, existing, key, value)
            if table_map_commands:
                commands.extend(table_map_commands)

        elif value is True:
            commands.append(key)

        elif value is False:
            commands.append('no {0}'.format(key))

        elif value == 'default':
            if key in PARAM_TO_DEFAULT_KEYMAP.keys():
                commands.append('{0} {1}'.format(key, PARAM_TO_DEFAULT_KEYMAP[key]))

            elif existing_commands.get(key):
                if key == 'table-map-filter':
                    default_tmf_command = get_default_table_map_filter(existing)

                    if default_tmf_command:
                        commands.extend(default_tmf_command)
                else:
                    existing_value = existing_commands.get(key)
                    default_command = default_existing(existing_value, key, value)
                    if default_command:
                        commands.extend(default_command)
        else:
            if key == 'network':
                network_commands = get_network_command(existing, key, value)
                if network_commands:
                    commands.extend(network_commands)

            elif key == 'inject-map':
                inject_map_commands = get_inject_map_command(existing, key, value)
                if inject_map_commands:
                    commands.extend(inject_map_commands)

            elif key == 'redistribute':
                redistribute_commands = get_redistribute_command(existing, key, value)
                if redistribute_commands:
                    commands.extend(redistribute_commands)

            else:
                command = '{0} {1}'.format(key, value)
                commands.append(command)

    if commands:
        parents = ["router bgp {0}".format(module.params['asn'])]
        if module.params['vrf'] != 'default':
            parents.append('vrf {0}'.format(module.params['vrf']))

        if len(commands) == 1:
            candidate.add(commands, parents=parents)
        elif len(commands) > 1:
            parents.append('address-family {0} {1}'.format(module.params['afi'],
                                                module.params['safi']))
            if addr_family_command in commands:
                commands.remove(addr_family_command)
            candidate.add(commands, parents=parents)


def state_absent(module, existing, proposed, candidate):
    commands = []
    parents = ["router bgp {0}".format(module.params['asn'])]
    if module.params['vrf'] != 'default':
        parents.append('vrf {0}'.format(module.params['vrf']))

    commands.append('no address-family {0} {1}'.format(
                            module.params['afi'], module.params['safi']))
    candidate.add(commands, parents=parents)


def main():
    argument_spec = dict(
            asn=dict(required=True, type='str'),
            vrf=dict(required=False, type='str', default='default'),
            safi=dict(required=True, type='str', choices=['unicast','multicast', 'evpn']),
            afi=dict(required=True, type='str', choices=['ipv4','ipv6', 'vpnv4', 'vpnv6', 'l2vpn']),
            additional_paths_install=dict(required=False, type='bool'),
            additional_paths_receive=dict(required=False, type='bool'),
            additional_paths_selection=dict(required=False, type='str'),
            additional_paths_send=dict(required=False, ype='bool'),
            advertise_l2vpn_evpn=dict(required=False, type='bool'),
            client_to_client=dict(required=False, type='bool'),
            dampen_igp_metric=dict(required=False, type='str'),
            dampening_state=dict(required=False, type='bool'),
            dampening_half_time=dict(required=False, type='str'),
            dampening_max_suppress_time=dict(required=False, type='str'),
            dampening_reuse_time=dict(required=False, type='str'),
            dampening_routemap=dict(required=False, type='str'),
            dampening_suppress_time=dict(required=False, type='str'),
            default_information_originate=dict(required=False, type='bool'),
            default_metric=dict(required=False, type='str'),
            distance_ebgp=dict(required=False, type='str'),
            distance_ibgp=dict(required=False, type='str'),
            distance_local=dict(required=False, type='str'),
            inject_map=dict(required=False, type='list'),
            maximum_paths=dict(required=False, type='str'),
            maximum_paths_ibgp=dict(required=False, type='str'),
            networks=dict(required=False, type='list'),
            next_hop_route_map=dict(required=False, type='str'),
            redistribute=dict(required=False, type='list'),
            suppress_inactive=dict(required=False, type='bool'),
            table_map=dict(required=False, type='str'),
            table_map_filter=dict(required=False, type='bool'),
            m_facts=dict(required=False, default=False, type='bool'),
            state=dict(choices=['present', 'absent'], default='present',
                       required=False),
            include_defaults=dict(default=True)
    )
    argument_spec.update(nxos_argument_spec)
    module = get_module(argument_spec=argument_spec,
                        required_together=[DAMPENING_PARAMS,
                                          ['distance_ibgp',
                                           'distance_ebgp',
                                           'distance_local']],
                        supports_check_mode=True)

    state = module.params['state']
    if module.params['dampening_routemap']:
        for param in DAMPENING_PARAMS:
            if module.params[param]:
                module.fail_json(msg='dampening_routemap cannot be used with'
                                     ' the {0} param'.format(param))

    if module.params['advertise_l2vpn_evpn']:
        if module.params['vrf'] == 'default':
            module.fail_json(msg='It is not possible to advertise L2VPN '
                                 'EVPN in the default VRF. Please specify '
                                 'another one.', vrf=module.params['vrf'])

    if module.params['table_map_filter'] and not module.params['table_map']:
        module.fail_json(msg='table_map param is needed when using'
                             ' table_map_filter filter.')

    args =  [
            "additional_paths_install",
            "additional_paths_receive",
            "additional_paths_selection",
            "additional_paths_send",
            "advertise_l2vpn_evpn",
            "afi",
            "asn",
            "client_to_client",
            "dampen_igp_metric",
            "dampening_half_time",
            "dampening_max_suppress_time",
            "dampening_reuse_time",
            "dampening_suppress_time",
            "dampening_routemap",
            "dampening_state",
            "default_information_originate",
            "default_metric",
            "distance_ebgp",
            "distance_ibgp",
            "distance_local",
            "inject_map",
            "maximum_paths",
            "maximum_paths_ibgp",
            "networks",
            "next_hop_route_map",
            "redistribute",
            "safi",
            "suppress_inactive",
            "table_map",
            "table_map_filter",
            "vrf"
        ]

    existing = invoke('get_existing', module, args)

    if existing.get('asn'):
        if (existing.get('asn') != module.params['asn'] and
            state == 'present'):
            module.fail_json(msg='Another BGP ASN already exists.',
                             proposed_asn=module.params['asn'],
                             existing_asn=existing.get('asn'))

    end_state = existing
    proposed_args = dict((k, v) for k, v in module.params.iteritems()
                    if v is not None and k in args)

    if proposed_args.get('networks'):
        if proposed_args['networks'][0] == 'default':
            proposed_args['networks'] = 'default'
    if proposed_args.get('inject_map'):
        if proposed_args['inject_map'][0] == 'default':
            proposed_args['inject_map'] = 'default'

    proposed = {}
    for key, value in proposed_args.iteritems():
        if key not in ['asn', 'vrf']:
            if str(value).lower() == 'default':
                value = PARAM_TO_DEFAULT_KEYMAP.get(key)
                if value is None:
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
