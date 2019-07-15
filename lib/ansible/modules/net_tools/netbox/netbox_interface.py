#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Mikhail Yohman (@FragmentedPacket) <mikhail.yohman@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {"metadata_version": "1.1",
                    "status": ["preview"],
                    "supported_by": "community"}

DOCUMENTATION = r"""
---
module: netbox_interface
short_description: Creates or removes interfaces from Netbox
description:
  - Creates or removes interfaces from Netbox
notes:
  - Tags should be defined as a YAML list
  - This should be ran with connection C(local) and hosts C(localhost)
author:
  - Mikhail Yohman (@FragmentedPacket)
requirements:
  - pynetbox
version_added: "2.8"
options:
  netbox_url:
    description:
      - URL of the Netbox instance resolvable by Ansible control host
    required: true
    type: str
  netbox_token:
    description:
      - The token created within Netbox to authorize API access
    required: true
    type: str
  data:
    description:
      - Defines the prefix configuration
    suboptions:
      device:
        description:
          - Name of the device the interface will be associated with (case-sensitive)
        required: true
        type: str
      name:
        description:
          - Name of the interface to be created
        required: true
        type: str
      form_factor:
        description:
          - |
            Form factor of the interface:
            ex. 1000Base-T (1GE), Virtual, 10GBASE-T (10GE)
            This has to be specified exactly as what is found within UI
        type: str
      enabled:
        description:
          - Sets whether interface shows enabled or disabled
        type: bool
      lag:
        description:
          - Parent LAG interface will be a member of
        type: dict
      mtu:
        description:
          - The MTU of the interface
        type: str
      mac_address:
        description:
          - The MAC address of the interface
        type: str
      mgmt_only:
        description:
          - This interface is used only for out-of-band management
        type: bool
      description:
        description:
          - The description of the prefix
        type: str
      mode:
        description:
          - The mode of the interface
        choices:
          - Access
          - Tagged
          - Tagged All
        type: str
      untagged_vlan:
        description:
          - The untagged VLAN to be assigned to interface
        type: dict
      tagged_vlans:
        description:
          - A list of tagged VLANS to be assigned to interface. Mode must be set to either C(Tagged) or C(Tagged All)
        type: list
      tags:
        description:
          - Any tags that the prefix may need to be associated with
        type: list
    required: true
  state:
    description:
      - Use C(present) or C(absent) for adding or removing.
    choices: [ absent, present ]
    default: present
    type: str
  validate_certs:
    description:
      - |
        If C(no), SSL certificates will not be validated.
        This should only be used on personally controlled sites using self-signed certificates.
    default: "yes"
    type: bool
"""

EXAMPLES = r"""
- name: "Test Netbox interface module"
  connection: local
  hosts: localhost
  gather_facts: False
  tasks:
    - name: Create interface within Netbox with only required information
      netbox_interface:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          device: test100
          name: GigabitEthernet1
        state: present
    - name: Delete interface within netbox
      netbox_interface:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          device: test100
          name: GigabitEthernet1
        state: absent
    - name: Create LAG with several specified options
      netbox_interface:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          device: test100
          name: port-channel1
          form_factor: Link Aggregation Group (LAG)
          mtu: 1600
          mgmt_only: false
          mode: Access
        state: present
    - name: Create interface and assign it to parent LAG
      netbox_interface:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          device: test100
          name: GigabitEthernet1
          enabled: false
          form_factor: 1000Base-t (1GE)
          lag:
            name: port-channel1
          mtu: 1600
          mgmt_only: false
          mode: Access
        state: present
    - name: Create interface as a trunk port
      netbox_interface:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          device: test100
          name: GigabitEthernet25
          enabled: false
          form_factor: 1000Base-t (1GE)
          untagged_vlan:
            name: Wireless
            site: Test Site
          tagged_vlans:
            - name: Data
              site: Test Site
            - name: VoIP
              site: Test Site
          mtu: 1600
          mgmt_only: true
          mode: Tagged
        state: present
"""

RETURN = r"""
interface:
  description: Serialized object as created or already existent within Netbox
  returned: on creation
  type: dict
msg:
  description: Message indicating failure or info about what has been achieved
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.net_tools.netbox.netbox_dcim import (
    NetboxDcimModule,
    NB_INTERFACES,
)


def main():
    """
    Main entry point for module execution
    """
    argument_spec = dict(
        netbox_url=dict(type="str", required=True),
        netbox_token=dict(type="str", required=True, no_log=True),
        data=dict(type="dict", required=True),
        state=dict(required=False, default="present", choices=["present", "absent"]),
        validate_certs=dict(type="bool", default=True)
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    netbox_interface = NetboxDcimModule(module, NB_INTERFACES)
    netbox_interface.run()


if __name__ == "__main__":
    main()
