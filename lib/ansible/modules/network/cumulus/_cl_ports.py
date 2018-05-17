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
module: cl_ports
version_added: "2.1"
author: "Cumulus Networks (@CumulusNetworks)"
short_description: Configure Cumulus Switch port attributes (ports.conf)
deprecated:
  removed_in: "2.5"
  why: The M(nclu) module is designed to be easier to use for individuals who are new to Cumulus Linux by exposing the NCLU interface in an automatable way.
  alternative: Use M(nclu) instead.
description:
    - Set the initial port attribute defined in the Cumulus Linux ports.conf,
      file. This module does not do any error checking at the moment. Be careful
      to not include ports that do not exist on the switch. Carefully read the
      original ports.conf file for any exceptions or limitations.
      For more details go the Configure Switch Port Attribute Documentation at
      U(http://docs.cumulusnetworks.com).
options:
    speed_10g:
        description:
            - List of ports to run initial run at 10G.
    speed_40g:
        description:
            - List of ports to run initial run at 40G.
    speed_4_by_10g:
        description:
            - List of 40G ports that will be unganged to run as 4 10G ports.
    speed_40g_div_4:
        description:
            - List of 10G ports that will be ganged to form a 40G port.
'''
EXAMPLES = '''
# Use cl_ports module to manage the switch attributes defined in the
# ports.conf file on Cumulus Linux

## Unganged port configuration on certain ports
- name: configure ports.conf setup
  cl_ports:
    speed_4_by_10g:
      - swp1
      - swp32
    speed_40g:
      - swp2-31

## Unganged port configuration on certain ports
- name: configure ports.conf setup
  cl_ports:
    speed_4_by_10g:
      - swp1-3
      - swp6
    speed_40g:
      - swp4-5
      - swp7-32
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
