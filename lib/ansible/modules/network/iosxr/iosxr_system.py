#!/usr/bin/python
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: iosxr_system
version_added: "2.3"
author:
  - "Peter Sprygada (@privateip)"
  - "Kedar Kekan @kedarX"
short_description: Manage the system attributes on Cisco IOS XR devices
description:
  - This module provides declarative management of node system attributes
    on Cisco IOS XR devices. It provides an option to configure host system
    parameters or remove those parameters from the device active
    configuration.
extends_documentation_fragment: iosxr
notes:
  - Tested against IOS XRv 6.1.2
  - name-servers I(state=absent) operation with C(netconf) transport is a success, but with rpc-error. This is
    due to XR platform issue. Recommended to use I(ignore_errors) option with the task as a workaround.
options:
  hostname:
    description:
      - Configure the device hostname parameter. This option takes an ASCII string value.
  vrf:
    description:
      - VRF name for domain services
    version_added: 2.5
  domain_name:
    description:
      - Configure the IP domain name
        on the remote device to the provided value. Value
        should be in the dotted name form and will be
        appended to the C(hostname) to create a fully-qualified
        domain name.
  domain_search:
    description:
      - Provides the list of domain suffixes to
        append to the hostname for the purpose of doing name resolution.
        This argument accepts a list of names and will be reconciled
        with the current active configuration on the running node.
  lookup_source:
    description:
      - The C(lookup_source) argument provides one or more source
        interfaces to use for performing DNS lookups.  The interface
        provided in C(lookup_source) must be a valid interface configured
        on the device.
  lookup_enabled:
    description:
      - Provides administrative control
        for enabling or disabling DNS lookups.  When this argument is
        set to True, lookups are performed and when it is set to False,
        lookups are not performed.
    type: bool
  name_servers:
    description:
      - The C(name_serves) argument accepts a list of DNS name servers by
        way of either FQDN or IP address to use to perform name resolution
        lookups.  This argument accepts wither a list of DNS servers See
        examples.
  state:
    description:
      - State of the configuration
        values in the device's current active configuration.  When set
        to I(present), the values should be configured in the device active
        configuration and when set to I(absent) the values should not be
        in the device active configuration
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure hostname and domain-name (default vrf=default)
  iosxr_system:
    hostname: iosxr01
    domain_name: test.example.com
    domain-search:
      - ansible.com
      - redhat.com
      - cisco.com
- name: remove configuration
  iosxr_system:
    hostname: iosxr01
    domain_name: test.example.com
    domain-search:
      - ansible.com
      - redhat.com
      - cisco.com
    state: absent
- name: configure hostname and domain-name with vrf
  iosxr_system:
    hostname: iosxr01
    vrf: nondefault
    domain_name: test.example.com
    domain-search:
      - ansible.com
      - redhat.com
      - cisco.com
- name: configure DNS lookup sources
  iosxr_system:
    lookup_source: MgmtEth0/0/CPU0/0
    lookup_enabled: True
- name: configure name servers
  iosxr_system:
    name_servers:
      - 8.8.8.8
      - 8.8.4.4
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - hostname iosxr01
    - ip domain-name test.example.com
xml:
  description: NetConf rpc xml sent to device with transport C(netconf)
  returned: always (empty list when no xml rpc to send)
  type: list
  version_added: 2.5
  sample:
    - '<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <ip-domain xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ip-domain-cfg">
    <vrfs>
    <vrf>
    <vrf-name>default</vrf-name>
    <lists>
    <list xc:operation="merge">
    <order>0</order>
    <list-name>redhat.com</list-name>
    </list>
    </lists>
    </vrf>
    </vrfs>
    </ip-domain>
    </config>'
