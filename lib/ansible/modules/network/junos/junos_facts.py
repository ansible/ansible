#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: junos_facts
version_added: "2.1"
author: "Nathaniel Case (@Qalthos)"
short_description: Collect facts from remote devices running Juniper Junos
description:
  - Collects fact information from a remote device running the Junos
    operating system.  By default, the module will collect basic fact
    information from the device to be included with the hostvars.
    Additional fact information can be collected based on the
    configured set of arguments.
extends_documentation_fragment: junos
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        all, hardware, config, and interfaces.  Can specify a list of
        values to include a larger subset.  Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected. To maintain backward compatibility old style facts
        can be retrieved by explicitly adding C(ofacts)  to value, this requires
        junos-eznc to be installed as a prerequisite. Valid value of gather_subset
        are default, hardware, config, interfaces, ofacts. If C(ofacts) is present in the
        list it fetches the old style facts (fact keys without 'ansible_' prefix) and it requires
        junos-eznc library to be installed on control node and the device login credentials
        must be given in C(provider) option.
    required: false
    default: ['!config']
    version_added: "2.3"
  config_format:
    description:
      - The I(config_format) argument specifies the format of the configuration
         when serializing output from the device. This argument is applicable
         only when C(config) value is present in I(gather_subset).
         The I(config_format) should be supported by the junos version running on
         device. This value is not applicable while fetching old style facts that is
         when C(ofacts) value is present in value if I(gather_subset) value. This option
         is valid only for C(gather_subset) values.
    required: false
    default: 'text'
    choices: ['xml', 'text', 'set', 'json']
    version_added: "2.3"
  gather_network_resources:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset. Possible values for this argument include
        all and the resources like interfaces, vlans etc.
        Can specify a list of values to include a larger subset.
        Values can also be used with an initial C(M(!)) to specify that
        a specific subset should not be collected.
        Valid subsets are 'all', 'interfaces', 'lacp', 'lacp_interfaces',
              'lag_interfaces', 'l2_interfaces', 'l3_interfaces', 'lldp_global',
              'lldp_interfaces', 'vlans'.
    required: false
    version_added: "2.9"
requirements:
  - ncclient (>=v0.5.2)
notes:
  - Ensure I(config_format) used to retrieve configuration from device
    is supported by junos version running on device.
  - With I(config_format = json), configuration in the results will be a dictionary(and not a JSON string)
  - This module requires the netconf system service be enabled on
    the remote device being managed.
  - Tested against vSRX JUNOS version 15.1X49-D15.4, vqfx-10000 JUNOS Version 15.1X53-D60.4.
  - Recommended connection is C(netconf). See L(the Junos OS Platform Options,../network/user_guide/platform_junos.html).
  - This module also works with C(local) connections for legacy playbooks.
  - Fetching old style facts requires junos-eznc library to be installed on control node and the device login credentials
    must be given in provider option.
"""

EXAMPLES = """
- name: collect default set of facts
  junos_facts:

- name: collect default set of facts and configuration
  junos_facts:
    gather_subset: config

- name: Gather legacy and resource facts
  junos_facts:
    gather_subset: all
    gather_network_resources: all
"""

RETURN = """
ansible_facts:
  description: Returns the facts collect from the device
  returned: always
  type: dict
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.junos.argspec.facts.facts import FactsArgs
from ansible.module_utils.network.junos.facts.facts import Facts
from ansible.module_utils.network.junos.junos import junos_argument_spec


def main():
    """ Main entry point for AnsibleModule
    """
    argument_spec = FactsArgs.argument_spec
    argument_spec.update(junos_argument_spec)

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
