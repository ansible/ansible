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
module: junos_vrf
version_added: "2.4"
author: "Ganesh Nalawade (@ganeshrn)"
short_description: Manage the VRF definitions on Juniper JUNOS devices
description:
  - This module provides declarative management of VRF definitions on
    Juniper JUNOS devices.  It allows playbooks to manage individual or
    the entire VRF collection.
options:
  name:
    description:
      - The name of the VRF definition to be managed on the remote IOS
        device.  The VRF definition name is an ASCII string name used
        to uniquely identify the VRF.  This argument is mutually exclusive
        with the C(aggregate) argument
  description:
    description:
      - Provides a short description of the VRF definition in the
        current active configuration.  The VRF definition value accepts
        alphanumeric characters used to provide additional information
        about the VRF.
  rd:
    description:
      - The router-distinguisher value uniquely identifies the VRF to
        routing processes on the remote IOS system.  The RD value takes
        the form of C(A:B) where C(A) and C(B) are both numeric values.
  interfaces:
    description:
      - Identifies the set of interfaces that
        should be configured in the VRF. Interfaces must be routed
        interfaces in order to be placed into a VRF.
  target:
    description:
      - It configures VRF target community configuration. The target value takes
        the form of C(target:A:B) where C(A) and C(B) are both numeric values.
  table_label:
    description:
      - Causes JUNOS to allocate a VPN label per VRF rather than per VPN FEC.
        This allows for forwarding of traffic to directly connected subnets, COS
        Egress filtering etc.
    type: bool
  aggregate:
    description:
      - The set of VRF definition objects to be configured on the remote
        JUNOS device.  Ths list entries can either be the VRF name or a hash
        of VRF definitions and attributes.  This argument is mutually
        exclusive with the C(name) argument.
  state:
    description:
      - Configures the state of the VRF definition
        as it relates to the device operational configuration.  When set
        to I(present), the VRF should be configured in the device active
        configuration and when set to I(absent) the VRF should not be
        in the device active configuration
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
- name: Configure vrf configuration
  junos_vrf:
    name: test-1
    description: test-vrf-1
    interfaces:
      - ge-0/0/3
      - ge-0/0/2
    rd: 192.0.2.1:10
    target: target:65514:113
    state: present

- name: Remove vrf configuration
  junos_vrf:
    name: test-1
    description: test-vrf-1
    interfaces:
      - ge-0/0/3
      - ge-0/0/2
    rd: 192.0.2.1:10
    target: target:65514:113
    state: absent

- name: Deactivate vrf configuration
  junos_vrf:
    name: test-1
    description: test-vrf-1
    interfaces:
      - ge-0/0/3
      - ge-0/0/2
    rd: 192.0.2.1:10
    target: target:65514:113
    active: False

- name: Activate vrf configuration
  junos_vrf:
    name: test-1
    description: test-vrf-1
    interfaces:
      - ge-0/0/3
      - ge-0/0/2
    rd: 192.0.2.1:10
    target: target:65514:113
    active: True

- name: Create vrf using aggregate
  junos_vrf:
    aggregate:
    - name: test-1
      description: test-vrf-1
      interfaces:
        - ge-0/0/3
         - ge-0/0/2
      rd: 192.0.2.1:10
      target: target:65514:113
    - name: test-2
      description: test-vrf-2
      interfaces:
        - ge-0/0/4
        - ge-0/0/5
      rd: 192.0.2.2:10
      target: target:65515:114
  state: present
"""

RETURN = """
diff.prepared:
  description: Configuration difference before and after applying change.
  returned: when configuration is changed and diff option is enabled.
  type: string
  sample: >
        [edit routing-instances]
        +   test-1 {
        +       description test-vrf-1;
        +       instance-type vrf;
        +       interface ge-0/0/2.0;
        +       interface ge-0/0/3.0;
        +       route-distinguisher 192.0.2.1:10;
        +       vrf-target target:65514:113;
        +   }
"""
import collections

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.network.junos.junos import junos_argument_spec
from ansible.module_utils.network.junos.junos import load_config, map_params_to_obj, map_obj_to_ele, to_param_list
from ansible.module_utils.network.junos.junos import commit_configuration, discard_changes, locked_config

try:
    from lxml.etree import tostring
except ImportError:
    from xml.etree.ElementTree import tostring

USE_PERSISTENT_CONNECTION = True


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(),
        description=dict(),
        rd=dict(type='list'),
        interfaces=dict(type='list'),
        target=dict(type='list'),
        state=dict(default='present', choices=['present', 'absent']),
        active=dict(default=True, type='bool'),
        table_label=dict(default=True, type='bool')
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

    required_one_of = [['aggregate', 'name']]
    mutually_exclusive = [['aggregate', 'name']]

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive)

    warnings = list()
    result = {'changed': False}

    if warnings:
        result['warnings'] = warnings

    top = 'routing-instances/instance'

    param_to_xpath_map = collections.OrderedDict()
    param_to_xpath_map.update([
        ('name', {'xpath': 'name', 'is_key': True}),
        ('description', 'description'),
        ('type', 'instance-type'),
        ('rd', 'route-distinguisher/rd-type'),
        ('interfaces', 'interface/name'),
        ('target', 'vrf-target/community'),
        ('table_label', {'xpath': 'vrf-table-label', 'tag_only': True}),
    ])

    params = to_param_list(module)
    requests = list()

    for param in params:
        # if key doesn't exist in the item, get it from module.params
        for key in param:
            if param.get(key) is None:
                param[key] = module.params[key]

        item = param.copy()
        item['type'] = 'vrf'

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
