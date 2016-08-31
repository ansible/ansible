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
module: nxos_bgp
version_added: "2.2"
short_description: Manages BGP configuration
description:
    - Manages BGP configurations on NX-OS switches
author: Jason Edelman (@jedelman8), Gabriele Gerbino (@GGabriele)
extends_documentation_fragment: nxos
notes:
    - State 'absent' removes the whole BGP ASN configuration when VRF is
      'default' or the whole VRF instance within the BGP process when using
      a different VRF.
    - 'default', when supported, restores params default value.
    - Configuring global parmas is only permitted if VRF is 'default'.
options:
    asn:
        description:
            - BGP autonomous system number. Valid values are String,
              Integer in ASPLAIN or ASDOT notation.
        required: true
    vrf:
        description:
            - Name of the VRF. The name 'default' is a valid VRF representing the global BGP.
        required: false
        default: null
    bestpath_always_compare_med:
        description:
            - Enable/Disable MED comparison on paths from different autonomous systems.
        required: false
        choices: ['true','false', 'default']
        default: null
    bestpath_aspath_multipath_relax:
        description:
            - Enable/Disable load sharing across the providers with
              different (but equal-length) AS paths.
        required: false
        choices: ['true','false', 'default']
        default: null
    bestpath_compare_routerid:
        description:
            - Enable/Disable comparison of router IDs for identical eBGP paths.
        required: false
        choices: ['true','false', 'default']
        default: null
    bestpath_cost_community_ignore:
        description:
            - Enable/Disable Ignores the cost community for BGP best-path
              calculations.
        required: false
        choices: ['true','false', 'default']
        default: null
    bestpath_med_confed:
        description:
            - Enable/Disable enforcement of bestpath to do a MED comparison
              only between paths originated within a confederation.
        required: false
        choices: ['true','false', 'default']
        default: null
    bestpath_med_missing_as_worst:
        description:
            - Enable/Disable assigns the value of infinity to received routes that
              do not carry the MED attribute, making these routes the least desirable.
        required: false
        choices: ['true','false', 'default']
        default: null
    bestpath_med_non_deterministic:
        description:
            - Enable/Disable deterministic selection of the best MED path from among
              the paths from the same autonomous system.
        required: false
        choices: ['true','false', 'default']
        default: null
    cluster_id:
        description:
            - Route Reflector Cluster-ID.
        required: false
        default: null
    confederation_id:
        description:
            - Routing domain confederation AS.
        required: false
        default: null
    confederation_peers:
        description:
            - AS confederation parameters.
        required: false
        default: null
    disable_policy_batching:
        description:
            - Enable/Disable the batching evaluation of prefix advertisements to all peers.
        required: false
        choices: ['true','false', 'default']
        default: null
    disable_policy_batching_ipv4_prefix_list:
        description:
            - Enable/Disable the batching evaluation of prefix advertisements to all
              peers with prefix list.
        required: false
        default: null
    disable_policy_batching_ipv6_prefix_list:
        description:
            - Enable/Disable the batching evaluation of prefix advertisements to all peers with prefix list.
        required: false
    enforce_first_as:
        description:
            - Enable/Disable enforces the neighbor autonomous system to be the first AS number
              listed in the AS path attribute for eBGP.  On NX-OS, this property is only supported
              in the global BGP context.
        required: false
        choices: ['true','false', 'default']
        default: null
    event_history_cli:
        description:
            - Enable/Disable cli event history buffer.
        required: false
        choices: ['size_small', 'size_medium', 'size_large', 'size_disable', 'default']
        default: null
    event_history_detail:
        description:
            - Enable/Disable detail event history buffer.
        required: false
        choices: ['size_small', 'size_medium', 'size_large', 'size_disable', 'default']
        default: null
    event_history_events:
        description:
            - Enable/Disable event history buffer.
        required: false
        choices: ['size_small', 'size_medium', 'size_large', 'size_disable', 'default']
        default: null
    event_history_periodic:
        description:
            - Enable/Disable periodic event history buffer.
        required: false
        choices: ['size_small', 'size_medium', 'size_large', 'size_disable', 'default']
    fast_external_fallover:
        description:
            - Enable/Disable immediately reset the session if the link to a
              directly connected BGP peer goes down.  Only supported in the global BGP context.
        required: false
        choices: ['true','false', 'default']
        default: null
    flush_routes:
        description:
            - Enable/Disable flush routes in RIB upon controlled restart.
              On NX-OS, this property is only supported in the global BGP context.
        required: false
        choices: ['true','false', 'default']
        default: null
    graceful_restart:
        description:
            - Enable/Disable graceful restart.
        required: false
        choices: ['true','false', 'default']
        default: null
    graceful_restart_helper:
        description:
            - Enable/Disable graceful restart helper mode.
        required: false
        choices: ['true','false', 'default']
        default: null
    graceful_restart_timers_restart:
        description:
            - Set maximum time for a restart sent to the BGP peer.
        required: false
        choices: ['true','false', 'default']
        default: null
    graceful_restart_timers_stalepath_time:
        description:
            - Set maximum time that BGP keeps the stale routes from the restarting BGP peer.
        choices: ['true','false', 'default']
        default: null
    isolate:
        description:
            - Enable/Disable isolate this router from BGP perspective.
        required: false
        choices: ['true','false', 'default']
        default: null
    local_as:
        description:
            - Local AS number to be used within a VRF instance.
        required: false
        default: null
    log_neighbor_changes:
        description:
            - Enable/Disable message logging for neighbor up/down event.
        required: false
        choices: ['true','false', 'default']
        default: null
    maxas_limit:
        description:
            - Specify Maximum number of AS numbers allowed in the AS-path attribute
              Valid values are between 1 and 512.
        required: false
        default: null
    neighbor_down_fib_accelerate:
        description:
            - Enable/Disable handle BGP neighbor down event, due to various reasons.
        required: false
        choices: ['true','false', 'default']
        default: null
    reconnect_interval:
        description:
            - The BGP reconnection interval for dropped sessions.  1 - 60.
        required: false
        default: null
    router_id:
        description:
            - Router Identifier (ID) of the BGP router VRF instance.
        required: false
        default: null
    shutdown:
        description:
            - Administratively shutdown the BGP protocol.
        required: false
        choices: ['true','false', 'default']
        default: null
    suppress_fib_pending:
        description:
            - Enable/Disable advertise only routes programmed in hardware to peers.
        required: false
        choices: ['true','false', 'default']
        default: null
    timer_bestpath_limit:
        description:
            - Specify timeout for the first best path after a restart, in seconds.
        required: false
        default: null
    timer_bestpath_limit_always:
        description:
            - Enable/Disable update-delay-always option.
        required: false
        choices: ['true','false', 'default']
        default: null
    timer_bgp_hold:
        description:
            - Set bgp hold timer
        required: false
        default: null
    timer_bgp_keepalive:
        description:
            - Set bgp keepalive timer.
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
# configure a simple asn
- nxos_bgp:
      asn=65535
      vrf=default
      state=present
      transport=cli
