#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: junos_vlan
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage VLANs on Juniper JUNOS network devices
description:
  - This module provides declarative management of VLANs
    on Juniper JUNOS network devices.
deprecated:
  removed_in: "2.13"
  why: Updated modules released with more functionality
  alternative: Use M(junos_vlans) instead.
options:
  name:
    description:
      - Name of the VLAN.
    required: true
  vlan_id:
    description:
      - ID of the VLAN. Range 1-4094.
    required: true
  l3_interface:
    description:
      -  Name of logical layer 3 interface.
    version_added: "2.7"
  filter_input:
    description:
      - The name of input filter.
    version_added: "2.8"
  filter_output:
    description:
      - The name of output filter.
    version_added: "2.8"
  description:
    description:
      - Text description of VLANs.
  interfaces:
    description:
      - List of interfaces to check the VLAN has been
        configured correctly.
  aggregate:
    description: List of VLANs definitions.
  state:
    description:
      - State of the VLAN configuration.
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
- name: configure VLAN ID and name
  junos_vlan:
    name: test
    vlan_id: 20

- name: Link to logical layer 3 interface
  junos_vlan:
    name: test
    vlan_id: 20
    l3-interface: vlan.20

- name: remove VLAN configuration
  junos_vlan:
    name: test
    state: absent

- name: deactive VLAN configuration
  junos_vlan:
    name: test
    state: present
    active: False

- name: activate VLAN configuration
  junos_vlan:
    name: test
    state: present
    active: True

- name: Create vlan configuration using aggregate
  junos_vlan:
    aggregate:
      - { vlan_id: 159, name: test_vlan_1, description: test vlan-1 }
      - { vlan_id: 160, name: test_vlan_2, description: test vlan-2 }

- name: Delete vlan configuration using aggregate
  junos_vlan:
    aggregate:
      - { vlan_id: 159, name: test_vlan_1 }
      - { vlan_id: 160, name: test_vlan_2 }
    state: absent
"""

RETURN = """
diff.prepared:
  description: Configuration difference before and after applying change.
  returned: when configuration is changed and diff option is enabled.
  type: str
  sample: >
         [edit vlans]
         +   test-vlan-1 {
         +       vlan-id 60;
         +   }
"""
import collections

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.junos.junos import junos_argument_spec, tostring
from ansible.module_utils.network.junos.junos import load_config, map_params_to_obj, map_obj_to_ele, to_param_list
from ansible.module_utils.network.junos.junos import commit_configuration, discard_changes, locked_config

USE_PERSISTENT_CONNECTION = True


def validate_vlan_id(value, module):
    if value and not 1 <= value <= 4094:
        module.fail_json(msg='vlan_id must be between 1 and 4094')


def validate_param_values(module, obj, param=None):
    if not param:
        param = module.params
    for key in obj:
        # validate the param value (if validator func exists)
        validator = globals().get('validate_%s' % key)
        if callable(validator):
            validator(param.get(key), module)


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(),
        vlan_id=dict(type='int'),
        description=dict(),
        interfaces=dict(),
        l3_interface=dict(),
        filter_input=dict(),
        filter_output=dict(),
        state=dict(default='present', choices=['present', 'absent']),
        active=dict(default=True, type='bool')
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec)
    )

    argument_spec.update(element_spec)
    argument_spec.update(junos_argument_spec)

    required_one_of = [['aggregate', 'name']]
    mutually_exclusive = [['aggregate', 'name']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    top = 'vlans/vlan'

    param_to_xpath_map = collections.OrderedDict()
    param_to_xpath_map.update([
        ('name', {'xpath': 'name', 'is_key': True}),
        ('vlan_id', 'vlan-id'),
        ('l3_interface', 'l3-interface'),
        ('filter_input', 'forwarding-options/filter/input'),
        ('filter_output', 'forwarding-options/filter/output'),
        ('description', 'description')
    ])

    params = to_param_list(module)
    requests = list()

    for param in params:
        # if key doesn't exist in the item, get it from module.params
        for key in param:
            if param.get(key) is None:
                param[key] = module.params[key]

        item = param.copy()

        validate_param_values(module, param_to_xpath_map, param=item)

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
