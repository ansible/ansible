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
The module file for junos_lacp_interfaces
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
module: junos_lacp_interfaces
version_added: 2.9
short_description: Manage Link Aggregation Control Protocol (LACP) attributes of interfaces on Juniper JUNOS devices.
description:
  - This module manages Link Aggregation Control Protocol (LACP) attributes of interfaces on Juniper JUNOS devices.
author: Ganesh Nalawade (@ganeshrn)
options:
  config:
    description: The list of dictionaries of LACP interfaces options.
    type: list
    elements: dict
    suboptions:
      name:
        description:
          - Name Identifier of the interface or link aggregation group.
        type: str
      period:
        description:
          - Timer interval for periodic transmission of LACP packets. If the value is
            set to C(fast) the packets are received every second and if the value is
            C(slow) the packets are received every 30 seconds. This value is applicable
            for aggregate interface only.
        type: str
        choices: ['fast', 'slow']
      sync_reset:
        description:
          - The argument notifies minimum-link failure out of sync to peer. If the value
            is C(disable) it disables minimum-link failure handling at LACP level and if
            value is C(enable) it enables minimum-link failure handling at LACP level.
            This value is applicable for aggregate interface only.
        type: str
        choices: ['disable', 'enable']
      force_up:
        description:
          - This is a boolean argument to control if the port should be up in absence
            of received link Aggregation Control Protocol Data Unit (LACPDUS).
            This value is applicable for member interfaces only.
        type: bool
      port_priority:
        description:
          - Priority of the member port. This value is applicable for member interfaces only.
          - Refer to vendor documentation for valid values.
        type: int
      system:
        description:
          - This dict object contains configurable options related to LACP
            system parameters for the link aggregation group.
            This value is applicable for aggregate interface only.
        type: dict
        suboptions:
          priority:
            description:
              - Specifies the system priority to use in LACP negotiations for
                the bundle.
              - Refer to vendor documentation for valid values.
            type: int
          mac:
            description:
              - Specifies the system ID to use in LACP negotiations for
                the bundle, encoded as a MAC address.
            type: dict
            suboptions:
                address:
                  description:
                    - The system ID to use in LACP negotiations.
                  type: str
  state:
    description:
      - The state of the configuration after module completion.
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
# user@junos01# show interfaces
# ge-0/0/2 {
#     ether-options {
#         802.3ad ae4;
#     }
# }
# ge-0/0/3 {
#    ether-options {
#         802.3ad ae0;
#     }
# }
# ae0 {
#     description "lag interface merged";
#     aggregated-ether-options {
#         lacp {
#             passive;
#         }
#     }
# }
# ae4 {
#     description "test aggregate interface";
#     aggregated-ether-options {
#         lacp {
#             passive;
#             link-protection;
#         }
#     }
# }

- name: Merge provided configuration with device configuration
  junos_lacp_interfaces:
    config:
      - name: ae0
        period: fast
        sync_reset: enable
        system:
          priority: 100
          mac:
            address: 00:00:00:00:00:02
      - name: ge-0/0/3
        port_priority: 100
        force_up: True
    state: merged

# After state:
# -------------
# user@junos01# show interfaces
# ge-0/0/2 {
#     ether-options {
#         802.3ad ae4;
#     }
# }
# ge-0/0/3 {
#     ether-options {
#         802.3ad {
#             lacp {
#                 force-up;
#                 port-priority 100;
#             }
#             ae0;
#         }
#     }
# }
# ae0 {
#     description "lag interface merged";
#     aggregated-ether-options {
#         lacp {
#             passive;
#             periodic fast;
#             sync-reset enable;
#             system-priority 100;
#             system-id 00:00:00:00:00:02;
#         }
#     }
# }
# ae4 {
#     description "test aggregate interface";
#     aggregated-ether-options {
#         lacp {
#             passive;
#             link-protection;
#         }
#     }
# }

# Using replaced
# Before state:
# -------------
# user@junos01# show interfaces
# ge-0/0/2 {
#     ether-options {
#         802.3ad ae4;
#     }
# }
# ge-0/0/3 {
#     ether-options {
#         802.3ad {
#             lacp {
#                 force-up;
#                 port-priority 100;
#             }
#             ae0;
#         }
#     }
# }
# ae0 {
#     description "lag interface merged";
#     aggregated-ether-options {
#         lacp {
#             passive;
#             periodic fast;
#             sync-reset enable;
#             system-priority 100;
#             system-id 00:00:00:00:00:02;
#         }
#     }
# }
# ae4 {
#     description "test aggregate interface";
#     aggregated-ether-options {
#         lacp {
#             passive;
#             link-protection;
#         }
#     }
# }

- name: Replace device LACP interfaces configuration with provided configuration
  junos_lacp_interfaces:
    config:
      - name: ae0
        period: slow
    state: replaced

