#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2020, A10 Networks Inc.
# GNU General Public License v3.0
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: acos_facts
short_description: Collect facts from remote devices running A10 ACOS
description:
  - Collects a base set of device facts from a remote device that
    is running ACOS.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will collect a base set of facts from the device
    and can enable or disable collection of additional facts.
notes:
  - Tested against ACOS 4.1.1-P9
options:
  gather_subset:
    description:
      - When supplied, this argument restricts the facts collected
         to a given subset.
      - Possible values for this argument include
         all, hardware, config and interfaces
      - Specify a list of comma seperated values (without spaces) to include
         a larger subset.
    required: false
    default: 'all'
'''

EXAMPLES = r'''
  tasks:
    - name: collect all the facts
      acos_facts:
        gather_subset: all

    - name: collect only the config and default facts
      acos_facts:
        gather_subset:
          - config

    - name: do not collect hardware facts
      acos_facts:
        gather_subset:
          - "!hardware"
'''

RETURN = r'''
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list
ansible_net_model:
  description: The model name returned from the device
  returned: always
  type: str
ansible_net_hostid:
  description: The hostid returned from the device
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

# hardware
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
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.a10.acos import acos_argument_spec
from ansible.module_utils.network.a10.facts.facts import Facts


class FactsArgs(object):
    """ The arg spec for the acos_facts module """

    argument_spec = {
        'gather_subset': dict(default=['!config'], type='list')
    }


def main():
    """ Main entry point for AnsibleModule """
    argument_spec = FactsArgs.argument_spec
    argument_spec.update(acos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = []
    ansible_facts, additional_warnings = Facts(module).get_facts()
    warnings.extend(additional_warnings)

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
