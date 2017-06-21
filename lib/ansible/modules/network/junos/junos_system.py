#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
#
# This file is part of Ansible by Red Hat
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: junos_system
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage the system attributes on Juniper JUNOS devices
description:
  - This module provides declarative management of node system attributes
    on Juniper JUNOS devices.  It provides an option to configure host system
    parameters or remove those parameters from the device active
    configuration.
options:
  hostname:
    description:
      - Configure the device hostname parameter. This option takes an ASCII string value.
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
  name_servers:
    description:
      - List of DNS name servers by IP address to use to perform name resolution
        lookups.  This argument accepts either a list of DNS servers See
        examples.
  state:
    description:
      - State of the configuration
        values in the device's current active configuration.  When set
        to I(present), the values should be configured in the device active
        configuration and when set to I(absent) the values should not be
        in the device active configuration
    default: present
    choices: ['present', 'absent', 'active', 'suspend']
requirements:
  - ncclient (>=v0.5.2)
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed
"""

EXAMPLES = """
- name: configure hostname and domain name
  junos_system:
    hostname: junos01
    domain_name: test.example.com
    domain-search:
      - ansible.com
      - redhat.com
      - juniper.com

- name: remove configuration
  junos_system:
    state: absent

- name: configure name servers
  junos_system:
    name_servers:
      - 8.8.8.8
      - 8.8.4.4
"""

RETURN = """
rpc:
  description: load-configuration RPC send to the device
  returned: when configuration is changed on device
  type: string
  sample: >
            <interfaces>
                <interface>
                    <name>ge-0/0/0</name>
                    <description>test interface</description>
                </interface>
            </interfaces>
"""
import collections

from ansible.module_utils.junos import junos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.junos import load_config, map_params_to_obj, map_obj_to_ele

try:
    from lxml.etree import tostring
except ImportError:
    from xml.etree.ElementTree import tostring

USE_PERSISTENT_CONNECTION = True


def validate_param_values(module, obj):
    for key in obj:
        # validate the param value (if validator func exists)
        validator = globals().get('validate_%s' % key)
        if callable(validator):
            validator(module.params.get(key), module)


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        hostname=dict(),
        domain_name=dict(),
        domain_search=dict(type='list'),
        name_servers=dict(type='list'),

        state=dict(choices=['present', 'absent', 'active', 'suspend'], default='present')
    )

    argument_spec.update(junos_argument_spec)

    params = ['hostname', 'domain_name', 'domain_search', 'name_servers']
    required_if = [('state', 'present', params, True),
                   ('state', 'absent', params, True),
                   ('state', 'active', params, True),
                   ('state', 'suspend', params, True)]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    top = 'system'

    param_to_xpath_map = collections.OrderedDict()
    param_to_xpath_map.update({
        'hostname': {'xpath': 'host-name', 'leaf_only': True},
        'domain_name': {'xpath': 'domain-name', 'leaf_only': True},
        'domain_search': {'xpath': 'domain-search', 'leaf_only': True, 'value_req': True},
        'name_servers': {'xpath': 'name-server/name', 'is_key': True}
    })

    validate_param_values(module, param_to_xpath_map)

    want = list()
    want.append(map_params_to_obj(module, param_to_xpath_map))
    ele = map_obj_to_ele(module, want, top)

    kwargs = {'commit': not module.check_mode}
    kwargs['action'] = 'replace'

    diff = load_config(module, tostring(ele), warnings, **kwargs)

    if diff:
        result.update({
            'changed': True,
            'diff': {'prepared': diff},
            'rpc': tostring(ele)
        })

    module.exit_json(**result)

if __name__ == "__main__":
    main()
