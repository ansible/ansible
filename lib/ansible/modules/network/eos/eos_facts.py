#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: eos_facts
version_added: "2.2"
author:
  - "Peter Sprygada (@privateip)"
  - "Nathaniel Case (@Qalthos)"
short_description: Collect facts from remote devices running Arista EOS
description:
  - Collects facts from Arista devices running the EOS operating
    system. This module places the facts gathered in the fact tree keyed by the
    respective resource name.  The facts module will always collect a
    base set of facts from the device and can enable or disable
    collection of additional facts.
extends_documentation_fragment: eos
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
    type: list
    default: '!config'
  gather_network_resources:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset. Possible values for this argument include
        all and the resources like interfaces, vlans etc.
        Can specify a list of values to include a larger subset. Values
        can also be used with an initial C(M(!)) to specify that a
        specific subset should not be collected. Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
        Valid subsets are 'all', 'interfaces', 'l2_interfaces', 'l3_interfaces',
        'lacp', 'lacp_interfaces', 'lag_interfaces', 'lldp_global', 'lldp_interfaces',
        'vlans'.
    required: false
    type: list
    version_added: "2.9"
"""

EXAMPLES = """
- name: Gather all legacy facts
- eos_facts:
    gather_subset: all

- name: Gather only the config and default facts
  eos_facts:
    gather_subset:
      - config

- name: Do not gather hardware facts
  eos_facts:
    gather_subset:
      - "!hardware"

- name: Gather legacy and resource facts
  eos_facts:
    gather_subset: all
    gather_network_resources: all

- name: Gather only the interfaces resource facts and no legacy facts
- eos_facts:
    gather_subset:
      - '!all'
      - '!min'
    gather_network_resources:
      - interfaces

- name: Gather all resource facts and minimal legacy facts
  eos_facts:
    gather_subset: min
    gather_network_resources: all
"""

RETURN = """
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list

ansible_net_gather_network_resources:
  description: The list of fact for network resource subsets collected from the device
  returned: when the resource is configured
  type: list

# default
ansible_net_model:
  description: The model name returned from the device
  returned: always
  type: str
ansible_net_serialnum:
  description: The serial number of the remote device
  returned: always
  type: str
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
ansible_net_fqdn:
  description: The fully qualified domain name of the device
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
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.eos.argspec.facts.facts import FactsArgs
from ansible.module_utils.network.eos.facts.facts import Facts
from ansible.module_utils.network.eos.eos import eos_argument_spec


def main():
    """ Main entry point for module execution

    :returns: ansible_facts
    """
    argument_spec = FactsArgs.argument_spec
    argument_spec.update(eos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = ['default value for `gather_subset` '
                'will be changed to `min` from `!config` v2.11 onwards']

    result = Facts(module).get_facts()

    ansible_facts, additional_warnings = result
    warnings.extend(additional_warnings)

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
