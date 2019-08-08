#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Advania Ísland ehf. <gabriel.arthur.petursson@advania.is>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: system_crypto_policy
short_description: Manage system-wide crypto policies
version_added: "2.9"
description:
    - Manage system-wide crypto policies on Fedora systems and derivatives.
    - https://www.redhat.com/en/blog/consistent-security-crypto-policies-red-hat-enterprise-linux-8

options:
    policy:
        description:
            - Name of a crypto policy to set
        type: str
        required: false

author:
    - Gabríel Arthúr Pétursson (@polarina)
'''

EXAMPLES = '''
- name: Query current crypto policy
  system_crypto_policy: {}
  register: result

- name: Print current policy
  debug:
    msg: "{{result.policy}}"

- name: Harden system's security
  system_crypto_policy:
    policy: FUTURE
'''

RETURN = '''
policy:
    description: Current system's crypto policy
    type: str
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule


def get_current_policy(module):
    args = ['/usr/bin/update-crypto-policies', '--show']
    rc, stdout, stderr = module.run_command(args, check_rc=True)
    return stdout.strip()


def set_current_policy(module, new_policy):
    args = ['/usr/bin/update-crypto-policies', '--set', new_policy]
    module.run_command(args, check_rc=True)


def main():
    module_args = dict(
        policy=dict(type='str', required=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    changed = False
    current_policy = get_current_policy(module)
    want_policy = module.params['policy']

    if want_policy is None:
        module.exit_json(policy=current_policy)

    if current_policy != want_policy:
        if not module.check_mode:
            set_current_policy(module, want_policy)
            current_policy = want_policy

        changed = True

    module.exit_json(changed=changed, policy=current_policy)


if __name__ == '__main__':
    main()
