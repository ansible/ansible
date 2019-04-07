#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: ucs_mac_pool
short_description: Configures MAC address pools on Cisco UCS Manager
description:
- Configures MAC address pools and MAC address blocks on Cisco UCS Manager.
- Examples can be used with the UCS Platform Emulator U(https://communities.cisco.com/ucspe).
extends_documentation_fragment: ucs
options:
  state:
    description:
    - If C(present), will verify MAC pool is present and will create if needed.
    - If C(absent), will verify MAC pool is absent and will delete if needed.
    choices: [present, absent]
    default: present
  name:
    description:
    - The name of the MAC pool.
    - This name can be between 1 and 32 alphanumeric characters.
    - "You cannot use spaces or any special characters other than - (hyphen), \"_\" (underscore), : (colon), and . (period)."
    - You cannot change this name after the MAC pool is created.
    required: yes
  descrption:
    description:
    - A description of the MAC pool.
    - Enter up to 256 characters.
    - "You can use any characters or spaces except the following:"
    - "` (accent mark), \ (backslash), ^ (carat), \" (double quote), = (equal sign), > (greater than), < (less than), or ' (single quote)."
    aliases: [ descr ]
  order:
    description:
    - The Assignment Order field.
    - "This can be one of the following:"
    - "default - Cisco UCS Manager selects a random identity from the pool."
    - "sequential - Cisco UCS Manager selects the lowest available identity from the pool."
    choices: [default, sequential]
    default: default
  first_addr:
    description:
    - The first MAC address in the block of addresses.
    - This is the From field in the UCS Manager MAC Blocks menu.
  last_addr:
    description:
    - The last MAC address in the block of addresses.
    - This is the To field in the UCS Manager Add MAC Blocks menu.
  org_dn:
    description:
    - The distinguished name (dn) of the organization where the resource is assigned.
    default: org-root
requirements:
- ucsmsdk
author:
- David Soper (@dsoper2)
- CiscoUcs (@CiscoUcs)
version_added: '2.5'
'''

EXAMPLES = r'''
- name: Configure MAC address pool
  ucs_mac_pool:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: mac-A
    first_addr: 00:25:B5:00:66:00
    last_addr: 00:25:B5:00:67:F3
    order: sequential

- name: Remove MAC address pool
  ucs_mac_pool:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: mac-A
    state: absent
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def main():
    argument_spec = ucs_argument_spec
    argument_spec.update(
        org_dn=dict(type='str', default='org-root'),
        name=dict(type='str', required=True),
        descr=dict(type='str', default=''),
        order=dict(type='str', default='default', choices=['default', 'sequential']),
        first_addr=dict(type='str'),
        last_addr=dict(type='str'),
        state=dict(default='present', choices=['present', 'absent'], type='str'),
    )
    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
    )
    # UCSModule verifies ucsmsdk is present and exits on failure.  Imports are below ucs object creation.
    ucs = UCSModule(module)

    err = False

    from ucsmsdk.mometa.macpool.MacpoolPool import MacpoolPool
    from ucsmsdk.mometa.macpool.MacpoolBlock import MacpoolBlock

    changed = False
    try:
        mo_exists = False
        props_match = False
        # dn is <org_dn>/mac-pool-<name>
        dn = module.params['org_dn'] + '/mac-pool-' + module.params['name']
        mo = ucs.login_handle.query_dn(dn)
        if mo:
            mo_exists = True

        if module.params['state'] == 'absent':
            if mo_exists:
                if not module.check_mode:
                    ucs.login_handle.remove_mo(mo)
                    ucs.login_handle.commit()
                changed = True
        else:
            if mo_exists:
                # check top-level mo props
                kwargs = dict(assignment_order=module.params['order'])
                kwargs['descr'] = module.params['descr']
                if (mo.check_prop_match(**kwargs)):
                    # top-level props match, check next level mo/props
                    if module.params['last_addr'] and module.params['first_addr']:
                        # mac address block specified, check properties
                        block_dn = dn + '/block-' + module.params['first_addr'].upper() + '-' + module.params['last_addr'].upper()
                        mo_1 = ucs.login_handle.query_dn(block_dn)
                        if mo_1:
                            props_match = True
                    else:
                        # no MAC address block specified, but top-level props matched
                        props_match = True

            if not props_match:
                if not module.check_mode:
                    # create if mo does not already exist
                    mo = MacpoolPool(
                        parent_mo_or_dn=module.params['org_dn'],
                        name=module.params['name'],
                        descr=module.params['descr'],
                        assignment_order=module.params['order'],
                    )

                    if module.params['last_addr'] and module.params['first_addr']:
                        mo_1 = MacpoolBlock(
                            parent_mo_or_dn=mo,
                            to=module.params['last_addr'],
                            r_from=module.params['first_addr'],
                        )

                    ucs.login_handle.add_mo(mo, True)
                    ucs.login_handle.commit()
                changed = True

    except Exception as e:
        err = True
        ucs.result['msg'] = "setup error: %s " % str(e)

    ucs.result['changed'] = changed
    if err:
        module.fail_json(**ucs.result)
    module.exit_json(**ucs.result)


if __name__ == '__main__':
    main()
