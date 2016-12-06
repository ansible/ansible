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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: nxos_igmp_interface
version_added: "2.2"
short_description: Manages IGMP interface configuration
description:
    - Manages IGMP interface configuration settings
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - When state=default, supported params will be reset to a default state.
      These include: version, startup_query_interval, startup_query_count,
      robustness, querier_timeout, query_mrt, query_interval, last_member_qrt,
      last_member_query_count, group_timeout, report_llg, and immediate_leave
    - When state=absent, all configs for oif_prefix, oif_source, and
      oif_routemap will be removed.
    - PIM must be enabled to use this module
    - This module is for Layer 3 interfaces
    - Route-map check not performed (same as CLI) check when configuring
      route-map with 'static-oif'
    - If restart is set to true with other params set, the restart will happen
      last, i.e. after the configuration takes place
    - While username and password are not required params, they are
      if you are not using the .netauth file.  .netauth file is recommended
      as it will clean up the each task in the playbook by not requiring
      the username and password params for every tasks.
    - Using the username and password params will override the .netauth file
options:
    interface:
        description:
            - The FULL interface name for IGMP configuration.
        required: true
    version:
        description:
            - IGMP version. It can be 2 or 3.
        required: false
        default: null
        choices: ['2', '3']
    startup_query_interval:
        description:
            - Query interval used when the IGMP process starts up.
              The range is from 1 to 18000. The default is 31.
        required: false
        default: null
    startup_query_count:
        description:
            - Query count used when the IGMP process starts up.
              The range is from 1 to 10. The default is 2.
        required: false
        default: null
    robustness:
        description:
            - Sets the robustness variable. Values can range from 1 to 7.
              The default is 2.
        required: false
        default: null
    querier_timeout:
        description:
            - Sets the querier timeout that the software uses when deciding
              to take over as the querier. Values can range from 1 to 65535
              seconds. The default is 255 seconds.
        required: false
        default: null
    query_mrt:
        description:
            - Sets the response time advertised in IGMP queries.
              Values can range from 1 to 25 seconds. The default is 10 seconds.
        required: false
        default: null
    query_interval:
        description:
            - Sets the frequency at which the software sends IGMP host query
              messages. Values can range from 1 to 18000 seconds.
              he default is 125 seconds.
        required: false
        default: null
    last_member_qrt:
        description:
            - Sets the query interval waited after sending membership reports
              before the software deletes the group state. Values can range
              from 1 to 25 seconds. The default is 1 second
        required: false
        default: null
    last_member_query_count:
        description:
            - Sets the number of times that the software sends an IGMP query
              in response to a host leave message.
              Values can range from 1 to 5. The default is 2.
        required: false
        default: null
    group_timeout:
        description:
            - Sets the group membership timeout for IGMPv2.
              Values can range from 3 to 65,535 seconds.
              The default is 260 seconds.
        required: false
        default: null
    report_llg:
        description:
            - Configures report-link-local-groups.
              Enables sending reports for groups in 224.0.0.0/24.
              Reports are always sent for nonlink local groups.
              By default, reports are not sent for link local groups.
        required: false
        choices: ['true', 'false']
        default: false
    immediate_leave:
        description:
            - Enables the device to remove the group entry from the multicast
              routing table immediately upon receiving a leave message for
              the group. Use this command to minimize the leave latency of
              IGMPv2 group memberships on a given IGMP interface because the
              device does not send group-specific queries.
              The default is disabled.
        required: false
        choices: ['true', 'false']
        default: false
    oif_routemap:
        description:
            - Configure a routemap for static outgoing interface (OIF).
        required: false
        default: null
    oif_prefix:
        description:
            - Configure a prefix for static outgoing interface (OIF).
        required: false
        default: null
    oif_source:
        description:
            - Configure a source for static outgoing interface (OIF).
        required: false
        default: null
    restart:
        description:
            - Restart IGMP
        required: false
        choices: ['true', 'false']
        default: null
    state:
        description:
            - Manages desired state of the resource
        required: false
        default: present
        choices: ['present', 'default']
