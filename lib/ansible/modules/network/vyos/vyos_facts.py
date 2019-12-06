#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The module file for vyos_facts
"""


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': [u'preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: vyos_facts
version_added: 2.2
short_description: Get facts about vyos devices.
description:
  - Collects facts from network devices running the vyos operating
    system. This module places the facts gathered in the fact tree keyed by the
    respective resource name.  The facts module will always collect a
    base set of facts from the device and can enable or disable
    collection of additional facts.
author:
  - Nathaniel Case (@qalthos)
  - Nilashish Chakraborty (@Nilashishc)
  - Rohit Thakur (@rohitthakur2590)
extends_documentation_fragment: vyos
notes:
  - Tested against VyOS 1.1.8 (helium).
  - This module works with connection C(network_cli). See L(the VyOS OS Platform Options,../network/user_guide/platform_vyos.html).
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        all, default, config, and neighbors. Can specify a list of
        values to include a larger subset. Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    required: false
    default: "!config"
  gather_network_resources:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset. Possible values for this argument include
        all and the resources like interfaces.
        Can specify a list of values to include a larger subset. Values
        can also be used with an initial C(M(!)) to specify that a
        specific subset should not be collected.
        Valid subsets are 'all', 'interfaces', 'l3_interfaces', 'lag_interfaces',
        'lldp_global', 'lldp_interfaces'.
    required: false
    version_added: "2.9"
"""

EXAMPLES = """
# Gather all facts
- vyos_facts:
    gather_subset: all
    gather_network_resources: all

# collect only the config and default facts
- vyos_facts:
    gather_subset: config

# collect everything exception the config
- vyos_facts:
    gather_subset: "!config"

# Collect only the interfaces facts
- vyos_facts:
    gather_subset:
      - '!all'
      - '!min'
    gather_network_resources:
      - interfaces

# Do not collect interfaces facts
- vyos_facts:
    gather_network_resources:
      - "!interfaces"

# Collect interfaces and minimal default facts
- vyos_facts:
    gather_subset: min
    gather_network_resources: interfaces
"""

RETURN = """
ansible_net_config:
  description: The running-config from the device
  returned: when config is configured
  type: str
ansible_net_commits:
  description: The set of available configuration revisions
  returned: when present
  type: list
ansible_net_hostname:
  description: The configured system hostname
  returned: always
  type: str
ansible_net_model:
  description: The device model string
  returned: always
  type: str
ansible_net_serialnum:
  description: The serial number of the device
  returned: always
  type: str
ansible_net_version:
  description: The version of the software running
  returned: always
  type: str
ansible_net_neighbors:
  description: The set of LLDP neighbors
  returned: when interface is configured
  type: list
ansible_net_gather_subset:
  description: The list of subsets gathered by the module
  returned: always
  type: list
ansible_net_api:
  description: The name of the transport
  returned: always
  type: str
ansible_net_python_version:
  description: The Python version Ansible controller is using
  returned: always
  type: str
ansible_net_gather_network_resources:
  description: The list of fact resource subsets collected from the device
  returned: always
  type: list
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.vyos.argspec.facts.facts import FactsArgs
from ansible.module_utils.network.vyos.facts.facts import Facts
from ansible.module_utils.network.vyos.vyos import vyos_argument_spec


def main():
    """
    Main entry point for module execution

    :returns: ansible_facts
    """
    argument_spec = FactsArgs.argument_spec

    argument_spec.update(vyos_argument_spec)

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
