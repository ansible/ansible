#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The module file for iosxr_facts
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': [u'preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: iosxr_facts
version_added: 2.2
short_description: Get facts about iosxr devices.
extends_documentation_fragment: iosxr
description:
  - Collects facts from network devices running the iosxr operating
    system. This module places the facts gathered in the fact tree keyed by the
    respective resource name.  The facts module will always collect a
    base set of facts from the device and can enable or disable
    collection of additional facts.
notes:
  - Tested against IOS-XR 6.1.3.
  - This module works with connection C(network_cli). See L(the IOS-XR Platform Options,../network/user_guide/platform_iosxr.html).
author:
  - Ricardo Carrillo Cruz (@rcarrillocruz)
  - Nilashish Chakraborty (@Nilashishc)
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        all, hardware, config, and interfaces.  Can specify a list of
        values to include a larger subset.  Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    required: false
    default: '!config'
  gather_network_resources:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset. Possible values for this argument include
        all and the resources like interfaces, lacp etc.
        Can specify a list of values to include a larger subset. Values
        can also be used with an initial C(M(!)) to specify that a
        specific subset should not be collected.
        Valid subsets are 'all', 'lacp', 'lacp_interfaces', 'lldp_global',
        'lldp_interfaces', 'interfaces', 'l2_interfaces', 'l3_interfaces',
        'lag_interfaces'.
    required: false
    version_added: "2.9"
"""

EXAMPLES = """
# Gather all facts
- iosxr_facts:
    gather_subset: all
    gather_network_resources: all

# Collect only the config and default facts
- iosxr_facts:
    gather_subset:
      - config

# Do not collect hardware facts
- iosxr_facts:
    gather_subset:
      - "!hardware"

# Collect only the lacp facts
- iosxr_facts:
    gather_subset:
      - "!all"
      - "!min"
    gather_network_resources:
      - lacp

# Do not collect lacp_interfaces facts
- iosxr_facts:
    gather_network_resources:
      - "!lacp_interfaces"

# Collect lacp and minimal default facts
- iosxr_facts:
    gather_subset: min
    gather_network_resources: lacp

# Collect only the interfaces facts
- iosxr_facts:
    gather_subset:
      - "!all"
      - "!min"
    gather_network_resources:
      - interfaces
      - l2_interfaces
"""

RETURN = """
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list

# default
ansible_net_version:
  description: The operating system version running on the remote device
  returned: always
  type: str
ansible_net_hostname:
  description: The configured hostname of the device
  returned: always
  type: str
ansible_net_image:
  description: The image file the device is running
  returned: always
  type: str
ansible_net_api:
  description: The name of the transport
  returned: always
  type: str
ansible_net_python_version:
  description: The Python version Ansible controller is using
  returned: always
  type: str
ansible_net_model:
  description: The model name returned from the device
  returned: always
  type: str

# hardware
ansible_net_filesystems:
  description: All file system names available on the device
  returned: when hardware is configured
  type: list
ansible_net_memfree_mb:
  description: The available free memory on the remote device in Mb
  returned: when hardware is configured
  type: int
ansible_net_memtotal_mb:
  description: The total memory on the remote device in Mb
  returned: when hardware is configured
  type: int

# config
ansible_net_config:
  description: The current active config from the device
  returned: when config is configured
  type: str

# interfaces
ansible_net_all_ipv4_addresses:
  description: All IPv4 addresses configured on the device
  returned: when interfaces is configured
  type: list
ansible_net_all_ipv6_addresses:
  description: All IPv6 addresses configured on the device
  returned: when interfaces is configured
  type: list
ansible_net_interfaces:
  description: A hash of all interfaces running on the system
  returned: when interfaces is configured
  type: dict
ansible_net_neighbors:
  description: The list of LLDP neighbors from the remote device
  returned: when interfaces is configured
  type: dict

# network resources
ansible_net_gather_network_resources:
  description: The list of fact resource subsets collected from the device
  returned: always
  type: list
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.iosxr.iosxr import iosxr_argument_spec
from ansible.module_utils.network.iosxr.argspec.facts.facts import FactsArgs
from ansible.module_utils.network.iosxr.facts.facts import Facts


def main():
    """
    Main entry point for module execution

    :returns: ansible_facts
    """
    spec = FactsArgs.argument_spec
    spec.update(iosxr_argument_spec)

    module = AnsibleModule(argument_spec=spec,
                           supports_check_mode=True)
    warnings = ['default value for `gather_subset` '
                'will be changed to `min` from `!config` v2.11 onwards']

    result = Facts(module).get_facts()

    ansible_facts, additional_warnings = result
    warnings.extend(additional_warnings)

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
