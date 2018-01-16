#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: ucs_ip_pool
short_description: Configures IP address pools on Cisco UCS Manager
description:
- Configures IP address pools and blocks of IP addresses on Cisco UCS Manager.
- Examples can be used with the UCS Platform Emulator U(https://communities.cisco.com/ucspe).
extends_documentation_fragment: ucs
options:
  state:
    description:
    - If C(present), will verify IP pool is present and will create if needed.
    - If C(absent), will verify IP pool is absent and will delete if needed.
    choices: [present, absent]
    default: present
  name:
    description:
    - The name of the IP address pool.
    - This name can be between 1 and 32 alphanumeric characters.
    - "You cannot use spaces or any special characters other than - (hyphen), \"_\" (underscore), : (colon), and . (period)."
    - You cannot change this name after the IP address pool is created.
    required: yes
  descrption:
    description:
    - The user-defined description of the IP address pool.
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
    - The first IPv4 address in the IPv4 addresses block.
    - This is the From field in the UCS Manager Add IPv4 Blocks menu.
  last_addr:
    description:
    - The last IPv4 address in the IPv4 addresses block.
    - This is the To field in the UCS Manager Add IPv4 Blocks menu.
  subnet_mask:
    description:
    - The subnet mask associated with the IPv4 addresses in the block.
    default: 255.255.255.0
  default_gw:
    description:
    - The default gateway associated with the IPv4 addresses in the block.
    default: 0.0.0.0
  primary_dns:
    description:
    - The primary DNS server that this block of IPv4 addresses should access.
    default: 0.0.0.0
  secondary_dns:
    description:
    - The secondary DNS server that this block of IPv4 addresses should access.
    default: 0.0.0.0
  ipv6_first_addr:
    description:
    - The first IPv6 address in the IPv6 addresses block.
    - This is the From field in the UCS Manager Add IPv6 Blocks menu.
  ipv6_last_addr:
    description:
    - The last IPv6 address in the IPv6 addresses block.
    - This is the To field in the UCS Manager Add IPv6 Blocks menu.
  ipv6_prefix:
    description:
    - The network address prefix associated with the IPv6 addresses in the block.
    default: '64'
  ipv6_default_gw:
    description:
    - The default gateway associated with the IPv6 addresses in the block.
    default: '::'
  ipv6_primary_dns:
    description:
    - The primary DNS server that this block of IPv6 addresses should access.
    default: '::'
  ipv6_secondary_dns:
    description:
    - The secondary DNS server that this block of IPv6 addresses should access.
    default: '::'
  org_dn:
    description:
    - Org dn (distinguished name)
    default: org-root
requirements:
- ucsmsdk
author:
- David Soper (@dsoper2)
- CiscoUcs (@CiscoUcs)
version_added: '2.5'
'''

EXAMPLES = r'''
- name: Configure IPv4 address pools
  ucs_ip_pool:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: ip-A
    order: sequential
    first_addr: 192.168.0.10
    last_addr: 192.168.0.19
    subnet_mask: 255.255.255.0
    default_gw: 192.168.0.1
    primary_dns: 172.16.143.136
- name: Configure IPv6 address pools
  ucs_ip_pool:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: ipv6-B
    ipv6_first_addr: fe80::1cae:7992:d7a1:ed07
    ipv6_last_addr: fe80::1cae:7992:d7a1:edfe
    ipv6_default_gw: fe80::1cae:7992:d7a1:ecff

- name: Remove IPv4 address pools
  ucs_ip_pool:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: ip-A
    state: absent
- name: Remove IPv6 address pools
  ucs_ip_pool:
    hostname: 172.16.143.150
    username: admin
    password: password
    name: ipv6-B
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
        subnet_mask=dict(type='str', default='255.255.255.0'),
        default_gw=dict(type='str', default='0.0.0.0'),
        primary_dns=dict(type='str', default='0.0.0.0'),
        secondary_dns=dict(type='str', default='0.0.0.0'),
        ipv6_first_addr=dict(type='str'),
        ipv6_last_addr=dict(type='str'),
        ipv6_prefix=dict(type='str', default='64'),
        ipv6_default_gw=dict(type='str', default='::'),
        ipv6_primary_dns=dict(type='str', default='::'),
        ipv6_secondary_dns=dict(type='str', default='::'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
    )
    # UCSModule verifies ucsmsdk is present and exits on failure.  Imports are below ucs object creation.
    ucs = UCSModule(module)

    err = False

    from ucsmsdk.mometa.ippool.IppoolPool import IppoolPool
    from ucsmsdk.mometa.ippool.IppoolBlock import IppoolBlock
    from ucsmsdk.mometa.ippool.IppoolIpV6Block import IppoolIpV6Block

    changed = False
    try:
        mo_exists = False
        props_match = False
        # dn is <org_dn>/ip-pool-<name>
        dn = module.params['org_dn'] + '/ip-pool-' + module.params['name']

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
                        # ipv4 block specified, check properties
                        block_dn = dn + '/block-' + module.params['first_addr'] + '-' + module.params['last_addr']
                        mo_1 = ucs.login_handle.query_dn(block_dn)
                        if mo_1:
                            kwargs = dict(subnet=module.params['subnet_mask'])
                            kwargs['def_gw'] = module.params['default_gw']
                            kwargs['prim_dns'] = module.params['primary_dns']
                            kwargs['sec_dns'] = module.params['secondary_dns']
                            if (mo_1.check_prop_match(**kwargs)):
                                # ipv4 block exists and properties match
                                props_match = True
                    else:
                        # no ipv4 block specified, but top-level props matched
                        props_match = True

                    # only check ipv6 props if the top-level and ipv4 props matched
                    if props_match and module.params['ipv6_last_addr'] and module.params['ipv6_first_addr']:
                        # ipv6 block specified, check properties
                        block_dn = dn + '/v6block-' + module.params['ipv6_first_addr'].lower() + '-' + module.params['ipv6_last_addr'].lower()
                        mo_1 = ucs.login_handle.query_dn(block_dn)
                        if mo_1:
                            kwargs = dict(prefix=module.params['ipv6_prefix'])
                            kwargs['def_gw'] = module.params['ipv6_default_gw']
                            kwargs['prim_dns'] = module.params['ipv6_primary_dns']
                            kwargs['sec_dns'] = module.params['ipv6_secondary_dns']
                            if (mo_1.check_prop_match(**kwargs)):
                                # ipv6 block exists and properties match
                                props_match = True
                        else:
                            # no ipv6 block specified, but previous checks matched
                            props_match = True

            if not props_match:
                if not module.check_mode:
                    # create if mo does not already exist
                    mo = IppoolPool(
                        parent_mo_or_dn=module.params['org_dn'],
                        name=module.params['name'],
                        descr=module.params['descr'],
                        assignment_order=module.params['order'],
                    )

                    if module.params['last_addr'] and module.params['first_addr']:
                        mo_1 = IppoolBlock(
                            parent_mo_or_dn=mo,
                            to=module.params['last_addr'],
                            r_from=module.params['first_addr'],
                            subnet=module.params['subnet_mask'],
                            def_gw=module.params['default_gw'],
                            prim_dns=module.params['primary_dns'],
                            sec_dns=module.params['secondary_dns'],
                        )

                    if module.params['ipv6_last_addr'] and module.params['ipv6_first_addr']:
                        mo_1 = IppoolIpV6Block(
                            parent_mo_or_dn=mo,
                            to=module.params['ipv6_last_addr'],
                            r_from=module.params['ipv6_first_addr'],
                            prefix=module.params['ipv6_prefix'],
                            def_gw=module.params['ipv6_default_gw'],
                            prim_dns=module.params['ipv6_primary_dns'],
                            sec_dns=module.params['ipv6_secondary_dns'],
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