'''
EXAMPLES = '''
- nxos_igmp_interface:
    interface: ethernet1/32
    startup_query_interval: 30
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
    sample: {"asn": "65535", "router_id": "1.1.1.1", "vrf": "test"}
existing:
    description: k/v pairs of existing BGP configuration
    type: dict
    sample: {"asn": "65535", "bestpath_always_compare_med": false,
            "bestpath_aspath_multipath_relax": false,
            "bestpath_compare_neighborid": false,
            "bestpath_compare_routerid": false,
            "bestpath_cost_community_ignore": false,
            "bestpath_med_confed": false,
            "bestpath_med_missing_as_worst": false,
            "bestpath_med_non_deterministic": false, "cluster_id": "",
            "confederation_id": "", "confederation_peers": "",
            "graceful_restart": true, "graceful_restart_helper": false,
            "graceful_restart_timers_restart": "120",
            "graceful_restart_timers_stalepath_time": "300", "local_as": "",
            "log_neighbor_changes": false, "maxas_limit": "",
            "neighbor_down_fib_accelerate": false, "reconnect_interval": "60",
            "router_id": "11.11.11.11", "suppress_fib_pending": false,
            "timer_bestpath_limit": "", "timer_bgp_hold": "180",
            "timer_bgp_keepalive": "60", "vrf": "test"}