# After state:
# -------------
# user@junos01# show interfaces
# ge-0/0/2 {
#     ether-options {
#         802.3ad ae4;
#     }
# }
# ge-0/0/3 {
#     ether-options {
#         802.3ad {
#             lacp {
#                 force-up;
#                 port-priority 100;
#             }
#             ae0;
#         }
#     }
# }
# ae0 {
#     description "lag interface merged";
#     aggregated-ether-options {
#         lacp {
#             passive;
#             periodic slow;
#         }
#     }
# }
# ae4 {
#     description "test aggregate interface";
#     aggregated-ether-options {
#         lacp {
#             passive;
#             link-protection;
#         }
#     }
# }

# Using overridden
# Before state:
# -------------
# user@junos01# show interfaces
# ge-0/0/2 {
#     ether-options {
#         802.3ad ae4;
#     }
# }
# ge-0/0/3 {
#     ether-options {
#         802.3ad {
#             lacp {
#                 force-up;
#                 port-priority 100;
#             }
#             ae0;
#         }
#     }
# }
# ae0 {
#     description "lag interface merged";
#     aggregated-ether-options {
#         lacp {
#             passive;
#             periodic slow;
#         }
#     }
# }
# ae4 {
#     description "test aggregate interface";
#     aggregated-ether-options {
#         lacp {
#             passive;
#             link-protection;
#         }
#     }
# }

- name: Overrides all device LACP interfaces configuration with provided configuration
  junos_lacp_interfaces:
    config:
      - name: ae0
        system:
          priority: 300
          mac:
            address: 00:00:00:00:00:03
      - name: ge-0/0/2
        port_priority: 200
        force_up: False
    state: overridden

# After state:
# -------------
# user@junos01# show interfaces
# ge-0/0/2 {
#     ether-options {
#         802.3ad {
#             lacp {
#                 port-priority 200;
#             }
#             ae4;
#         }
#     }
# }
# ge-0/0/3 {
#     ether-options {
#         802.3ad {
#             lacp {
#                 force-up;
#                 port-priority 100;
#             }
#             ae0;
#         }
#     }
# }
# ae0 {
#     description "lag interface merged";
#     aggregated-ether-options {
#         lacp {
#             passive;
#             system-priority 300;
#             system-id 00:00:00:00:00:03;
#         }
#     }
# }
# ae4 {
#     description "test aggregate interface";
#     aggregated-ether-options {
#         lacp {
#             passive;
#             link-protection;
#         }
#     }
# }

# Using deleted
# Before state:
# -------------
# user@junos01# show interfaces
# ge-0/0/2 {
#     ether-options {
#         802.3ad {
#             lacp {
#                 port-priority 200;
#             }
#             ae4;
#         }
#     }
# }
# ge-0/0/3 {
#     ether-options {
#         802.3ad {
#             lacp {
#                 force-up;
#                 port-priority 100;
#             }
#             ae0;
#         }
#     }
# }
# ae0 {
#     description "lag interface merged";
#     aggregated-ether-options {
#         lacp {
#             passive;
#             system-priority 300;
#             system-id 00:00:00:00:00:03;
#         }
#     }
# }
# ae4 {
#     description "test aggregate interface";
#     aggregated-ether-options {
#         lacp {
#             passive;
#             link-protection;
#         }
#     }
# }

- name: "Delete LACP interfaces attributes of given interfaces (Note: This won't delete the interface itself)"
  junos_lacp_interfaces:
    config:
      - name: ae0
      - name: ge-0/0/3
      - name: ge-0/0/2
    state: deleted

# After state:
# -------------
# user@junos01# show interfaces
# ge-0/0/2 {
#     ether-options {
#         802.3ad ae4;
#     }
# }
# ge-0/0/3 {
#    ether-options {
#         802.3ad ae0;
#     }
# }
# ae0 {
#     description "lag interface merged";
#     aggregated-ether-options {
#         lacp {
#             passive;
#         }
#     }
# }
# ae4 {
#     description "test aggregate interface";
#     aggregated-ether-options {
#         lacp {
#             passive;
#             link-protection;
#         }
#     }
# }
"""

RETURN = """
before:
  description: The configuration as structured data prior to module invocation.
  returned: always
  type: list
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
after:
  description: The configuration as structured data after module completion.
  returned: when changed
  type: list
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
from ansible.module_utils.network.junos.argspec.lacp_interfaces.lacp_interfaces import Lacp_interfacesArgs
from ansible.module_utils.network.junos.config.lacp_interfaces.lacp_interfaces import Lacp_interfaces


def main():
    """
    Main entry point for module execution
    :returns: the result form module invocation
    """
    required_if = [('state', 'merged', ('config',)),
                   ('state', 'replaced', ('config',)),
                   ('state', 'overridden', ('config',))]

    module = AnsibleModule(argument_spec=Lacp_interfacesArgs.argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    result = Lacp_interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
