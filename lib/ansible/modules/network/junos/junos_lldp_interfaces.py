#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#############################################
#                WARNING                    #
#############################################
#
# This file is auto generated by the resource
#   module builder playbook.
#
# Do not edit this file manually.
#
# Changes to this file will be over written
#   by the resource module builder.
#
# Changes should be made in the model used to
#   generate this file or in the resource module
#   builder template.
#
#############################################

"""
The module file for junos_lldp_interfaces
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'network'
}

DOCUMENTATION = """
---
module: junos_lldp_interfaces
version_added: 2.9
short_description: Manage link layer discovery protocol (LLDP) attributes of interfaces on Juniper JUNOS devices
description:
  - This module manages link layer discovery protocol (LLDP) attributes of interfaces on Juniper JUNOS devices.
author: Ganesh Nalawade (@ganeshrn)
options:
  config:
    description: The list of link layer discovery protocol interface attribute configurations
    type: list
    elements: dict
    suboptions:
      name:
        description:
          - Name of the interface LLDP needs to be configured on.
        type: str
        required: True
      enabled:
        description:
          - This is a boolean value to control disabling of LLDP on the interface C(name)
        type: bool
  state:
    description:
      - The state the configuration should be left in.
    type: str
    choices:
    - merged
    - replaced
    - overridden
    - deleted
    default: merged
"""
EXAMPLES = """
# Using merged
# Before state:
# -------------
# user@junos01# # show protocols lldp
# management-address 10.1.1.1;
# advertisement-interval 10000;

- name: Merge provided configuration with device configuration
  junos_lldp_interfaces:
    config:
      - name: ge-0/0/1
      - name: ge-0/0/2
        enabled: False
    state: merged

# After state:
# -------------
# user@junos01# show protocols lldp
# management-address 10.1.1.1;
# advertisement-interval 10000;
# interface ge-0/0/1;
# interface ge-0/0/2 {
#     disable;
# }

# Using replaced
# Before state:
# -------------
# user@junos01# show protocols lldp
# management-address 10.1.1.1;
# advertisement-interval 10000;
# interface ge-0/0/1;
# interface ge-0/0/2 {
#     disable;
# }

- name: Replace provided configuration with device configuration
  junos_lldp_interfaces:
    config:
      - name: ge-0/0/2
        disable: False
      - name: ge-0/0/3
        enabled: False
    state: replaced

# After state:
# -------------
# user@junos01# show protocols lldp
# management-address 10.1.1.1;
# advertisement-interval 10000;
# interface ge-0/0/1;
# interface ge-0/0/2;
# interface ge-0/0/3 {
#     disable;
# }

# Using overridden
# Before state:
# -------------
# user@junos01# show protocols lldp
# management-address 10.1.1.1;
# advertisement-interval 10000;
# interface ge-0/0/1;
# interface ge-0/0/2 {
#     disable;
# }

- name: Override provided configuration with device configuration
  junos_lldp_interfaces:
    config:
      - name: ge-0/0/2
        enabled: False
    state: overridden

# After state:
# -------------
# user@junos01# show protocols lldp
# management-address 10.1.1.1;
# advertisement-interval 10000;
# interface ge-0/0/2 {
#     disable;
# }

# Using deleted
# Before state:
# -------------
# user@junos01# show protocols lldp
# management-address 10.1.1.1;
# advertisement-interval 10000;
# interface ge-0/0/1;
# interface ge-0/0/2;
# interface ge-0/0/3 {
#     disable;
# }
- name: Delete lldp interface configuration (this will not delete other lldp configuration)
  junos_lldp_interfaces:
    config:
    - name: ge-0/0/1
    - name: ge-0/0/3
    state: deleted

# After state:
# -------------
# user@junos01# show protocols lldp
# management-address 10.1.1.1;
# advertisement-interval 10000;
# interface ge-0/0/2;
# interface ge-0/0/1;
"""

RETURN = """
before:
  description: The configuration prior to the model invocation.
  returned: always
  type: list
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
after:
  description: The resulting configuration model invocation.
  returned: when changed
  type: list
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
commands:
  description: The set of commands pushed to the remote device.
  returned: always
  type: list
  sample: ['xml 1', 'xml 2', 'xml 3']
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.junos.argspec.lldp_interfaces.lldp_interfaces import Lldp_interfacesArgs
from ansible.module_utils.network.junos.config.lldp_interfaces.lldp_interfaces import Lldp_interfaces


def main():
    """
    Main entry point for module execution
    :returns: the result form module invocation
    """
    required_if = [('state', 'merged', ('config',)),
                   ('state', 'replaced', ('config',)),
                   ('state', 'overridden', ('config',))]

    module = AnsibleModule(argument_spec=Lldp_interfacesArgs.argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    result = Lldp_interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