end_state:
    description: k/v pairs of BGP configuration after module execution
    returned: always
    type: dict
    sample: {"asn": "65535", "bestpath_always_compare_med": false,
            "bestpath_aspath_multipath_relax": false,
            "bestpath_compare_neighborid": false,
            "bestpath_compare_routerid": false,
            "bestpath_cost_community_ignore": false,
            "bestpath_med_confed": false,
            "bestpath_med_missing_as_worst": false,
            "bestpath_med_non_deterministic": false, "cluster_id": "",
            "confederation_id": "", "confederation_peers": "",
            "graceful_restart": true, "graceful_restart_helper": false,
            "graceful_restart_timers_restart": "120",
            "graceful_restart_timers_stalepath_time": "300", "local_as": "",
            "log_neighbor_changes": false, "maxas_limit": "",
            "neighbor_down_fib_accelerate": false, "reconnect_interval": "60",
            "router_id": "1.1.1.1",  "suppress_fib_pending": false,
            "timer_bestpath_limit": "", "timer_bgp_hold": "180",
            "timer_bgp_keepalive": "60", "vrf": "test"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["router bgp 65535", "vrf test", "router-id 1.1.1.1"]
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


def get_cli_body_ssh(command, response, module):
    """Get response for when transport=cli.  This is kind of a hack and mainly
    needed because these modules were originally written for NX-API.  And
    not every command supports "| json" when using cli/ssh.  As such, we assume
    if | json returns an XML string, it is a valid command, but that the
    resource doesn't exist yet. Instead, the output will be a raw string
    when issuing commands containing 'show run'.
    """
    if 'xml' in response[0]:
        body = []
    elif 'show run' in command:
        body = response
    else:
        try:
            response = response[0].replace(command + '\n\n', '').strip()
            body = [json.loads(response)]
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
        command += ' | json'
        cmds = [command]
        response = execute_show(cmds, module)
        body = get_cli_body_ssh(command, response, module)
    elif module.params['transport'] == 'nxapi':
        cmds = [command]
        body = execute_show(cmds, module, command_type=command_type)

    return body


def get_interface_mode(interface, intf_type, module):
    command = 'show interface {0}'.format(interface)
    interface = {}
    mode = 'unknown'

    if intf_type in ['ethernet', 'portchannel']:
        body = execute_show_command(command, module)[0]
        interface_table = body['TABLE_interface']['ROW_interface']
        mode = str(interface_table.get('eth_mode', 'layer3'))
        if mode == 'access' or mode == 'trunk':
            mode = 'layer2'
    elif intf_type == 'loopback' or intf_type == 'svi':
        mode = 'layer3'
    return mode


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


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def get_igmp_interface(module, interface):
    command = 'show ip igmp interface {0}'.format(interface)
    igmp = {}

    key_map = {
        'IGMPVersion': 'version',
        'ConfiguredStartupQueryInterval': 'startup_query_interval',
        'StartupQueryCount': 'startup_query_count',
        'RobustnessVariable': 'robustness',
        'QuerierTimeout': 'querier_timeout',
        'ConfiguredMaxResponseTime': 'query_mrt',
        'ConfiguredQueryInterval': 'query_interval',
        'LastMemberMTR': 'last_member_qrt',
        'LastMemberQueryCount': 'last_member_query_count',
        'ConfiguredGroupTimeout': 'group_timeout'
    }

    body = execute_show_command(command, module)[0]

    if body:
        resource = body['TABLE_vrf']['ROW_vrf']['TABLE_if']['ROW_if']
        igmp = apply_key_map(key_map, resource)
        report_llg = str(resource['ReportingForLinkLocal'])
        if report_llg == 'true':
            igmp['report_llg'] = True
        elif report_llg == 'false':
            igmp['report_llg'] = False

        immediate_leave = str(resource['ImmediateLeave'])  # returns en or dis
        if immediate_leave == 'en':
            igmp['immediate_leave'] = True
        elif immediate_leave == 'dis':
            igmp['immediate_leave'] = False

    # the  next block of code is used to retrieve anything with:
    # ip igmp static-oif *** i.e.. could be route-map ROUTEMAP
    # or PREFIX source <ip>, etc.
    command = 'show run interface {0} | inc oif'.format(interface)

    body = execute_show_command(
                        command, module, command_type='cli_show_ascii')[0]

    staticoif = []
    if body:
        split_body = body.split('\n')
        route_map_regex = ('.*ip igmp static-oif route-map\s+'
                           '(?P<route_map>\S+).*')
        prefix_source_regex = ('.*ip igmp static-oif\s+(?P<prefix>'
                               '((\d+.){3}\d+))(\ssource\s'
                               '(?P<source>\S+))?.*')

        for line in split_body:
            temp = {}
            try:
                match_route_map = re.match(route_map_regex, line, re.DOTALL)
                route_map = match_route_map.groupdict()['route_map']
            except AttributeError:
                route_map = ''

            try:
                match_prefix_source = re.match(
                                        prefix_source_regex, line, re.DOTALL)
                prefix_source_group = match_prefix_source.groupdict()
                prefix = prefix_source_group['prefix']
                source = prefix_source_group['source']
            except AttributeError:
                prefix = ''
                source = ''

            if route_map:
                temp['route_map'] = route_map
            if prefix:
                temp['prefix'] = prefix
            if source:
                temp['source'] = source
            if temp:
                staticoif.append(temp)

    igmp['oif_routemap'] = None
    igmp['oif_prefix_source'] = []

    if staticoif:
        if len(staticoif) == 1 and staticoif[0].get('route_map'):
            igmp['oif_routemap'] = staticoif[0]['route_map']
        else:
            igmp['oif_prefix_source'] = staticoif

    return igmp


def config_igmp_interface(delta, found_both, found_prefix):
    CMDS = {
        'version': 'ip igmp version {0}',
        'startup_query_interval': 'ip igmp startup-query-interval {0}',
        'startup_query_count': 'ip igmp startup-query-count {0}',
        'robustness': 'ip igmp robustness-variable {0}',
        'querier_timeout': 'ip igmp querier-timeout {0}',
        'query_mrt': 'ip igmp query-max-response-time {0}',
        'query_interval': 'ip igmp query-interval {0}',
        'last_member_qrt': 'ip igmp last-member-query-response-time {0}',
        'last_member_query_count': 'ip igmp last-member-query-count {0}',
        'group_timeout': 'ip igmp group-timeout {0}',
        'report_llg': 'ip igmp report-link-local-groups',
        'immediate_leave': 'ip igmp immediate-leave',
        'oif_prefix_source': 'ip igmp static-oif {0} source {1} ',
        'oif_routemap': 'ip igmp static-oif route-map {0}',
        'oif_prefix': 'ip igmp static-oif {0}',
    }

    commands = []
    command = None

    for key, value in delta.iteritems():
        if key == 'oif_source' or found_both or found_prefix:
            pass
        elif key == 'oif_prefix':
            if delta.get('oif_source'):
                command = CMDS.get('oif_prefix_source').format(
                    delta.get('oif_prefix'), delta.get('oif_source'))
            else:
                command = CMDS.get('oif_prefix').format(
                    delta.get('oif_prefix'))
        elif value:
            command = CMDS.get(key).format(value)
        elif not value:
            command = 'no {0}'.format(CMDS.get(key).format(value))

        if command:
            if command not in commands:
                commands.append(command)
        command = None

    return commands


def get_igmp_interface_defaults():
    version = '2'
    startup_query_interval = '31'
    startup_query_count = '2'
    robustness = '2'
    querier_timeout = '255'
    query_mrt = '10'
    query_interval = '125'
    last_member_qrt = '1'
    last_member_query_count = '2'
    group_timeout = '260'
    report_llg = False
    immediate_leave = False

    args = dict(version=version, startup_query_interval=startup_query_interval,
                startup_query_count=startup_query_count, robustness=robustness,
                querier_timeout=querier_timeout, query_mrt=query_mrt,
                query_interval=query_interval, last_member_qrt=last_member_qrt,
                last_member_query_count=last_member_query_count,
                group_timeout=group_timeout, report_llg=report_llg,
                immediate_leave=immediate_leave)

    default = dict((param, value) for (param, value) in args.iteritems()
                   if value is not None)

    return default


def config_default_igmp_interface(existing, delta, found_both, found_prefix):
    commands = []
    proposed = get_igmp_interface_defaults()
    delta = dict(set(proposed.iteritems()).difference(existing.iteritems()))
    if delta:
        command = config_igmp_interface(delta, found_both, found_prefix)

        if command:
            for each in command:
                commands.append(each)

    return commands


def config_remove_oif(existing, existing_oif_prefix_source):
    commands = []
    command = None
    if existing.get('routemap'):
        command = 'no ip igmp static-oif route-map {0}'.format(
                                                    existing.get('routemap'))
    if existing_oif_prefix_source:
        for each in existing_oif_prefix_source:
            if each.get('prefix') and each.get('source'):
                command = 'no ip igmp static-oif {0} source {1} '.format(
                    each.get('prefix'), each.get('source')
                    )
            elif each.get('prefix'):
                command = 'no ip igmp static-oif {0}'.format(
                    each.get('prefix')
                    )
            if command:
                commands.append(command)
            command = None

    return commands


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


def main():
    argument_spec = dict(
            interface=dict(required=True, type='str'),
            version=dict(required=False, type='str'),
            startup_query_interval=dict(required=False, type='str'),
            startup_query_count=dict(required=False, type='str'),
            robustness=dict(required=False, type='str'),
            querier_timeout=dict(required=False, type='str'),
            query_mrt=dict(required=False, type='str'),
            query_interval=dict(required=False, type='str'),
            last_member_qrt=dict(required=False, type='str'),
            last_member_query_count=dict(required=False, type='str'),
            group_timeout=dict(required=False, type='str'),
            report_llg=dict(type='bool'),
            immediate_leave=dict(type='bool'),
            oif_routemap=dict(required=False, type='str'),
            oif_prefix=dict(required=False, type='str'),
            oif_source=dict(required=False, type='str'),
            restart=dict(type='bool', default=False),
            state=dict(choices=['present', 'absent', 'default'],
                       default='present'),
            include_defaults=dict(default=True)
    )
    argument_spec.update(nxos_argument_spec)
    module = get_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    state = module.params['state']
    interface = module.params['interface']
    oif_prefix = module.params['oif_prefix']
    oif_source = module.params['oif_source']
    oif_routemap = module.params['oif_routemap']

    if oif_source:
        if not oif_prefix:
            module.fail_json(msg='oif_prefix required when setting oif_source')

    intf_type = get_interface_type(interface)
    if get_interface_mode(interface, intf_type, module) == 'layer2':
        module.fail_json(msg='this module only works on Layer 3 interfaces')

    if oif_prefix and oif_routemap:
        module.fail_json(msg='cannot use oif_prefix AND oif_routemap.'
                             '  select one.')

    existing = get_igmp_interface(module, interface)
    existing_copy = existing.copy()
    end_state = existing_copy

    if not existing.get('version'):
        module.fail_json(msg='pim needs to be enabled on the interface')

    existing_oif_prefix_source = existing.get('oif_prefix_source')
    # not json serializable
    existing.pop('oif_prefix_source')

    if oif_routemap and existing_oif_prefix_source:
        module.fail_json(msg='Delete static-oif configurations on this '
                             'interface if you want to use a routemap')

    if oif_prefix and existing.get('oif_routemap'):
        module.fail_json(msg='Delete static-oif route-map configuration '
                             'on this interface if you want to config '
                             'static entries')

    args = [
        'version',
        'startup_query_interval',
        'startup_query_count',
        'robustness',
        'querier_timeout',
        'query_mrt',
        'query_interval',
        'last_member_qrt',
        'last_member_query_count',
        'group_timeout',
        'report_llg',
        'immediate_leave',
        'oif_routemap',
        'oif_prefix',
        'oif_source'
    ]

    changed = False
    commands = []
    proposed = dict((k, v) for k, v in module.params.iteritems()
                     if v is not None and k in args)

    CANNOT_ABSENT = ['version', 'startup_query_interval',
                     'startup_query_count', 'robustness', 'querier_timeout',
                     'query_mrt', 'query_interval', 'last_member_qrt',
                     'last_member_query_count', 'group_timeout', 'report_llg',
                     'immediate_leave']

    if state == 'absent':
        for each in CANNOT_ABSENT:
            if each in proposed:
                module.fail_json(msg='only params: oif_prefix, oif_source, '
                                     'oif_routemap can be used when '
                                     'state=absent')

    # delta check for all params except oif_prefix and oif_source
    delta = dict(set(proposed.iteritems()).difference(existing.iteritems()))

    # now check to see there is a delta for prefix and source command option
    found_both = False
    found_prefix = False

    if existing_oif_prefix_source:
        if oif_prefix and oif_source:
            for each in existing_oif_prefix_source:
                if (oif_prefix == each.get('prefix') and
                        oif_source == each.get('source')):
                    found_both = True
            if not found_both:
                delta['prefix'] = oif_prefix
                delta['source'] = oif_source
        elif oif_prefix:
            for each in existing_oif_prefix_source:
                if oif_prefix == each.get('prefix') and not each.get('source'):
                    found_prefix = True
            if not found_prefix:
                delta['prefix'] = oif_prefix

    if state == 'present':
        if delta:
            command = config_igmp_interface(delta, found_both, found_prefix)
            if command:
                commands.append(command)

    elif state == 'default':
        command = config_default_igmp_interface(existing, delta,
                                                found_both, found_prefix)
        if command:
            commands.append(command)
    elif state == 'absent':
        command = None
        if existing.get('oif_routemap') or existing_oif_prefix_source:
            command = config_remove_oif(existing, existing_oif_prefix_source)

        if command:
            commands.append(command)

        command = config_default_igmp_interface(existing, delta,
                                                found_both, found_prefix)
        if command:
            commands.append(command)

    if module.params['restart']:
        commands.append('restart igmp')

    cmds = []
    results = {}
    if commands:
        commands.insert(0, ['interface {0}'.format(interface)])
        cmds = flatten_list(commands)

        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            execute_config_command(cmds, module)
            changed = True
            end_state = get_igmp_interface(module, interface)
            if 'configure' in cmds:
                cmds.pop(0)

    results['proposed'] = proposed
    results['existing'] = existing_copy
    results['updates'] = cmds
    results['changed'] = changed
    results['end_state'] = end_state

    module.exit_json(**results)


if __name__ == '__main__':
    main()
