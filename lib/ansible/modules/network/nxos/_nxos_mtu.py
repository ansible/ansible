#!/usr/bin/python
#
# This file is part of Ansible
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'network'}

DOCUMENTATION = '''
---
module: nxos_mtu
extends_documentation_fragment: nxos
version_added: "2.2"
deprecated:
  removed_in: "2.5"
  why: Replaced with common C(*_system) network modules.
  alternative: Use M(nxos_system)'s C(system_mtu) option. To specify an interfaces MTU use M(nxos_interface).
short_description: Manages MTU settings on Nexus switch.
description:
    - Manages MTU settings on Nexus switch.
author:
    - Jason Edelman (@jedelman8)
notes:
    - Tested against NXOSv 7.3.(0)D1(1) on VIRL
    - Either C(sysmtu) param is required or (C(interface) AND C(mtu)) parameters are required.
    - C(state=absent) unconfigures a given MTU if that value is currently present.
options:
    interface:
        description:
            - Full name of interface, i.e. Ethernet1/1.
    mtu:
        description:
            - MTU for a specific interface. Must be an even number between 576 and 9216.
    sysmtu:
        description:
            - System jumbo MTU. Must be an even number between 576 and 9216.
    state:
        description:
            - Specify desired state of the resource.
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
# Ensure system mtu is 9126
- nxos_mtu:
    sysmtu: 9216
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# Config mtu on Eth1/1 (routed interface)
- nxos_mtu:
    interface: Ethernet1/1
    mtu: 1600
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# Config mtu on Eth1/3 (switched interface)
- nxos_mtu:
    interface: Ethernet1/3
    mtu: 9216
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"

# Unconfigure mtu on a given interface
- nxos_mtu:
    interface: Ethernet1/3
    mtu: 9216
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
    state: absent
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"mtu": "1700"}
existing:
    description:
        - k/v pairs of existing mtu/sysmtu on the interface/system
    returned: always
    type: dict
    sample: {"mtu": "1600", "sysmtu": "9216"}
end_state:
    description: k/v pairs of mtu/sysmtu values after module execution
    returned: always
    type: dict
    sample: {"mtu": "1700", sysmtu": "9216"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["interface vlan10", "mtu 1700"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

from ansible.module_utils.common.removed import removed_module

if __name__ == '__main__':
    removed_module()
