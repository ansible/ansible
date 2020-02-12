#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2020, Allied Telesis Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: awplus_interfaces
author: Cheng Yi Kok (@cyk19)
short_description: 'Manages attribute of AlliedWare Plus interfaces.'
description: 'Manages attribute of AlliedWare Plus network interfaces'
version_added: "2.10"
options:
  config:
    description: A dictionary of interface options
    type: list
    suboptions:
      name:
        description:
        - Full name of interface, e.g. GigabitEthernet0/2, loopback999.
        type: str
        required: True
      description:
        description:
        - Interface description.
        type: str
      enabled:
        description:
        - Administrative state of the interface.
        - Set the value to C(true) to administratively enable the interface or C(false) to disable it.
        type: bool
        default: True
      speed:
        description:
        - Interface link speed. Applicable for Ethernet interfaces only.
        type: str
      mtu:
        description:
        - MTU for a specific interface. Applicable for Ethernet interfaces only.
        - Refer to vendor documentation for valid values.
        type: int
      duplex:
        description:
        - Interface link status. Applicable for Ethernet interfaces only, either in half duplex,
          full duplex or in automatic state which negotiates the duplex automatically.
        type: str
        choices: ['full', 'half', 'auto']
  state:
    choices:
    - merged
    - replaced
    - overridden
    - deleted
    default: merged
    description:
    - The state of the configuration after module completion
    type: str
"""

EXAMPLES = """
# Using merged

Before state:
------------------
interface port1.0.1
 switchport
 switchport mode access
!
interface port1.0.2
 duplex full
 switchport
 switchport mode access
!
interface port1.0.3
 speed 1000
 duplex full
 switchport
 switchport mode access
!
interface port1.0.4
 duplex full
 switchport
 switchport mode access
!
interface vlan1
 ip address 192.168.5.2/24
 ipv6 enable
 ipv6 address dhcp
 ip dhcp-client vendor-identifying-class
 ip dhcp-client request vendor-identifying-specific
!

    - name: Test awplus_interface module
    connection: network_cli
    hosts: all
    tasks:
      - name: Merge provided configuration with device configuration
        awplus_interfaces:
          config:
            - name: port1.0.2
              description: Merged by Ansible Network
              duplex: full

              # vlan1 does not have duplex configuration option
            - name: vlan1
              description: Merged by Ansible Network
              mtu: 1500 # in the range <68-1582> ; Changed mtu config doesn't show in CLI
          state: merged

After state:
---------------------
interface port1.0.1
 switchport
 switchport mode access
!
interface port1.0.2
 description Merged by Ansible Network
 duplex full
 switchport
 switchport mode access
!
interface port1.0.3
 speed 1000
 duplex full
 switchport
 switchport mode access
!
interface port1.0.4
 duplex full
 switchport
 switchport mode access
!
interface vlan1
 description Merged by Ansible Network
 ip address 192.168.5.2/24
 ipv6 enable
 ipv6 address dhcp
 ip dhcp-client vendor-identifying-class
 ip dhcp-client request vendor-identifying-specific
!

Using replaced:

Before state:
---------------------
interface port1.0.1
 switchport
 switchport mode access
!
interface port1.0.2
 description Merged by Ansible Network
 duplex full
 switchport
 switchport mode access
!
interface port1.0.3
 speed 1000
 duplex full
 switchport
 switchport mode access
!
interface port1.0.4
 duplex full
 switchport
 switchport mode access
!
interface vlan1
 description Merged by Ansible Network
 ip address 192.168.5.2/24
 ipv6 enable
 ipv6 address dhcp
 ip dhcp-client vendor-identifying-class
 ip dhcp-client request vendor-identifying-specific
!

  - name: Test awplus_interface module
    connection: network_cli
    hosts: all
    tasks:
      - name: Replace device configuration with provided configuration
        awplus_interfaces:
          config:
            - name: port1.0.3
              description: Replaced by Ansible Network
              duplex: full
              # Available options for speed:
              # 10, 100, 1000, 10000, 100000, (mbps)
              # 2500, 40000, 5000, auto (mbps)
              speed: 1000
              enabled: False

              # vlan1 does not have duplex configuration option
            - name: vlan1
              description: Replaced by Ansible Network
              mtu: 900 # in the range <68-1582>
              enabled: True
          state: replaced

After state:
---------------------
interface port1.0.1
 switchport
 switchport mode access
!
interface port1.0.2
 description Merged by Ansible Network
 duplex full
 switchport
 switchport mode access
!
interface port1.0.3
 description Replaced by Ansible Network
 speed 1000
 duplex full
 shutdown
 switchport
 switchport mode access
!
interface port1.0.4
 duplex full
 switchport
 switchport mode access
!
interface vlan1
 description Replaced by Ansible Network
 ip address 192.168.5.2/24
 ipv6 enable
 ipv6 address dhcp
 ip dhcp-client vendor-identifying-class
 ip dhcp-client request vendor-identifying-specific
!

Using overridden

Before state:
------------------------
interface port1.0.1
 switchport
 switchport mode access
!
interface port1.0.2
 description Merged by Ansible Network
 duplex full
 switchport
 switchport mode access
!
interface port1.0.3
 description Replaced by Ansible Network
 speed 1000
 duplex full
 shutdown
 switchport
 switchport mode access
!
interface port1.0.4
 duplex full
 switchport
 switchport mode access
