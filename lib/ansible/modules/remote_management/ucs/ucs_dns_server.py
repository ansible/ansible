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
module: ucs_dns_server

short_description: Configure DNS servers on Cisco UCS Manager

extends_documentation_fragment:
- ucs

description:
- Configure DNS servers on Cisco UCS Manager.
- Examples can be used with the L(UCS Platform Emulator,https://communities.cisco.com/ucspe).

options:
  state:
    description:
    - If C(absent), will remove a DNS server.
    - If C(present), will add or update a DNS server.
    choices: [absent, present]
    default: present
    type: str

  dns_server:
    description:
    - DNS server IP address.
    - Enter a valid IPV4 Address.
    - UCS Manager supports up to 4 DNS Servers
    aliases: [ name ]
    type: str

  description:
    description:
    - A user-defined description of the DNS server.
    - Enter up to 256 characters.
    - "You can use any characters or spaces except the following:"
    - "` (accent mark), \ (backslash), ^ (carat), \" (double quote), = (equal sign), > (greater than), < (less than), or ' (single quote)."
    aliases: [ descr ]
    type: str

  delegate_to:
    description:
    - Where the module will be run
    default: localhost
    type: str

requirements:
- ucsmsdk

author:
- John McDonough (@movinalot)
- CiscoUcs (@CiscoUcs)

version_added: "2.8"
'''

EXAMPLES = r'''
- name: Configure DNS server
  ucs_dns_server:
    hostname: 172.16.143.150
    username: admin
    password: password
    dns_server: 10.10.10.10
    description: DNS Server IP address
    state: present
    delegate_to: localhost

- name: Remove DNS server
  ucs_dns_server:
    hostname: 172.16.143.150
    username: admin
    password: password
    dns_server: 10.10.10.10
    state: absent
    delegate_to: localhost
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def run_module():
    argument_spec = ucs_argument_spec
    argument_spec.update(
        dns_server=dict(type='str', aliases=['name']),
        description=dict(type='str', aliases=['descr'], default=''),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        delegate_to=dict(type='str', default='localhost'),
    )

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['dns_server']],
        ],
    )
    # UCSModule verifies ucsmsdk is present and exits on failure.
    # Imports are below for UCS object creation.
    ucs = UCSModule(module)
    from ucsmsdk.mometa.comm.CommDnsProvider import CommDnsProvider

    err = False
    changed = False

    try:
        mo_exists = False
        props_match = False

        dn = 'sys/svc-ext/dns-svc/dns-' + module.params['dns_server']

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
                kwargs = dict(descr=module.params['description'])
                if mo.check_prop_match(**kwargs):
                    props_match = True

            if not props_match:
                if not module.check_mode:
                    # update/add mo
                    mo = CommDnsProvider(parent_mo_or_dn='sys/svc-ext/dns-svc',
                                         name=module.params['dns_server'],
                                         descr=module.params['description'])
                    ucs.login_handle.add_mo(mo, modify_present=True)
                    ucs.login_handle.commit()
                changed = True

    except Exception as e:
        err = True
        ucs.result['msg'] = "setup error: %s " % str(e)

    ucs.result['changed'] = changed
    if err:
        module.fail_json(**ucs.result)
    module.exit_json(**ucs.result)


def main():
    run_module()


if __name__ == '__main__':
    main()
