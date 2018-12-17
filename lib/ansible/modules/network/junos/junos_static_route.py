#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


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
  aggregate:
    description: List of static route definitions
  state:
    description:
      - State of the static route configuration.
    default: present
    choices: ['present', 'absent']
  active:
    description:
      - Specifies whether or not the configuration is active or deactivated
    default: True
    type: bool
requirements:
  - ncclient (>=v0.5.2)
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed.
  - Tested against vSRX JUNOS version 15.1X49-D15.4, vqfx-10000 JUNOS Version 15.1X53-D60.4.
  - Recommended connection is C(netconf). See L(the Junos OS Platform Options,../network/user_guide/platform_junos.html).
  - This module also works with C(local) connections for legacy playbooks.
extends_documentation_fragment: junos
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

- name: Configure static route using aggregate
  junos_static_route:
    aggregate:
    - { address: 4.4.4.0/24, next_hop: 3.3.3.3, qualified_next_hop: 5.5.5.5, qualified_preference: 30 }
    - { address: 5.5.5.0/24, next_hop: 6.6.6.6, qualified_next_hop: 7.7.7.7, qualified_preference: 12 }
    preference: 10

- name: Delete static route using aggregate
  junos_static_route:
    aggregate:
    - address: 4.4.4.0/24
    - address: 5.5.5.0/24
    state: absent
"""

RETURN = """
diff.prepared:
  description: Configuration difference before and after applying change.
  returned: when configuration is changed and diff option is enabled.
  type: str
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

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.junos.junos import junos_argument_spec, tostring
from ansible.module_utils.network.junos.junos import load_config, map_params_to_obj, map_obj_to_ele, to_param_list
from ansible.module_utils.network.junos.junos import commit_configuration, discard_changes, locked_config

USE_PERSISTENT_CONNECTION = True


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        address=dict(aliases=['prefix']),
        next_hop=dict(),
        preference=dict(type='int', aliases=['admin_distance']),
        qualified_next_hop=dict(type='str'),
        qualified_preference=dict(type='int'),
        state=dict(default='present', choices=['present', 'absent']),
        active=dict(default=True, type='bool')
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['address'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)
    argument_spec.update(junos_argument_spec)

    required_one_of = [['aggregate', 'address']]
    mutually_exclusive = [['aggregate', 'address']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
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

    params = to_param_list(module)
    requests = list()

    for param in params:
        # if key doesn't exist in the item, get it from module.params
        for key in param:
            if param.get(key) is None:
                param[key] = module.params[key]

        item = param.copy()
        if item['state'] == 'present':
            if not item['address'] and item['next_hop']:
                module.fail_json(msg="parameters are required together: ['address', 'next_hop']")

        want = map_params_to_obj(module, param_to_xpath_map, param=item)
        requests.append(map_obj_to_ele(module, want, top, param=item))

    with locked_config(module):
        for req in requests:
            diff = load_config(module, tostring(req), warnings, action='merge')

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