'''

# COMMON CODE FOR MIGRATION

import re
import time
import collections
import itertools
import shlex
import itertools

from ansible.module_utils.basic import BOOLEANS_TRUE, BOOLEANS_FALSE

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
                string = item.text if ignore_whitespace is True else item.raw
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

def get_config(module):
    config = module.params['running_config']
    if not config:
        config = module.get_config()
    return CustomNetworkConfig(indent=2, contents=config)

def load_config(module, candidate):
    config = get_config(module)

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

import re

WARNINGS = []
BOOLEANS_TRUE = ['yes', 'on', '1', 'true', 'True', 1, True]
BOOLEANS_FALSE = ['no', 'off', '0', 'false', 'False', 0, False]
ACCEPTED = BOOLEANS_TRUE + BOOLEANS_FALSE + ['default']
BOOL_PARAMS = [
    'bestpath_always_compare_med',
    'bestpath_aspath_multipath_relax',
    'bestpath_compare_neighborid',
    'bestpath_compare_routerid',
    'bestpath_cost_community_ignore',
    'bestpath_med_confed',
    'bestpath_med_missing_as_worst',
    'bestpath_med_non_deterministic',
    'disable_policy_batching',
    'enforce_first_as',
    'fast_external_fallover',
    'flush_routes',
    'graceful_restart',
    'graceful_restart_helper',
    'isolate',
    'log_neighbor_changes',
    'neighbor_down_fib_accelerate',
    'shutdown',
    'suppress_fib_pending'
]
GLOBAL_PARAMS = [
    'disable_policy_batching',
    'disable_policy_batching_ipv4_prefix_list',
    'disable_policy_batching_ipv6_prefix_list',
    'enforce_first_as',
    'event_history_cli',
    'event_history_detail',
    'event_history_events',
    'event_history_periodic',
    'fast_external_fallover',
    'flush_routes',
    'isolate',
    'shutdown'
]
PARAM_TO_DEFAULT_KEYMAP = {
    'timer_bgp_keepalive': '60',
    'timer_bgp_hold': '180',
    'graceful_restart': True,
    'graceful_restart_timers_restart': '120',
    'graceful_restart_timers_stalepath_time': '300',
    'reconnect_interval': '60',
    'suppress_fib_pending': True,
    'fast_external_fallover': True,
    'enforce_first_as': True,
    'event_history_periodic': True,
    'event_history_cli': True,
    'event_history_events': True
}
PARAM_TO_COMMAND_KEYMAP = {
    'asn': 'router bgp',
    'bestpath_always_compare_med': 'bestpath always-compare-med',
    'bestpath_aspath_multipath_relax': 'bestpath as-path multipath-relax',
    'bestpath_compare_neighborid': 'bestpath compare-neighborid',
    'bestpath_compare_routerid': 'bestpath compare-routerid',
    'bestpath_cost_community_ignore': 'bestpath cost-community ignore',
    'bestpath_med_confed': 'bestpath med confed',
    'bestpath_med_missing_as_worst': 'bestpath med missing-as-worst',
    'bestpath_med_non_deterministic': 'bestpath med non-deterministic',
    'cluster_id': 'cluster-id',
    'confederation_id': 'confederation identifier',
    'confederation_peers': 'confederation peers',
    'disable_policy_batching': 'disable-policy-batching',
    'disable_policy_batching_ipv4_prefix_list': 'disable-policy-batching ipv4 prefix-list',
    'disable_policy_batching_ipv6_prefix_list': 'disable-policy-batching ipv6 prefix-list',
    'enforce_first_as': 'enforce-first-as',
    'event_history_cli': 'event-history cli',
    'event_history_detail': 'event-history detail',
    'event_history_events': 'event-history events',
    'event_history_periodic': 'event-history periodic',
    'fast_external_fallover': 'fast-external-fallover',
    'flush_routes': 'flush-routes',
    'graceful_restart': 'graceful-restart',
    'graceful_restart_helper': 'graceful-restart-helper',
    'graceful_restart_timers_restart': 'graceful-restart restart-time',
    'graceful_restart_timers_stalepath_time': 'graceful-restart stalepath-time',
    'isolate': 'isolate',
    'local_as': 'local-as',
    'log_neighbor_changes': 'log-neighbor-changes',
    'maxas_limit': 'maxas-limit',
    'neighbor_down_fib_accelerate': 'neighbor-down fib-accelerate',
    'reconnect_interval': 'reconnect-interval',
    'router_id': 'router-id',
    'shutdown': 'shutdown',
    'suppress_fib_pending': 'suppress-fib-pending',
    'timer_bestpath_limit': 'timers bestpath-limit',
    'timer_bgp_hold': 'timers bgp',
    'timer_bgp_keepalive': 'timers bgp',
    'vrf': 'vrf'
}


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def get_custom_value(config, arg):
    if arg.startswith('event_history'):
        REGEX_SIZE = re.compile(r'(?:{0} size\s)(?P<value>.*)$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        REGEX = re.compile(r'\s+{0}\s*$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        value = False

        if 'no {0}'.format(PARAM_TO_COMMAND_KEYMAP[arg]) in config:
            pass
        elif PARAM_TO_COMMAND_KEYMAP[arg] in config:
            try:
                value = REGEX_SIZE.search(config).group('value')
            except AttributeError:
                if REGEX.search(config):
                    value = True

    elif arg == 'confederation_peers':
        REGEX = re.compile(r'(?:confederation peers\s)(?P<value>.*)$', re.M)
        value = ''
        if 'confederation peers' in config:
            value = REGEX.search(config).group('value').split()

    elif arg == 'timer_bgp_keepalive':
        REGEX = re.compile(r'(?:timers bgp\s)(?P<value>.*)$', re.M)
        value = ''
        if 'timers bgp' in config:
            parsed = REGEX.search(config).group('value').split()
            value = parsed[0]

    elif arg == 'timer_bgp_hold':
        REGEX = re.compile(r'(?:timers bgp\s)(?P<value>.*)$', re.M)
        value = ''
        if 'timers bgp' in config:
            parsed = REGEX.search(config).group('value').split()
            if len(parsed) == 2:
                value = parsed[1]

    return value


def get_value(arg, config):
    custom = [
        'event_history_cli',
        'event_history_events',
        'event_history_periodic',
        'event_history_detail',
        'confederation_peers',
        'timer_bgp_hold',
        'timer_bgp_keepalive'
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
        value = get_custom_value(config, arg)
    else:
        REGEX = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        value = ''
        if PARAM_TO_COMMAND_KEYMAP[arg] in config:
            value = REGEX.search(config).group('value')
    return value


def get_existing(module, args):
    existing = {}
    netcfg = get_config(module)

    try:
        asn_regex = '.*router\sbgp\s(?P<existing_asn>\d+).*'
        match_asn = re.match(asn_regex, str(netcfg), re.DOTALL)
        existing_asn_group = match_asn.groupdict()
        existing_asn = existing_asn_group['existing_asn']
    except AttributeError:
        existing_asn = ''

    if existing_asn:
        bgp_parent = 'router bgp {0}'.format(existing_asn)
        if module.params['vrf'] != 'default':
            parents = [bgp_parent, 'vrf {0}'.format(module.params['vrf'])]
        else:
            parents = bgp_parent

        config = netcfg.get_section(parents)
        if config:
            for arg in args:
                if arg != 'asn':
                    if module.params['vrf'] != 'default':
                        if arg not in GLOBAL_PARAMS:
                            existing[arg] = get_value(arg, config)
                    else:
                        existing[arg] = get_value(arg, config)

            existing['asn'] = existing_asn
            if module.params['vrf'] == 'default':
                existing['vrf'] = 'default'
        else:
            if (module.params['state'] == 'present' and
                    module.params['vrf'] != 'default'):
                msg = ("VRF {0} doesn't exist. ".format(module.params['vrf']))
                WARNINGS.append(msg)
    else:
        if (module.params['state'] == 'present' and
                module.params['vrf'] != 'default'):
            msg = ("VRF {0} doesn't exist. ".format(module.params['vrf']))
            WARNINGS.append(msg)

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
            if key in PARAM_TO_DEFAULT_KEYMAP.keys():
                commands.append('{0} {1}'.format(key, PARAM_TO_DEFAULT_KEYMAP[key]))
            elif existing_commands.get(key):
                existing_value = existing_commands.get(key)
                if key == 'confederation peers':
                    commands.append('no {0} {1}'.format(key, ' '.join(existing_value)))
                else:
                    commands.append('no {0} {1}'.format(key, existing_value))
            else:
                if key.replace(' ', '_').replace('-', '_') in BOOL_PARAMS:
                    commands.append('no {0}'.format(key))
        else:
            if key == 'confederation peers':
                existing_confederation_peers = existing.get('confederation_peers')

                if existing_confederation_peers:
                    if not isinstance(existing_confederation_peers, list):
                        existing_confederation_peers = [existing_confederation_peers]
                else:
                    existing_confederation_peers = []

                values = value.split()
                for each_value in values:
                    if each_value not in existing_confederation_peers:
                        existing_confederation_peers.append(each_value)
                peer_string = ' '.join(existing_confederation_peers)
                commands.append('{0} {1}'.format(key, peer_string))
            elif key.startswith('timers bgp'):
                command = 'timers bgp {0} {1}'.format(
                                            proposed['timer_bgp_keepalive'],
                                            proposed['timer_bgp_hold'])
                if command not in commands:
                    commands.append(command)
            else:
                if value.startswith('size'):
                    value = value.replace('_', ' ')
                command = '{0} {1}'.format(key, value)
                commands.append(command)

    if commands:
        commands = fix_commands(commands)
        parents = ['router bgp {0}'.format(module.params['asn'])]
        if module.params['vrf'] != 'default':
            parents.append('vrf {0}'.format(module.params['vrf']))
        candidate.add(commands, parents=parents)
    else:
        if len(proposed.keys()) == 0:
            if module.params['vrf'] != 'default':
                commands.append('vrf {0}'.format(module.params['vrf']))
                parents = ['router bgp {0}'.format(module.params['asn'])]
            else:
                commands.append('router bgp {0}'.format(module.params['asn']))
                parents = []
            candidate.add(commands, parents=parents)


def state_absent(module, existing, proposed,  candidate):
    commands = []
    parents = []
    if module.params['vrf'] == 'default':
        commands.append('no router bgp {0}'.format(module.params['asn']))
    else:
        if existing.get('vrf') == module.params['vrf']:
            commands.append('no vrf {0}'.format(module.params['vrf']))
            parents = ['router bgp {0}'.format(module.params['asn'])]

    candidate.add(commands, parents=parents)


def fix_commands(commands):
    local_as_command = ''
    confederation_id_command = ''
    confederation_peers_command = ''

    for command in commands:
        if 'local-as' in command:
            local_as_command = command
        elif 'confederation identifier' in command:
            confederation_id_command = command
        elif 'confederation peers' in command:
            confederation_peers_command = command

    if local_as_command and confederation_id_command:
        commands.pop(commands.index(local_as_command))
        commands.pop(commands.index(confederation_id_command))
        commands.append(local_as_command)
        commands.append(confederation_id_command)

    elif confederation_peers_command and confederation_id_command:
        commands.pop(commands.index(confederation_peers_command))
        commands.pop(commands.index(confederation_id_command))
        commands.append(confederation_id_command)
        commands.append(confederation_peers_command)

    return commands


def main():
    argument_spec = dict(
            asn=dict(required=True, type='str'),
            vrf=dict(required=False, type='str', default='default'),
            bestpath_always_compare_med=dict(required=False, choices=ACCEPTED),
            bestpath_aspath_multipath_relax=dict(required=False, choices=ACCEPTED),
            bestpath_compare_neighborid=dict(required=False, choices=ACCEPTED),
            bestpath_compare_routerid=dict(required=False, choices=ACCEPTED),
            bestpath_cost_community_ignore=dict(required=False, choices=ACCEPTED),
            bestpath_med_confed=dict(required=False, choices=ACCEPTED),
            bestpath_med_missing_as_worst=dict(required=False, choices=ACCEPTED),
            bestpath_med_non_deterministic=dict(required=False, choices=ACCEPTED),
            cluster_id=dict(required=False, type='str'),
            confederation_id=dict(required=False, type='str'),
            confederation_peers=dict(required=False, type='str'),
            disable_policy_batching=dict(required=False, choices=ACCEPTED),
            disable_policy_batching_ipv4_prefix_list=dict(required=False, type='str'),
            disable_policy_batching_ipv6_prefix_list=dict(required=False, type='str'),
            enforce_first_as=dict(required=False, choices=ACCEPTED),
            event_history_cli=dict(required=False, choices=['true', 'false', 'default', 'size_small', 'size_medium', 'size_large', 'size_disable']),
            event_history_detail=dict(required=False, choices=['true', 'false', 'default', 'size_small', 'size_medium', 'size_large', 'size_disable']),
            event_history_events=dict(required=False, choices=['true', 'false', 'default' 'size_small', 'size_medium', 'size_large', 'size_disable']),
            event_history_periodic=dict(required=False, choices=['true', 'false', 'default', 'size_small', 'size_medium', 'size_large', 'size_disable']),
            fast_external_fallover=dict(required=False, choices=ACCEPTED),
            flush_routes=dict(required=False, choices=ACCEPTED),
            graceful_restart=dict(required=False, choices=ACCEPTED),
            graceful_restart_helper=dict(required=False, choices=ACCEPTED),
            graceful_restart_timers_restart=dict(required=False, type='str'),
            graceful_restart_timers_stalepath_time=dict(required=False, type='str'),
            isolate=dict(required=False, choices=ACCEPTED),
            local_as=dict(required=False, type='str'),
            log_neighbor_changes=dict(required=False, choices=ACCEPTED),
            maxas_limit=dict(required=False, type='str'),
            neighbor_down_fib_accelerate=dict(required=False, choices=ACCEPTED),
            reconnect_interval=dict(required=False, type='str'),
            router_id=dict(required=False, type='str'),
            shutdown=dict(required=False, choices=ACCEPTED),
            suppress_fib_pending=dict(required=False, choices=ACCEPTED),
            timer_bestpath_limit=dict(required=False, type='str'),
            timer_bgp_hold=dict(required=False, type='str'),
            timer_bgp_keepalive=dict(required=False, type='str'),
            m_facts=dict(required=False, default=False, type='bool'),
            state=dict(choices=['present', 'absent'], default='present',
                       required=False),
            include_defaults=dict(default=True)
    )
    argument_spec.update(nxos_argument_spec)
    module = get_module(argument_spec=argument_spec,
                        required_together=[['timer_bgp_hold',
                                            'timer_bgp_keepalive']],
                        supports_check_mode=True)

    state = module.params['state']
    args =  [
            "asn",
            "bestpath_always_compare_med",
            "bestpath_aspath_multipath_relax",
            "bestpath_compare_neighborid",
            "bestpath_compare_routerid",
            "bestpath_cost_community_ignore",
            "bestpath_med_confed",
            "bestpath_med_missing_as_worst",
            "bestpath_med_non_deterministic",
            "cluster_id",
            "confederation_id",
            "confederation_peers",
            "disable_policy_batching",
            "disable_policy_batching_ipv4_prefix_list",
            "disable_policy_batching_ipv6_prefix_list",
            "enforce_first_as",
            "event_history_cli",
            "event_history_detail",
            "event_history_events",
            "event_history_periodic",
            "fast_external_fallover",
            "flush_routes",
            "graceful_restart",
            "graceful_restart_helper",
            "graceful_restart_timers_restart",
            "graceful_restart_timers_stalepath_time",
            "isolate",
            "local_as",
            "log_neighbor_changes",
            "maxas_limit",
            "neighbor_down_fib_accelerate",
            "reconnect_interval",
            "router_id",
            "shutdown",
            "suppress_fib_pending",
            "timer_bestpath_limit",
            "timer_bgp_hold",
            "timer_bgp_keepalive",
            "vrf"
        ]

    if module.params['vrf'] != 'default':
        for param, inserted_value in module.params.iteritems():
            if param in GLOBAL_PARAMS and inserted_value:
                module.fail_json(msg='Global params can be modifed only'
                                     ' under "default" VRF.',
                                     vrf=module.params['vrf'],
                                     global_param=param)

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
    proposed = {}
    for key, value in proposed_args.iteritems():
        if key != 'asn' and key != 'vrf':
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.lower() == 'default':
                value = PARAM_TO_DEFAULT_KEYMAP.get(key)
                if value is None:
                    if key in BOOL_PARAMS:
                        value = False
                    else:
                        value = 'default'
            if existing.get(key) or (not existing.get(key) and value):
                proposed[key] = value

    result = {}
    if (state == 'present' or (state == 'absent' and
            existing.get('asn') == module.params['asn'])):
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


from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
from ansible.module_utils.shell import *
from ansible.module_utils.netcfg import *
from ansible.module_utils.nxos import *
if __name__ == '__main__':
    main()
