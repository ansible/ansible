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
module: ucs_timezone
short_description: Configures timezone on Cisco UCS Manager
description:
- Configures timezone on Cisco UCS Manager.
- Examples can be used with the L(UCS Platform Emulator,https://communities.cisco.com/ucspe).
extends_documentation_fragment: ucs
options:
  state:
    description:
    - If C(absent), will unset timezone.
    - If C(present), will set or update timezone.
    choices: [absent, present]
    default: present

  admin_state:
    description:
    - The admin_state setting
    - The enabled admin_state indicates the timezone confguration is utilized by UCS Manager.
    - The disabled admin_state indicates the timezone confguration is ignored by UCS Manager.
    choices: [disabled, enabled]
    default: enabled

  description:
    description:
    - A user-defined description of the timezone.
    - Enter up to 256 characters.
    - "You can use any characters or spaces except the following:"
    - "` (accent mark), \ (backslash), ^ (carat), \" (double quote), = (equal sign), > (greater than), < (less than), or ' (single quote)."
    aliases: [ descr ]
    default: ""

  timezone:
    description:
    - The timezone name.
    - Time zone names are from the L(tz database,https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
    - The timezone name is case sensitive.
    - The timezone name can be between 0 and 510 alphanumeric characters.
    - You cannot use spaces or any special characters other than
    - "\"-\" (hyphen), \"_\" (underscore), \"/\" (backslash)."

requirements:
- ucsmsdk
author:
- John McDonough (@movinalot)
- CiscoUcs (@CiscoUcs)
version_added: '2.7'
'''

EXAMPLES = r'''
- name: Configure Time Zone
  ucs_timezone:
    hostname: 172.16.143.150
    username: admin
    password: password
    state: present
    admin_state: enabled
    timezone: America/Los_Angeles
    description: 'Time Zone for Los Angeles'

- name: Unconfigure Time Zone
  ucs_timezone:
    hostname: 172.16.143.150
    username: admin
    password: password
    state: absent
    admin_state: disabled
'''

RETURN = r'''
#
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def run_module():
    argument_spec = ucs_argument_spec
    argument_spec.update(
        timezone=dict(type='str'),
        description=dict(type='str', aliases=['descr'], default=''),
        admin_state=dict(type='str', default='enabled', choices=['disabled', 'enabled']),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['timezone']],
        ],
    )
    ucs = UCSModule(module)

    err = False

    changed = False
    try:
        mo_exists = False
        props_match = False

        dn = 'sys/svc-ext/datetime-svc'

        mo = ucs.login_handle.query_dn(dn)
        if mo:
            mo_exists = True

        if module.params['state'] == 'absent':
            # mo must exist but all properties do not have to match
            if mo_exists:
                if not module.check_mode:
                    mo.timezone = ""
                    mo.descr = ""
                    ucs.login_handle.add_mo(mo, modify_present=True)
                    ucs.login_handle.commit()
                changed = True
        else:
            if mo_exists:
                # check top-level mo props
                kwargs = dict(descr=module.params['description'])
                kwargs['timezone'] = module.params['timezone']
                kwargs['admin_state'] = module.params['admin_state']
                if mo.check_prop_match(**kwargs):
                    props_match = True

            if not props_match:
                if not module.check_mode:
                    # update mo, timezone mo always exists
                    mo.timezone = module.params['timezone']
                    mo.descr = module.params['description']
                    mo.admin_state = module.params['admin_state']
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
