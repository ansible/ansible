#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = """
---
module: junos_vlan
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage VLANs on Juniper JUNOS network devices
description:
  - This module provides declarative management of VLANs
    on Juniper JUNOS network devices.
options:
  name:
    description:
      - Name of the VLAN.
    required: true
  vlan_id:
    description:
      - ID of the VLAN.
    required: true
  description:
    description:
      - Text description of VLANs.
  interfaces:
    description:
      - List of interfaces to check the VLAN has been
        configured correctly.
  aggregate:
    description: List of VLANs definitions.
  purge:
    description:
      - Purge VLANs not defined in the aggregate parameter.
    default: no
  state:
    description:
      - State of the VLAN configuration.
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
- name: configure VLAN ID and name
  junos_vlan:
    vlan_name: test
    vlan_id: 20
    name: test-vlan

- name: remove VLAN configuration
  junos_vlan:
    vlan_name: test
    state: absent

- name: deactive VLAN configuration
  junos_vlan:
    vlan_name: test
    state: present
    active: False

- name: activate VLAN configuration
  junos_vlan:
    vlan_name: test
    state: present
    active: True

- name: Create vlan configuration using aggregate
  junos_vlan:
    aggregate:
      - { vlan_id: 159, name: test_vlan_1, description: test vlan-1, state: present }
      - { vlan_id: 160, name: test_vlan_2, description: test vlan-2, state: present }

- name: Delete vlan configuration using aggregate
  junos_vlan:
    aggregate:
      - { vlan_id: 159, name: test_vlan_1, state: absent }
      - { vlan_id: 160, name: test_vlan_2, state: absent }
"""

RETURN = """
diff.prepared:
  description: Configuration difference before and after applying change.
  returned: when configuration is changed and diff option is enabled.
  type: string
  sample: >
         [edit vlans]
         +   test-vlan-1 {
         +       vlan-id 60;
         +   }
"""
import collections

from copy import copy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.junos import junos_argument_spec, check_args
from ansible.module_utils.junos import load_config, map_params_to_obj, map_obj_to_ele, to_param_list
from ansible.module_utils.junos import commit_configuration, discard_changes, locked_config

try:
    from lxml.etree import tostring
except ImportError:
    from xml.etree.ElementTree import tostring

USE_PERSISTENT_CONNECTION = True


def validate_vlan_id(value, module):
    if not 1 <= value <= 4094:
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
        state=dict(default='present', choices=['present', 'absent']),
        active=dict(default=True, type='bool')
    )
    aggregate_spec = copy(element_spec)
    aggregate_spec['name'] = dict(required=True)
    aggregate_spec['vlan_id'] = dict(required=True, type='int')

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
        purge=dict(default=False, type='bool')
    )

    argument_spec.update(element_spec)
    argument_spec.update(junos_argument_spec)

    required_one_of = [['aggregate', 'name']]
    required_together = [['name', 'vlan_id']]
    mutually_exclusive = [['aggregate', 'name'],
                          ['aggregate', 'vlan_id'],
                          ['aggregate', 'description'],
                          ['aggregate', 'interfaces'],
                          ['aggregate', 'state'],
                          ['aggregate', 'active']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           required_together=required_together,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    top = 'vlans/vlan'

    param_to_xpath_map = collections.OrderedDict()
    param_to_xpath_map.update([
        ('name', {'xpath': 'name', 'is_key': True}),
        ('vlan_id', 'vlan-id'),
        ('description', 'description')
    ])

    params = to_param_list(module)
    requests = list()

    for param in params:
        item = copy(param)
        validate_param_values(module, param_to_xpath_map, param=item)

        want = map_params_to_obj(module, param_to_xpath_map, param=item)
        requests.append(map_obj_to_ele(module, want, top, param=item))

    with locked_config(module):
        for req in requests:
            diff = load_config(module, tostring(req), warnings, action='replace')

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
