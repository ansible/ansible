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

version_added: "2.6"

description:
    - Configures time zone on Cisco UCS Manager.
    - Examples can be used with the UCS Platform Emulator U(https://communities.cisco.com/ucspe).

options:
    state:
        description:
            - If C(present), will verify timezone is set (persent) and will set (create) if needed.
            - If C(absent), will verify timezone is unset (absent) and will unset (delete) if needed.
        choices: [present, absent]
        default: absent
        aliases: [admin_state]

    timezone:
        description:
            - The timezone name. Time zone names are from the tz database U(https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
            - The timezone name is case sensitive.
            - This name can be between 0 and 510 alphanumeric characters.
            - You cannot use spaces or any special characters other than
            - "\"-\" (hyphen), \"_\" (underscore), \"/\" (backslash)."
        default: unset
        required: no

    description:
        description:
            - A user-defined description of the timezone object.
            - Enter up to 256 characters.
            - "You can use any characters or spaces except the following:"
            - "` (accent mark), \ (backslash), ^ (carat), \" (double quote), = (equal sign), > (greater than), < (less than), or ' (single quote)."
        required: no
        aliases: [ descr ]

extends_documentation_fragment:
    - ucs

requirements:

    - ucsmsdk
    - pytz

author:

    - John McDonough (@movinalot)
    - CiscoUcs (@CiscoUcs)
'''

EXAMPLES = r'''
- name: Configure Time Zone
  ucs_timezone:
    hostname: 172.16.143.150
    username: admin
    password: password
    state: present
    timezone: America/Los_Angeles
    descr: 'Time Zone for Los Angeles'

- name: Unconfigure Time Zone
  ucs_timezone:
    hostname: 172.16.143.150
    username: admin
    password: password
    state: absent
'''

RETURN = r'''
#
'''

import pytz
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.ucs import UCSModule, ucs_argument_spec


def main():
    argument_spec = ucs_argument_spec
    argument_spec.update(
        timezone=dict(type='str', default=''),
        descr=dict(type='str'),
        state=dict(type='str', default='absent', choices=['present', 'absent']),
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

    # UCSModule creation above verifies ucsmsdk is present and exits on failure, so additional imports are done below.

    changed = False
    try:
        mo_exists = False
        props_match = False

        if (module.params['timezone'] in pytz.all_timezones or
                len(module.params['timezone']) <= 0):

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
                    kwargs = dict(timezone=module.params['timezone'])
                    kwargs['descr'] = module.params['descr']
                    if mo.check_prop_match(**kwargs):
                        props_match = True

                if not props_match:
                    if not module.check_mode:
                        # update mo timezone mo always exists
                        mo.timezone = module.params['timezone']
                        mo.descr = module.params['descr']
                        ucs.login_handle.add_mo(mo, modify_present=True)
                        ucs.login_handle.commit()
                    changed = True
        else:
            err = True
            module.fail_json(msg='time zone: ' + module.params['timezone'] + ' is not a valid time zone string')

    except Exception as e:
        err = True
        ucs.result['msg'] = "setup error: %s " % str(e)

    ucs.result['changed'] = changed
    if err:
        module.fail_json(**ucs.result)
    module.exit_json(**ucs.result)


if __name__ == '__main__':
    main()
