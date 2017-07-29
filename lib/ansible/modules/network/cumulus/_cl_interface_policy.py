#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Cumulus Networks <ce-ceng@cumulusnetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cl_interface_policy
version_added: "2.1"
author: "Cumulus Networks (@CumulusNetworks)"
short_description: Configure interface enforcement policy on Cumulus Linux
deprecated: Deprecated in 2.3. Use M(nclu) instead.
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
import os
import re

from ansible.module_utils.basic import AnsibleModule


# get list of interface files that are currently "configured".
# doesn't mean actually applied to the system, but most likely are
def read_current_int_dir(module):
    module.custom_currentportlist = os.listdir(module.params.get('location'))


# take the allowed list and convert it to into a list
# of ports.
def convert_allowed_list_to_port_range(module):
    allowedlist = module.params.get('allowed')
    for portrange in allowedlist:
        module.custom_allowedportlist += breakout_portrange(portrange)


def breakout_portrange(prange):
    _m0 = re.match(r'(\w+[a-z.])(\d+)?-?(\d+)?(\w+)?', prange.strip())
    # no range defined
    if _m0.group(3) is None:
        return [_m0.group(0)]
    else:
        portarray = []
        intrange = range(int(_m0.group(2)), int(_m0.group(3)) + 1)
        for _int in intrange:
            portarray.append(''.join([_m0.group(1),
                                      str(_int),
                                      str(_m0.group(4) or '')
                                      ]
                                     )
                             )
        return portarray


# deletes the interface files
def unconfigure_interfaces(module):
    currentportset = set(module.custom_currentportlist)
    allowedportset = set(module.custom_allowedportlist)
    remove_list = currentportset.difference(allowedportset)
    fileprefix = module.params.get('location')
    module.msg = "remove config for interfaces %s" % (', '.join(remove_list))
    for _file in remove_list:
        os.unlink(fileprefix + _file)


# check to see if policy should be enforced
# returns true if policy needs to be enforced
# that is delete interface files
def int_policy_enforce(module):
    currentportset = set(module.custom_currentportlist)
    allowedportset = set(module.custom_allowedportlist)
    return not currentportset.issubset(allowedportset)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            allowed=dict(type='list', required=True),
            location=dict(type='str', default='/etc/network/interfaces.d/')
        ),
    )
    module.custom_currentportlist = []
    module.custom_allowedportlist = []
    module.changed = False
    module.msg = 'configured port list is part of allowed port list'
    read_current_int_dir(module)
    convert_allowed_list_to_port_range(module)
    if int_policy_enforce(module):
        module.changed = True
        unconfigure_interfaces(module)
    module.exit_json(changed=module.changed, msg=module.msg)


if __name__ == '__main__':
    main()