"""

import re
import collections

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.iosxr.iosxr import get_config, load_config, etree_findall
from ansible.module_utils.network.iosxr.iosxr import is_cliconf, is_netconf, etree_find
from ansible.module_utils.network.iosxr.iosxr import iosxr_argument_spec, build_xml


def diff_list(want, have):
    adds = set(want).difference(have)
    removes = set(have).difference(want)
    return (adds, removes)


class ConfigBase(object):
    def __init__(self, module):
        self._module = module
        self._result = {'changed': False, 'warnings': []}
        self._want = dict()
        self._have = dict()

    def map_params_to_obj(self):
        self._want.update({
            'hostname': self._module.params['hostname'],
            'vrf': self._module.params['vrf'],
            'domain_name': self._module.params['domain_name'],
            'domain_search': self._module.params['domain_search'],
            'lookup_source': self._module.params['lookup_source'],
            'lookup_enabled': self._module.params['lookup_enabled'],
            'name_servers': self._module.params['name_servers']
        })


class CliConfiguration(ConfigBase):
    def __init__(self, module):
        super(CliConfiguration, self).__init__(module)

    def map_obj_to_commands(self):
        commands = list()
        state = self._module.params['state']

        def needs_update(x):
            return self._want.get(x) and (self._want.get(x) != self._have.get(x))

        if state == 'absent':
            if self._have['hostname'] != 'ios':
                commands.append('no hostname')
            if self._have['domain_name']:
                commands.append('no domain name')
            if self._have['lookup_source']:
                commands.append('no domain lookup source-interface {0!s}'.format(self._have['lookup_source']))
            if not self._have['lookup_enabled']:
                commands.append('no domain lookup disable')
            for item in self._have['name_servers']:
                commands.append('no domain name-server {0!s}'.format(item))
            for item in self._have['domain_search']:
                commands.append('no domain list {0!s}'.format(item))

        elif state == 'present':
            if needs_update('hostname'):
                commands.append('hostname {0!s}'.format(self._want['hostname']))

            if needs_update('domain_name'):
                commands.append('domain name {0!s}'.format(self._want['domain_name']))

            if needs_update('lookup_source'):
                commands.append('domain lookup source-interface {0!s}'.format(self._want['lookup_source']))

            cmd = None
            if not self._want['lookup_enabled'] and self._have['lookup_enabled']:
                cmd = 'domain lookup disable'
            elif self._want['lookup_enabled'] and not self._have['lookup_enabled']:
                cmd = 'no domain lookup disable'
            if cmd is not None:
                commands.append(cmd)

            if self._want['name_servers'] is not None:
                adds, removes = diff_list(self._want['name_servers'], self._have['name_servers'])
                for item in adds:
                    commands.append('domain name-server {0!s}'.format(item))
                for item in removes:
                    commands.append('no domain name-server {0!s}'.format(item))

            if self._want['domain_search'] is not None:
                adds, removes = diff_list(self._want['domain_search'], self._have['domain_search'])
                for item in adds:
                    commands.append('domain list {0!s}'.format(item))
                for item in removes:
                    commands.append('no domain list {0!s}'.format(item))

        self._result['commands'] = []
        if commands:
            commit = not self._module.check_mode
            diff = load_config(self._module, commands, commit=commit)
            if diff:
                self._result['diff'] = dict(prepared=diff)

            self._result['commands'] = commands
            self._result['changed'] = True

    def parse_hostname(self, config):
        match = re.search(r'^hostname (\S+)', config, re.M)
        if match:
            return match.group(1)

    def parse_domain_name(self, config):
        match = re.search(r'^domain name (\S+)', config, re.M)
        if match:
            return match.group(1)

    def parse_lookup_source(self, config):
        match = re.search(r'^domain lookup source-interface (\S+)', config, re.M)
        if match:
            return match.group(1)

    def map_config_to_obj(self):
        config = get_config(self._module)
        self._have.update({
            'hostname': self.parse_hostname(config),
            'domain_name': self.parse_domain_name(config),
            'domain_search': re.findall(r'^domain list (\S+)', config, re.M),
            'lookup_source': self.parse_lookup_source(config),
            'lookup_enabled': 'domain lookup disable' not in config,
            'name_servers': re.findall(r'^domain name-server (\S+)', config, re.M)
        })

    def run(self):
        self.map_params_to_obj()
        self.map_config_to_obj()
        self.map_obj_to_commands()

        return self._result


class NCConfiguration(ConfigBase):
    def __init__(self, module):
        super(NCConfiguration, self).__init__(module)
        self._system_meta = collections.OrderedDict()
        self._system_domain_meta = collections.OrderedDict()
        self._system_server_meta = collections.OrderedDict()
        self._hostname_meta = collections.OrderedDict()
        self._lookup_source_meta = collections.OrderedDict()
        self._lookup_meta = collections.OrderedDict()

    def map_obj_to_xml_rpc(self):
        self._system_meta.update([
            ('vrfs', {'xpath': 'ip-domain/vrfs', 'tag': True, 'operation': 'edit'}),
            ('vrf', {'xpath': 'ip-domain/vrfs/vrf', 'tag': True, 'operation': 'edit'}),
            ('a:vrf', {'xpath': 'ip-domain/vrfs/vrf/vrf-name', 'operation': 'edit'}),
            ('a:domain_name', {'xpath': 'ip-domain/vrfs/vrf/name', 'operation': 'edit', 'attrib': "operation"}),
        ])

        self._system_domain_meta.update([
            ('vrfs', {'xpath': 'ip-domain/vrfs', 'tag': True, 'operation': 'edit'}),
            ('vrf', {'xpath': 'ip-domain/vrfs/vrf', 'tag': True, 'operation': 'edit'}),
            ('a:vrf', {'xpath': 'ip-domain/vrfs/vrf/vrf-name', 'operation': 'edit'}),
            ('lists', {'xpath': 'ip-domain/vrfs/vrf/lists', 'tag': True, 'operation': 'edit'}),
            ('list', {'xpath': 'ip-domain/vrfs/vrf/lists/list', 'tag': True, 'operation': 'edit', 'attrib': "operation"}),
            ('a:order', {'xpath': 'ip-domain/vrfs/vrf/lists/list/order', 'operation': 'edit'}),
            ('a:domain_search', {'xpath': 'ip-domain/vrfs/vrf/lists/list/list-name', 'operation': 'edit'}),
        ])

        self._system_server_meta.update([
            ('vrfs', {'xpath': 'ip-domain/vrfs', 'tag': True, 'operation': 'edit'}),
            ('vrf', {'xpath': 'ip-domain/vrfs/vrf', 'tag': True, 'operation': 'edit'}),
            ('a:vrf', {'xpath': 'ip-domain/vrfs/vrf/vrf-name', 'operation': 'edit'}),
            ('servers', {'xpath': 'ip-domain/vrfs/vrf/servers', 'tag': True, 'operation': 'edit'}),
            ('server', {'xpath': 'ip-domain/vrfs/vrf/servers/server', 'tag': True, 'operation': 'edit', 'attrib': "operation"}),
            ('a:order', {'xpath': 'ip-domain/vrfs/vrf/servers/server/order', 'operation': 'edit'}),
            ('a:name_servers', {'xpath': 'ip-domain/vrfs/vrf/servers/server/server-address', 'operation': 'edit'}),
        ])

        self._hostname_meta.update([
            ('a:hostname', {'xpath': 'host-names/host-name', 'operation': 'edit', 'attrib': "operation"}),
        ])

        self._lookup_source_meta.update([
            ('vrfs', {'xpath': 'ip-domain/vrfs', 'tag': True, 'operation': 'edit'}),
            ('vrf', {'xpath': 'ip-domain/vrfs/vrf', 'tag': True, 'operation': 'edit'}),
            ('a:vrf', {'xpath': 'ip-domain/vrfs/vrf/vrf-name', 'operation': 'edit'}),
            ('a:lookup_source', {'xpath': 'ip-domain/vrfs/vrf/source-interface', 'operation': 'edit', 'attrib': "operation"}),
        ])

        self._lookup_meta.update([
            ('vrfs', {'xpath': 'ip-domain/vrfs', 'tag': True, 'operation': 'edit'}),
            ('vrf', {'xpath': 'ip-domain/vrfs/vrf', 'tag': True, 'operation': 'edit'}),
            ('a:vrf', {'xpath': 'ip-domain/vrfs/vrf/vrf-name', 'operation': 'edit'}),
            ('lookup', {'xpath': 'ip-domain/vrfs/vrf/lookup', 'tag': True, 'operation': 'edit', 'attrib': "operation"}),
        ])

        state = self._module.params['state']
        _get_filter = build_xml('ip-domain', opcode="filter")
        running = get_config(self._module, source='running', config_filter=_get_filter)
        _get_filter = build_xml('host-names', opcode="filter")
        hostname_runn = get_config(self._module, source='running', config_filter=_get_filter)

        hostname_ele = etree_find(hostname_runn, 'host-name')
        hostname = hostname_ele.text if hostname_ele is not None else None

        vrf_ele = etree_findall(running, 'vrf')
        vrf_map = {}
        for vrf in vrf_ele:
            name_server_list = list()
            domain_list = list()
            vrf_name_ele = etree_find(vrf, 'vrf-name')
            vrf_name = vrf_name_ele.text if vrf_name_ele is not None else None

            domain_name_ele = etree_find(vrf, 'name')
            domain_name = domain_name_ele.text if domain_name_ele is not None else None

            domain_ele = etree_findall(vrf, 'list-name')
            for domain in domain_ele:
                domain_list.append(domain.text)

            server_ele = etree_findall(vrf, 'server-address')
            for server in server_ele:
                name_server_list.append(server.text)

            lookup_source_ele = etree_find(vrf, 'source-interface')
            lookup_source = lookup_source_ele.text if lookup_source_ele is not None else None

            lookup_enabled = False if etree_find(vrf, 'lookup') is not None else True

            vrf_map[vrf_name] = {'domain_name': domain_name,
                                 'domain_search': domain_list,
                                 'name_servers': name_server_list,
                                 'lookup_source': lookup_source,
                                 'lookup_enabled': lookup_enabled}

        opcode = None
        hostname_param = {}
        lookup_param = {}
        system_param = {}
        sys_server_params = list()
        sys_domain_params = list()
        add_domain_params = list()
        del_domain_params = list()
        add_server_params = list()
        del_server_params = list()
        lookup_source_params = {}

        try:
            sys_node = vrf_map[self._want['vrf']]
        except KeyError:
            sys_node = {'domain_name': None,
                        'domain_search': [],
                        'name_servers': [],
                        'lookup_source': None,
                        'lookup_enabled': True}

        if state == 'absent':
            opcode = "delete"

            def needs_update(x):
                return self._want[x] is not None and self._want[x] == sys_node[x]

            if needs_update('domain_name'):
                system_param = {'vrf': self._want['vrf'], 'domain_name': self._want['domain_name']}

            if needs_update('hostname'):
                hostname_param = {'hostname': hostname}

            if not self._want['lookup_enabled'] and not sys_node['lookup_enabled']:
                lookup_param['vrf'] = self._want['vrf']

            if needs_update('lookup_source'):
                lookup_source_params['vrf'] = self._want['vrf']
                lookup_source_params['lookup_source'] = self._want['lookup_source']

            if self._want['domain_search']:
                domain_param = {}
                domain_param['domain_name'] = self._want['domain_name']
                domain_param['vrf'] = self._want['vrf']
                domain_param['order'] = '0'
                for domain in self._want['domain_search']:
                    if domain in sys_node['domain_search']:
                        domain_param['domain_search'] = domain
                        sys_domain_params.append(domain_param.copy())

            if self._want['name_servers']:
                server_param = {}
                server_param['vrf'] = self._want['vrf']
                server_param['order'] = '0'
                for server in self._want['name_servers']:
                    if server in sys_node['name_servers']:
                        server_param['name_servers'] = server
                        sys_server_params.append(server_param.copy())

        elif state == 'present':
            opcode = "merge"

            def needs_update(x):
                return self._want[x] is not None and (sys_node[x] is None or
                                                      (sys_node[x] is not None and self._want[x] != sys_node[x]))

            if needs_update('domain_name'):
                system_param = {'vrf': self._want['vrf'], 'domain_name': self._want['domain_name']}

            if self._want['hostname'] is not None and self._want['hostname'] != hostname:
                hostname_param = {'hostname': self._want['hostname']}

            if not self._want['lookup_enabled'] and sys_node['lookup_enabled']:
                lookup_param['vrf'] = self._want['vrf']

            if needs_update('lookup_source'):
                lookup_source_params['vrf'] = self._want['vrf']
                lookup_source_params['lookup_source'] = self._want['lookup_source']

            if self._want['domain_search']:
                domain_adds, domain_removes = diff_list(self._want['domain_search'], sys_node['domain_search'])
                domain_param = {}
                domain_param['domain_name'] = self._want['domain_name']
                domain_param['vrf'] = self._want['vrf']
                domain_param['order'] = '0'
                for domain in domain_adds:
                    if domain not in sys_node['domain_search']:
                        domain_param['domain_search'] = domain
                        add_domain_params.append(domain_param.copy())
                for domain in domain_removes:
                    if domain in sys_node['domain_search']:
                        domain_param['domain_search'] = domain
                        del_domain_params.append(domain_param.copy())

            if self._want['name_servers']:
                server_adds, server_removes = diff_list(self._want['name_servers'], sys_node['name_servers'])
                server_param = {}
                server_param['vrf'] = self._want['vrf']
                server_param['order'] = '0'
                for domain in server_adds:
                    if domain not in sys_node['name_servers']:
                        server_param['name_servers'] = domain
                        add_server_params.append(server_param.copy())
                for domain in server_removes:
                    if domain in sys_node['name_servers']:
                        server_param['name_servers'] = domain
                        del_server_params.append(server_param.copy())

        self._result['xml'] = []
        _edit_filter_list = list()
        if opcode:
            if hostname_param:
                _edit_filter_list.append(build_xml('host-names', xmap=self._hostname_meta,
                                                   params=hostname_param, opcode=opcode))

            if system_param:
                _edit_filter_list.append(build_xml('ip-domain', xmap=self._system_meta,
                                                   params=system_param, opcode=opcode))

            if lookup_source_params:
                _edit_filter_list.append(build_xml('ip-domain', xmap=self._lookup_source_meta,
                                                   params=lookup_source_params, opcode=opcode))
            if lookup_param:
                _edit_filter_list.append(build_xml('ip-domain', xmap=self._lookup_meta,
                                                   params=lookup_param, opcode=opcode))

            if opcode == 'delete':
                if sys_domain_params:
                    _edit_filter_list.append(build_xml('ip-domain', xmap=self._system_domain_meta,
                                                       params=sys_domain_params, opcode=opcode))
                if sys_server_params:
                    _edit_filter_list.append(build_xml('ip-domain', xmap=self._system_server_meta,
                                                       params=sys_server_params, opcode=opcode))
                    if self._want['vrf'] != 'default':
                        self._result['warnings'] = ["name-servers delete operation with non-default vrf is a success, "
                                                    "but with rpc-error. Recommended to use 'ignore_errors' option with the task as a workaround"]
            elif opcode == 'merge':
                if add_domain_params:
                    _edit_filter_list.append(build_xml('ip-domain', xmap=self._system_domain_meta,
                                                       params=add_domain_params, opcode=opcode))
                if del_domain_params:
                    _edit_filter_list.append(build_xml('ip-domain', xmap=self._system_domain_meta,
                                                       params=del_domain_params, opcode="delete"))

                if add_server_params:
                    _edit_filter_list.append(build_xml('ip-domain', xmap=self._system_server_meta,
                                                       params=add_server_params, opcode=opcode))
                if del_server_params:
                    _edit_filter_list.append(build_xml('ip-domain', xmap=self._system_server_meta,
                                                       params=del_server_params, opcode="delete"))

        diff = None
        if _edit_filter_list:
            commit = not self._module.check_mode
            diff = load_config(self._module, _edit_filter_list, commit=commit, running=running,
                               nc_get_filter=_get_filter)

        if diff:
            if self._module._diff:
                self._result['diff'] = dict(prepared=diff)

            self._result['xml'] = _edit_filter_list
            self._result['changed'] = True

    def run(self):
        self.map_params_to_obj()
        self.map_obj_to_xml_rpc()

        return self._result


def main():
    """ Main entry point for Ansible module execution
    """
    argument_spec = dict(
        hostname=dict(),
        vrf=dict(type='str', default='default'),
        domain_name=dict(),
        domain_search=dict(type='list'),

        name_servers=dict(type='list'),
        lookup_source=dict(),
        lookup_enabled=dict(type='bool', default=True),

        state=dict(choices=['present', 'absent'], default='present')
    )

    argument_spec.update(iosxr_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    config_object = None
    if is_cliconf(module):
        module.deprecate(msg="cli support for 'iosxr_system' is deprecated. Use transport netconf instead",
                         version="4 releases from v2.5")
        config_object = CliConfiguration(module)
    elif is_netconf(module):
        config_object = NCConfiguration(module)

    result = None
    if config_object:
        result = config_object.run()
    module.exit_json(**result)


if __name__ == "__main__":
    main()
