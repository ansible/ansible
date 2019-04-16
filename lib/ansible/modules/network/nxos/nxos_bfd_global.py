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
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = '''
---
module: nxos_bfd_global
extends_documentation_fragment: nxos
version_added: "2.9"
short_description: Bidirectional Forwarding Detection (BFD) global-level configuration
description:
  - Manages Bidirectional Forwarding Detection (BFD) global-level configuration.

author: Chris Van Heuveln (@chrisvanheuveln)
notes:
    - Tested against NXOSv 9.2(2)
    - BFD global will automatically enable 'feature bfd' if it is disabled.
    - BFD global does not have a 'state' parameter. All of the BFD commands
      are unique and are defined if 'feature bfd' is enabled.
options:
  echo_interface:
    description:
      - Loopback interface used for echo frames.
        Valid values are loopback interface name or an empty string ''.
      - Not supported on N5K/N6K
    required: false
    type: str
  echo_rx_interval:
    description:
      - BFD Echo receive interval in milliseconds.
    required: false
    type: int
  interval:
    description:
      - BFD interval timer values.
        Valid values are a list of ints defining [interval, min_rx, multiplier]
    required: false
    type: list
  slow_timer:
    description:
      - BFD slow rate timer in milliseconds.
    required: false
    type: int
  startup_timer:
    description:
      - BFD delayed startup timer in seconds.
      - Not supported on N5K/N6K/N7K
    required: false
    type: int

  # IPv4/IPv6 specific commands
  ipv4_echo_rx_interval:
    description:
      - BFD IPv4 session echo receive interval in milliseconds.
    required: false
    type: int
  ipv4_interval:
    description:
      - BFD IPv4 interval timer values.
        Valid values are a list of ints defining [interval, min_rx, multiplier]
    required: false
    type: list
  ipv4_slow_timer:
    description:
      - BFD IPv4 slow rate timer in milliseconds.
    required: false
    type: int
  ipv6_echo_rx_interval:
    description:
      - BFD IPv6 session echo receive interval in milliseconds.
    required: false
    type: int
  ipv6_interval:
    description:
      - BFD IPv6 interval timer values.
        Valid values are a list of ints defining [interval, min_rx, multiplier]
    required: false
    type: list
  ipv6_slow_timer:
    description:
      - BFD IPv6 slow rate timer in milliseconds.
    required: false
    type: int

  # Fabricpath commands
  fabricpath_interval:
    description:
      - BFD fabricpath interval timer values.
        Valid values are a list of ints defining [interval, min_rx, multiplier]
    required: false
    type: list
  fabricpath_slow_timer:
    description:
      - BFD fabricpath slow rate timer in milliseconds.
    required: false
    type: int
  fabricpath_vlan:
    description:
      - BFD fabricpath control vlan.
    required: false
    type: int

'''
EXAMPLES = '''
- nxos_bfd_global:
    echo_interface: Ethernet1/2
    echo_interval: [50, 50, 3]
    state: present
'''

RETURN = '''
cmds:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["bfd echo-interface loopback1", "bfd slow-timer 2000"]
'''


import re, yaml

from ansible.module_utils.network.nxos.nxos import NxosCmdRef
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.network.nxos.nxos import load_config, run_commands, get_capabilities
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.config import CustomNetworkConfig