!
interface vlan1
 description Replaced by Ansible Network
 ip address 192.168.5.2/24
 ipv6 enable
 ipv6 address dhcp
 ip dhcp-client vendor-identifying-class
 ip dhcp-client request vendor-identifying-specific
!

---
  - name: Test awplus_interface module
    connection: network_cli
    hosts: all
    tasks:
      - name: Override device configuration of all interfaces with provided configuration
        awplus_interfaces:
          config:
            - name: port1.0.4
              description: Override by Ansible Network
              duplex: full
              # Available options for speed:
              # 10, 100, 1000, 10000, 100000, (mbps)
              # 2500, 40000, 5000, auto (mbps)
              speed: 2500
              enabled: True

              # vlan1 does not have duplex configuration option
            - name: vlan1
              description: Override by Ansible Network
              mtu: 900 # in the range <68-1582>
              enabled: True
          state: replaced

After state:
-------------------------
interface port1.0.1
 switchport
 switchport mode access
!
interface port1.0.2
 description Merged by Ansible Network
 duplex full
 switchport
 switchport mode access
!
interface port1.0.3
 description Replaced by Ansible Network
 speed 1000
 duplex full
 shutdown
 switchport
 switchport mode access
!
interface port1.0.4
 description Override by Ansible Network
 duplex full
 switchport
 switchport mode access
!
interface vlan1
 description Override by Ansible Network
 ip address 192.168.5.2/24
 ipv6 enable
 ipv6 address dhcp
 ip dhcp-client vendor-identifying-class
 ip dhcp-client request vendor-identifying-specific
!

Using Deleted

Before state:
---------------------
interface port1.0.1
 switchport
 switchport mode access
!
interface port1.0.2
 description Merged by Ansible Network
 duplex full
 switchport
 switchport mode access
!
interface port1.0.3
 description Replaced by Ansible Network
 speed 1000
 duplex full
 shutdown
 switchport
 switchport mode access
!
interface port1.0.4
 description Override by Ansible Network
 duplex full
 switchport
 switchport mode access
!
interface vlan1
 description Override by Ansible Network
 ip address 192.168.5.2/24
 ipv6 enable
 ipv6 address dhcp
 ip dhcp-client vendor-identifying-class
 ip dhcp-client request vendor-identifying-specific
!

  - name: Test awplus_interface module
    connection: network_cli
    hosts: all
    tasks:
      - name: "Delete module attributes of given interfaces (Note: This won't delete the interface itself)"
        awplus_interfaces:
          config:
            - name: port1.0.2
          state: deleted

After state:
---------------------------
interface port1.0.1
 switchport
 switchport mode access
!
interface port1.0.2
 duplex full
 switchport
 switchport mode access
!
interface port1.0.3
 description Replaced by Ansible Network
 speed 1000
 duplex full
 shutdown
 switchport
 switchport mode access
!
interface port1.0.4
 description Override by Ansible Network
 duplex full
 switchport
 switchport mode access
!
interface vlan1
 description Override by Ansible Network
 ip address 192.168.5.2/24
 ipv6 enable
 ipv6 address dhcp
 ip dhcp-client vendor-identifying-class
 ip dhcp-client request vendor-identifying-specific
!

Using Deleted without any config passed
NOTE: This will delete all of configured resource module attributes from each configured interface

Before state:
-----------------------
interface port1.0.1
 switchport
 switchport mode access
!
interface port1.0.2
 duplex full
 switchport
 switchport mode access
!
interface port1.0.3
 description Replaced by Ansible Network
 speed 1000
 duplex full
 shutdown
 switchport
 switchport mode access
!
interface port1.0.4
 description Override by Ansible Network
 duplex full
 switchport
 switchport mode access
!
interface vlan1
 description Override by Ansible Network
 ip address 192.168.5.2/24
 ipv6 enable
 ipv6 address dhcp
 ip dhcp-client vendor-identifying-class
 ip dhcp-client request vendor-identifying-specific
!

  - name: Test awplus_interface module
    connection: network_cli
    hosts: all
    tasks:
      - name: "Delete module attributes of given interfaces (Note: This won't delete the interface itself)"
        awplus_interfaces:source hacking/env-setup
          config:
          state: deleted

After state:
---------------------------
interface port1.0.1
 switchport
 switchport mode access
!
interface port1.0.2
 duplex full
 switchport
 switchport mode access
!
interface port1.0.3
 speed 1000
 duplex full
 switchport
 switchport mode access
!
interface port1.0.4
 duplex full
 switchport
 switchport mode access
!
interface vlan1
 ip address 192.168.5.2/24
 ipv6 enable
 ipv6 address dhcp
 ip dhcp-client vendor-identifying-class
 ip dhcp-client request vendor-identifying-specific
!

"""
RETURN = """
before:
  description: The configuration prior to the model invocation.
  returned: always
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
after:
  description: The resulting configuration model invocation.
  returned: when changed
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
commands:
  description: The set of commands pushed to the remote device.
  returned: always
  type: list
  sample: ['command 1', 'command 2', 'command 3']
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.awplus.argspec.interfaces.interfaces import InterfacesArgs
from ansible.module_utils.network.awplus.config.interfaces.interfaces import Interfaces


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=InterfacesArgs.argument_spec,
                           supports_check_mode=True)

    result = Interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
