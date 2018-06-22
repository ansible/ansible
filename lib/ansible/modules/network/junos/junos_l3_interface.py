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
module: junos_l3_interface
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage L3 interfaces on Juniper JUNOS network devices
description:
  - This module provides declarative management of L3 interfaces
    on Juniper JUNOS network devices.
options:
  name:
    description:
      - Name of the L3 interface.
  ipv4:
    description:
      - IPv4 of the L3 interface.
  ipv6:
    description:
      - IPv6 of the L3 interface.
  unit:
    description:
      - Logical interface number.
    default: 0
  aggregate:
    description: List of L3 interfaces definitions
  state:
    description:
      - State of the L3 interface configuration.
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
- name: Set ge-0/0/1 IPv4 address
  junos_l3_interface:
    name: ge-0/0/1
    ipv4: 192.168.0.1

- name: Remove ge-0/0/1 IPv4 address
  junos_l3_interface:
    name: ge-0/0/1
    state: absent

- name: Set ipv4 address using aggregate
  junos_l3_interface:
    aggregate:
    - name: ge-0/0/1
      ipv4: 192.0.2.1
    - name: ge-0/0/2
      ipv4: 192.0.2.2
      ipv6: fd5d:12c9:2201:2::2

- name: Delete ipv4 address using aggregate
  junos_l3_interface:
    aggregate:
    - name: ge-0/0/1
      ipv4: 192.0.2.1
    - name: ge-0/0/2
      ipv4: 192.0.2.2
    state: absent
"""

RETURN = """
diff:
  description: Configuration difference before and after applying change.
  returned: when configuration is changed and diff option is enabled.
  type: string
  sample: >
        [edit interfaces ge-0/0/1 unit 0 family inet]
        +       address 192.0.2.1/32;
        [edit interfaces ge-0/0/1 unit 0 family inet6]
        +       address fd5d:12c9:2201:1::1/128;
"""
import collections

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.junos.junos import junos_argument_spec, tostring
from ansible.module_utils.network.junos.junos import load_config, map_params_to_obj, map_obj_to_ele
from ansible.module_utils.network.junos.junos import commit_configuration, discard_changes, locked_config, to_param_list

USE_PERSISTENT_CONNECTION = True


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(),
        ipv4=dict(),
        ipv6=dict(),
        unit=dict(default=0, type='int'),
        state=dict(default='present', choices=['present', 'absent']),
        active=dict(default=True, type='bool')
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    )

    argument_spec.update(element_spec)
    argument_spec.update(junos_argument_spec)

    required_one_of = [['name', 'aggregate']]
    mutually_exclusive = [['name', 'aggregate']]

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           mutually_exclusive=mutually_exclusive,
                           required_one_of=required_one_of)

    warnings = list()
    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    top = 'interfaces/interface'

    param_to_xpath_map = collections.OrderedDict()
    param_to_xpath_map.update([
        ('name', {'xpath': 'name', 'parent_attrib': False, 'is_key': True}),
        ('unit', {'xpath': 'name', 'top': 'unit', 'parent_attrib': False, 'is_key': True}),
        ('ipv4', {'xpath': 'inet/address/name', 'top': 'unit/family', 'is_key': True}),
        ('ipv6', {'xpath': 'inet6/address/name', 'top': 'unit/family', 'is_key': True})
    ])

    params = to_param_list(module)

    requests = list()
    for param in params:
        # if key doesn't exist in the item, get it from module.params
        for key in param:
            if param.get(key) is None:
                param[key] = module.params[key]

        item = param.copy()
        if not item['ipv4'] and not item['ipv6']:
            module.fail_json(msg="one of the following is required: ipv4,ipv6")

        want = map_params_to_obj(module, param_to_xpath_map, param=item)
        requests.append(map_obj_to_ele(module, want, top, param=item))

    diff = None
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
