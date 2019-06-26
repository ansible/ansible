#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The module file for nxos_facts
"""

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network. \
    nxos.facts.facts import Facts

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': [u'preview'],
                    'supported_by': '<support_group>'}


DOCUMENTATION = """
---
module: nxos_facts
version_added: 2.9
short_description: Get facts about nxos devices.
description:
  - Collects facts from network devices running the nxos operating
    system. This module places the facts gathered in the fact tree keyed by the
    respective resource name.  The facts module will always collect a
    base set of facts from the device and can enable or disable
    collection of additional facts.
author: Mike Wiebe (@mikewiebe)
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset. Possible values for this argument include
        all, min, hardware, config, legacy, and interfaces. Can specify a
        list of values to include a larger subset. Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    required: false
    default: 'all'
    version_added: "2.2"
  gather_network_resources:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset. Possible values for this argument include
        all and the resources like interfaces, vlans etc.
        Can specify a list of values to include a larger subset. Values
        can also be used with an initial C(M(!)) to specify that a
        specific subset should not be collected.
    required: false
    version_added: "2.9"
"""

EXAMPLES = """
# Gather all facts
- nxos_facts:
    gather_subset: all
    gather_network_resources: all

# Collect only the tms_global facts
- nxos_facts:
    gather_subset:
      - !all
      - !min
    gather_network_resources:
      - tms_global

# Do not collect tms_global facts
- nxos_facts:
    gather_network_resources:
      - "!tms_global"

# Collect tms_global and minimal default facts
- nxos_facts:
    gather_subset: min
    gather_network_resources: tms_global
"""

RETURN = """
See the respective resource module parameters for the tree.
"""


def main():
    """
    Main entry point for module execution

    :returns: ansible_facts
    """
    module = AnsibleModule(argument_spec=Facts.argument_spec,
                           supports_check_mode=True)
    warnings = ['default value for `gather_subset` \
                will be changed to `min` from `!config` v2.11 onwards']

    connection = Connection(module._socket_path)  # pylint: disable=W0212
    gather_subset = module.params['gather_subset']
    gather_network_resources = module.params['gather_network_resources']
    result = Facts().get_facts(module, connection, gather_subset,
                               gather_network_resources)

    ansible_facts, additional_warnings = result
    warnings.extend(additional_warnings)

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
