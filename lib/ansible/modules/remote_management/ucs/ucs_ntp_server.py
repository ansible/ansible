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
module: ucs_ntp_server
short_description: Configures NTP server on Cisco UCS Manager
extends_documentation_fragment:
- ucs
description:
- Configures NTP server on Cisco UCS Manager.
- Examples can be used with the L(UCS Platform Emulator,https://communities.cisco.com/ucspe).
options:
  state:
    description:
    - If C(absent), will remove an NTP server.
    - If C(present), will add or update an NTP server.
    choices: [absent, present]
    default: present

  ntp_server:
    description:
    - NTP server IP address or hostname.
    - Enter up to 63 characters that form a valid hostname.
    - Enter a valid IPV4 Address.
    aliases: [ name ]
    default: ""

  description:
    description:
    - A user-defined description of the NTP server.
    - Enter up to 256 characters.
    - "You can use any characters or spaces except the following:"
    - "` (accent mark), \ (backslash), ^ (carat), \" (double quote), = (equal sign), > (greater than), < (less than), or ' (single quote)."
    aliases: [ descr ]
    default: ""

requirements:
- ucsmsdk
author:
- John McDonough (@movinalot)
- CiscoUcs (@CiscoUcs)
version_added: "2.7"
'''

EXAMPLES = r'''
- name: Configure NTP server
  ucs_ntp_server:
    hostname: 172.16.143.150
    username: admin
    password: password
    ntp_server: 10.10.10.10
    description: Internal NTP Server by IP address
    state: present

- name: Configure NTP server
  ucs_ntp_server:
    hostname: 172.16.143.150
    username: admin
    password: password
    ntp_server: pool.ntp.org
    description: External NTP Server by hostname
    state: present

- name: Remove NTP server
  ucs_ntp_server:
    hostname: 172.16.143.150
    username: admin
    password: password
    ntp_server: 10.10.10.10
    state: absent

- name: Remove NTP server
  ucs_ntp_server:
    hostname: 172.16.143.150
    username: admin
    password: password
    ntp_server: pool.ntp.org
    state: absent
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def run_module():
    argument_spec = ucs_argument_spec
    argument_spec.update(
        ntp_server=dict(type='str', aliases=['name']),
        description=dict(type='str', aliases=['descr'], default=''),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['ntp_server']],
        ],
    )
    # UCSModule verifies ucsmsdk is present and exits on failure.  Imports are below ucs object creation.
    ucs = UCSModule(module)

    err = False

    from ucsmsdk.mometa.comm.CommNtpProvider import CommNtpProvider

    changed = False
    try:
        mo_exists = False
        props_match = False

        dn = 'sys/svc-ext/datetime-svc/ntp-' + module.params['ntp_server']

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
                    mo = CommNtpProvider(parent_mo_or_dn='sys/svc-ext/datetime-svc',
                                         name=module.params['ntp_server'],
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
