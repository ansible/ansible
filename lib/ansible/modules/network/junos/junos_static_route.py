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
module: junos_static_route
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage static IP routes on Juniper JUNOS network devices
description:
  - This module provides declarative management of static
    IP routes on Juniper JUNOS network devices.
options:
  address:
    description:
      - Network address with prefix of the static route.
    required: true
    aliases: ['prefix']
  next_hop:
    description:
      - Next hop IP of the static route.
    required: true
  qualified_next_hop:
    description:
      - Qualified next hop IP of the static route. Qualified next hops allow
        to associate preference with a particular next-hop address.
  preference:
    description:
      - Global admin preference of the static route.
    aliases: ['admin_distance']
  qualified_preference:
    description:
      - Assign preference for qualified next hop.
  collection:
    description: List of static route definitions
  purge:
    description:
      - Purge static routes not defined in the collections parameter.
    default: no
  state:
    description:
      - State of the static route configuration.
    default: present
    choices: ['present', 'absent']
  active:
    description:
      - Specifies whether or not the configuration is active or deactivated
    default: True
    choices: [True, False]
requirements:
  - ncclient (>=v0.5.2)
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed
"""

EXAMPLES = """
- name: configure static route
  junos_static_route:
    address: 192.168.2.0/24
    next_hop: 10.0.0.1
    preference: 10
    qualified_next_hop: 10.0.0.2
    qualified_preference: 3
    state: present

- name: delete static route
  junos_static_route:
    address: 192.168.2.0/24
    state: absent

- name: deactivate static route configuration
  junos_static_route:
    address: 192.168.2.0/24
    next_hop: 10.0.0.1
    preference: 10
    qualified_next_hop: 10.0.0.2
    qualified_preference: 3
    state: present
    active: False

- name: activate static route configuration
  junos_static_route:
    address: 192.168.2.0/24
    next_hop: 10.0.0.1
    preference: 10
    qualified_next_hop: 10.0.0.2
    qualified_preference: 3
    state: present
    active: True
"""

RETURN = """
diff.prepared:
  description: Configuration difference before and after applying change.
  returned: when configuration is changed and diff option is enabled.
  type: string
  sample: >
          [edit routing-options static]
               route 2.2.2.0/24 { ... }
          +    route 4.4.4.0/24 {
                  next-hop 3.3.3.3;
                  qualified-next-hop 5.5.5.5 {
          +            preference 30;
                   }
          +        preference 10;
          +    }
"""
import collections

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.junos import junos_argument_spec, check_args
from ansible.module_utils.junos import load_config, map_params_to_obj, map_obj_to_ele
from ansible.module_utils.junos import commit_configuration, discard_changes, locked_config

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
        address=dict(required=True, type='str', aliases=['prefix']),
        next_hop=dict(type='str'),
        preference=dict(type='int', aliases=['admin_distance']),
        qualified_next_hop=dict(type='str'),
        qualified_preference=dict(type='int'),
        collection=dict(type='list'),
        purge=dict(type='bool'),
        state=dict(default='present', choices=['present', 'absent']),
        active=dict(default=True, type='bool')
    )

    argument_spec.update(junos_argument_spec)
    required_one_of = [['collection', 'address']]
    mutually_exclusive = [['collection', 'address']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    if module.params['state'] == 'present':
        if not module.params['address'] and module.params['next_hop']:
            module.fail_json(msg="parameters are required together: ['address', 'next_hop']")

    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    top = 'routing-options/static/route'

    param_to_xpath_map = collections.OrderedDict()
    param_to_xpath_map.update([
        ('address', {'xpath': 'name', 'is_key': True}),
        ('next_hop', 'next-hop'),
        ('preference', 'preference/metric-value'),
        ('qualified_next_hop', {'xpath': 'name', 'top': 'qualified-next-hop'}),
        ('qualified_preference', {'xpath': 'preference', 'top': 'qualified-next-hop'})
    ])

    validate_param_values(module, param_to_xpath_map)

    want = map_params_to_obj(module, param_to_xpath_map)
    ele = map_obj_to_ele(module, want, top)

    with locked_config(module):
        diff = load_config(module, tostring(ele), warnings, action='replace')

        commit = not module.check_mode
        if diff:
            if commit:
                commit_configuration(module)
            else:
                discard_changes(module)
            result['changed'] = True

            if module._diff:
                result['diff'] = {'prepared': diff}

    module.exit_json(**result)

if __name__ == "__main__":
    main()
