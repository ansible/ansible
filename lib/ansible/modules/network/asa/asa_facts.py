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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: asa_facts
version_added: "2.10"
author:
  - "Sumit Jaiswal (@justjais)"
short_description: Collect facts from remote devices running Cisco ASA
description:
  - Collects a base set of device facts from a remote device that
    is running ASA.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
  - Note, to collects facts from ASA device properly user should
    elevate the privilege to become.
extends_documentation_fragment: asa
notes:
  - Tested against asa 9.10(1)11
options:
  gather_subset:
    description:
      - When supplied, this argument restricts the facts collected
         to a given subset.
      - Possible values for this argument include
         C(all), C(min), C(hardware), C(config).
      - Specify a list of values to include a larger subset.
      - Use a value with an initial C(!) to collect all facts except that subset.
    required: false
    type: list
    default: '!config'
  gather_network_resources:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset. Possible values for this argument include
        all and the resources like interfaces, vlans etc.
        Can specify a list of values to include a larger subset.
        Values can also be used with an initial C(M(!)) to specify that
        a specific subset should not be collected.
        Valid subsets are 'all'.
    required: false
    type: list
"""

EXAMPLES = """
- name: Gather all legacy facts
  asa_facts:
    gather_subset: all

- name: Gather only the config and default facts
  asa_facts:
    gather_subset:
      - config

- name: Do not gather hardware facts
  asa_facts:
    gather_subset:
      - "!hardware"

- name: Gather legacy and resource facts
  asa_facts:
    gather_subset: all
"""

RETURN = """
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
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
ansible_net_firepower_version:
  description: The Firepower operating system version running on the remote device.
  returned: always
  type: str
ansible_net_device_mgr_version:
  description: The Device manager version running on the remote device.
  returned: always
  type: str
ansible_net_asatype:
  description: The operating system type (Cisco ASA) running on the remote device.
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
ansible_net_stacked_models:
  description: The model names of each device in the stack
  returned: when multiple devices are configured in a stack
  type: list
ansible_net_stacked_serialnums:
  description: The serial numbers of each device in the stack
  returned: when multiple devices are configured in a stack
  type: list
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
ansible_net_filesystems_info:
  description: A hash of all file systems containing info about each file system (e.g. free and total space)
  returned: when hardware is configured
  type: dict
ansible_net_memfree_mb:
  description: The available free memory on the remote device in Mb
  returned: when hardware is configured
  type: int
ansible_net_memused_mb:
  description: The used memory on the remote device in Mb
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
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.asa.argspec.facts.facts import FactsArgs
from ansible.module_utils.network.asa.facts.facts import Facts
from ansible.module_utils.network.asa.asa import asa_argument_spec


def main():
    """
    Main entry point for module execution

    :returns: ansible_facts
    """
    argument_spec = FactsArgs.argument_spec
    argument_spec.update(asa_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = []
    if module.params["gather_subset"] == "!config":
        warnings.append('default value for `gather_subset` will be changed to `min` from `!config` v2.11 onwards')

    result = Facts(module).get_facts()

    ansible_facts, additional_warnings = result
    warnings.extend(additional_warnings)

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
