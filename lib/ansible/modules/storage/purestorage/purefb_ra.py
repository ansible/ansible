#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: purefb_ra
version_added: '2.9'
short_description: Enable or Disable Pure Storage FlashBlade Remote Assist
description:
- Enable or Disable Remote Assist for a Pure Storage FlashBlade.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  state:
    description:
    - Define state of remote assist
    - When set to I(enable) the RA port can be exposed using the
      I(debug) module.
    type: str
    default: present
    choices: [ present, absent ]
extends_documentation_fragment:
- purestorage.fb
'''

EXAMPLES = r'''
- name: Enable Remote Assist port
  purefb_ra:
    fb_url: 10.10.10.2
    api_token: T-9f276a18-50ab-446e-8a0c-666a3529a1b6

- name: Disable Remote Assist port
  purefb_ra:
    state: absent
    fb_url: 10.10.10.2
    api_token: T-9f276a18-50ab-446e-8a0c-666a3529a1b6
'''

RETURN = r'''
'''

HAS_PURITY_FB = True
try:
    from purity_fb import Support
except ImportError:
    HAS_PURITY_FB = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_blade, purefb_argument_spec


MIN_REQUIRED_API_VERSION = "1.6"


def enable_ra(module, blade):
    """Enable Remote Assist"""
    changed = True
    if not module.check_mode:
        ra_settings = Support(remote_assist_active=True)
        try:
            blade.support.update_support(support=ra_settings)
        except Exception:
            module.fail_json(msg='Enabling Remote Assist failed')
    module.exit_json(changed=changed)


def disable_ra(module, blade):
    """Disable Remote Assist"""
    changed = True
    if not module.check_mode:
        ra_settings = Support(remote_assist_active=False)
        try:
            blade.support.update_support(support=ra_settings)
        except Exception:
            module.fail_json(msg='Disabling Remote Assist failed')
    module.exit_json(changed=changed)


def main():
    argument_spec = purefb_argument_spec()
    argument_spec.update(dict(
        state=dict(type='str', default='present', choices=['present', 'absent']),
    ))

    module = AnsibleModule(argument_spec,
                           supports_check_mode=True)

    blade = get_blade(module)
    api_version = blade.api_version.list_versions().versions
    if MIN_REQUIRED_API_VERSION not in api_version:
        module.fail_json(msg="Purity//FB must be upgraded to support this module.")

    if not HAS_PURITY_FB:
        module.fail_json(msg='purity_fb SDK is required for this module')

    if module.params['state'] == 'present' and not blade.support.list_support().items[0].remote_assist_active:
        enable_ra(module, blade)
    elif module.params['state'] == 'absent' and blade.support.list_support().items[0].remote_assist_active:
        disable_ra(module, blade)
    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
