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
module: purefb_smtp
version_added: '2.9'
short_description: Configure SMTP for Pure Storage FlashBlade
description:
- Configure SMTP for a Pure Storage FlashBlade.
- Whilst there can be no relay host, a sender domain must be configured.
author:
- Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  host:
    description: Relay server name
    type: str
  domain:
    description: Domain name for alert messages
    required: true
    type: str
extends_documentation_fragment:
- purestorage.fb
'''

EXAMPLES = r'''
- name: Configure SMTP settings
  purefb_smtp:
    host: hostname
    domain: xyz.com
    fb_url: 10.10.10.2
    api_token: T-9f276a18-50ab-446e-8a0c-666a3529a1b6
'''

RETURN = r'''
'''

HAS_PURITY_FB = True
try:
    from purity_fb import Smtp
except ImportError:
    HAS_PURITY_FB = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pure import get_blade, purefb_argument_spec


MIN_REQUIRED_API_VERSION = "1.6"


def set_smtp(module, blade):
    """Configure SMTP settings"""
    changed = True
    if not module.check_mode:
        current_smtp = blade.smtp.list_smtp().items[0]
        if module.params['host'] and module.params['host'] != current_smtp.relay_host:
            smtp_settings = Smtp(relay_host=module.params['host'])
            try:
                blade.smtp.update_smtp(smtp_settings=smtp_settings)
            except Exception:
                module.fail_json(msg='Configuring SMTP relay host failed')
        elif current_smtp.relay_host and not module.params['host']:
            smtp_settings = Smtp(relay_host='')
            try:
                blade.smtp.update_smtp(smtp_settings=smtp_settings)
            except Exception:
                module.fail_json(msg='Configuring SMTP relay host failed')
        if module.params['domain'] != current_smtp.sender_domain:
            smtp_settings = Smtp(sender_domain=module.params['domain'])
            try:
                blade.smtp.update_smtp(smtp_settings=smtp_settings)
            except Exception:
                module.fail_json(msg='Configuring SMTP sender domain failed')
        else:
            changed = False
    module.exit_json(changed=changed)


def main():
    argument_spec = purefb_argument_spec()
    argument_spec.update(dict(
        host=dict(type='str'),
        domain=dict(type='str', required=True),
    ))

    module = AnsibleModule(argument_spec,
                           supports_check_mode=True)

    blade = get_blade(module)
    api_version = blade.api_version.list_versions().versions
    if MIN_REQUIRED_API_VERSION not in api_version:
        module.fail_json(msg="Purity//FB must be upgraded to support this module.")

    if not HAS_PURITY_FB:
        module.fail_json(msg='purity_fb SDK is required for this module')

    set_smtp(module, blade)
    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
