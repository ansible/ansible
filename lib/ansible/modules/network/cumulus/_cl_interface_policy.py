#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Cumulus Networks <ce-ceng@cumulusnetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cl_interface_policy
version_added: "2.1"
author: "Cumulus Networks (@CumulusNetworks)"
short_description: Configure interface enforcement policy on Cumulus Linux
deprecated:
  removed_in: "2.5"
  why: The M(nclu) module is designed to be easier to use for individuals who are new to Cumulus Linux by exposing the NCLU interface in an automatable way.
  alternative: Use M(nclu) instead.
description:
    - This module affects the configuration files located in the interfaces
      folder defined by ifupdown2. Interfaces port and port ranges listed in the
      "allowed" parameter define what interfaces will be available on the
      switch. If the user runs this module and has an interface configured on
      the switch, but not found in the "allowed" list, this interface will be
      unconfigured. By default this is `/etc/network/interface.d`
      For more details go the Configuring Interfaces at
      U(http://docs.cumulusnetworks.com).
notes:
    - lo must be included in the allowed list.
    - eth0 must be in allowed list if out of band management is done
options:
    allowed:
        description:
            - List of ports to run initial run at 10G.
        required: true
    location:
        description:
            - Directory to store interface files.
        default: '/etc/network/interfaces.d/'
'''

EXAMPLES = '''
# Example playbook entries using the cl_interface_policy module.

    - name: shows types of interface ranges supported
      cl_interface_policy:
          allowed: "lo eth0 swp1-9, swp11, swp12-13s0, swp12-30s1, swp12-30s2, bond0-12"

'''

RETURN = '''
changed:
    description: whether the interface was changed
    returned: changed
    type: bool
    sample: True
msg:
    description: human-readable report of success or failure
    returned: always
    type: string
    sample: "interface bond0 config updated"
'''

from ansible.module_utils.common.removed import removed_module

if __name__ == '__main__':
    removed_module()