BFD_CMD_REF = """
# The cmd_ref is a yaml formatted list of module commands.
# A leading underscore denotes a non-command variable; e.g. _template.
# BFD does not have convenient json data so this cmd_ref uses raw cli configs.
---
_template: # _template holds common settings for all commands
  # Enable feature bfd if disabled
  feature: bfd
  # Common get syntax for BFD commands
  get_command: show run bfd all | incl '^(no )*bfd'

echo_interface:
  kind: str
  getval: (no )*bfd echo-interface *(\S+)*$
  setval: '{0}bfd echo-interface {1}'
  default: ''

echo_rx_interval:
  kind: int
  getval: bfd echo-rx-interval (\d+)$
  setval: bfd echo-rx-interval {0}
  default: 50
  N3K:
    default: 250

interval:
  kind: list
  getval: bfd interval (\d+) min_rx (\d+) multiplier (\d+)
  setval: bfd interval {0} min_rx {1} multiplier {2}
  default: [50,50,3]
  N3K:
    default: [250,250,3]

slow_timer:
  kind: int
  getval: bfd slow-timer (\d+)$
  setval: bfd slow-timer {0}
  default: 2000

startup_timer:
  _exclude: ['N5K', 'N6K', 'N7K']
  kind: int
  getval: bfd startup-timer (\d+)$
  setval: bfd startup-timer {0}
  default: 5

# IPv4/IPv6 specific commands
ipv4_echo_rx_interval:
  _exclude: ['N5K', 'N6K']
  kind: int
  getval: bfd ipv4 echo-rx-interval (\d+)$
  setval: bfd ipv4 echo-rx-interval {0}
  default: 50
  N3K:
    default: 250

ipv4_interval:
  _exclude: ['N5K', 'N6K']
  kind: list
  getval: bfd ipv4 interval (\d+) min_rx (\d+) multiplier (\d+)
  setval: bfd ipv4 interval {0} min_rx {1} multiplier {2}
  default: [50,50,3]
  N3K:
    default: [250,250,3]

ipv4_slow_timer:
  _exclude: ['N5K', 'N6K']
  kind: int
  getval: bfd ipv4 slow-timer (\d+)$
  setval: bfd ipv4 slow-timer {0}
  default: 2000

ipv6_echo_rx_interval:
  _exclude: ['N5K', 'N6K']
  kind: int
  getval: bfd ipv6 echo-rx-interval (\d+)$
  setval: bfd ipv6 echo-rx-interval {0}
  default: 50
  N3K:
    default: 250

ipv6_interval:
  _exclude: ['N5K', 'N6K']
  kind: list
  getval: bfd ipv6 interval (\d+) min_rx (\d+) multiplier (\d+)
  setval: bfd ipv6 interval {0} min_rx {1} multiplier {2}
  default: [50,50,3]
  N3K:
    default: [250,250,3]

ipv6_slow_timer:
  _exclude: ['N5K', 'N6K']
  kind: int
  getval: bfd ipv6 slow-timer (\d+)$
  setval: bfd ipv6 slow-timer {0}
  default: 2000

# Fabricpath Commands
fabricpath_interval:
  _exclude: ['N3K', 'N9K']
  kind: list
  getval: bfd fabricpath interval (\d+) min_rx (\d+) multiplier (\d+)
  setval: bfd fabricpath interval {0} min_rx {1} multiplier {2}
  default: [50,50,3]

fabricpath_slow_timer:
  _exclude: ['N3K', 'N9K']
  kind: int
  getval: bfd fabricpath slow-timer (\d+)$
  setval: bfd fabricpath slow-timer {0}
  default: 2000

fabricpath_vlan:
  _exclude: ['N3K', 'N9K']
  kind: int
  getval: bfd fabricpath vlan (\d+)$
  setval: bfd fabricpath vlan {0}
  default: 1
"""


def main():
    argument_spec = dict(
        echo_interface=dict(required=False, type='str'),
        echo_rx_interval=dict(required=False, type='int'),
        interval=dict(required=False, type='list'),
        slow_timer=dict(required=False, type='int'),
    )
    argument_spec.update(nxos_argument_spec)
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    warnings = list()
    check_args(module, warnings)

    cmd_ref = NxosCmdRef(module, BFD_CMD_REF)
    cmd_ref.get_existing()
    cmd_ref.get_playvals()
    cmds = cmd_ref.get_proposed()

    result = {'changed': False, 'commands': cmds, 'warnings': warnings,
              'check_mode': module.check_mode}
    if cmds:
        result['changed'] = True
        if not module.check_mode:
            load_config(module, cmds)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
