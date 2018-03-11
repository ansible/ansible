#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016 Michael Gruener <michael.gruener@chaosmoon.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: letsencrypt_account
author: "Felix Fontein (@felixfontein)"
version_added: "2.6"
short_description: Create, modify or delete accounts with Let's Encrypt
description:
   - "Allows to create, modify or delete accounts with Let's Encrypt.
      Let's Encrypt is a free, automated, and open certificate authority
      (CA), run for the public's benefit. For details see U(https://letsencrypt.org)."
   - "This module only works with the ACME v2 protocol."
extends_documentation_fragment:
  - letsencrypt
options:
  state:
    description:
      - "The state of the account, to be identified by its account key."
      - "If the state is C(absent), the account will either not exist or be
         deactivated."
    required: true
    choices:
    - present
    - absent
    version_added: "2.5"
  allow_creation:
    description:
      - "Whether account creation is allowed (when state is C(present))."
    default: yes
    type: bool
  contact:
    description:
      - "A list of contact URLs."
      - "Email addresses must be prefixed with C(mailto:)."
      - "See https://tools.ietf.org/html/draft-ietf-acme-acme-10#section-7.1.2 for what is allowed."
      - "Must be specified when state is C(present)"
    default: []
  terms_agreed:
    description:
      - "Boolean indicating whether you agree to the terms of service document."
      - "ACME servers can require this to be true."
    default: no
    type: bool
'''

EXAMPLES = '''
- name: Make sure account exists and has given contacts. We agree to TOS.
  letsencrypt:
    account_key_src: /etc/pki/cert/private/account.key
    state: present
    terms_agreed: yes
    contact:
    - mailto:me@example.com
    - mailto:myself@example.org

- name: Make sure account has given email address. Don't create account if it doesn't exist
  letsencrypt:
    account_key_src: /etc/pki/cert/private/account.key
    state: present
    allow_creation: no
    contact:
    - mailto:me@example.com

- name: Delete account
  letsencrypt:
    account_key_src: /etc/pki/cert/private/account.key
    state: absent
'''

RETURN = '''
account_uri:
  description: ACME account URI, or None if account does not exist.
  returned: always
  type: string
'''

from ansible.module_utils.letsencrypt import (
    ModuleFailException, ACMEAccount
)

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            account_key_src=dict(type='path', aliases=['account_key']),
            account_key_content=dict(type='str', no_log=True),
            acme_directory=dict(required=False, default='https://acme-staging.api.letsencrypt.org/directory', type='str'),
            acme_version=dict(required=False, default=1, choices=[1, 2], type='int'),
            terms_agreed=dict(required=False, default=False, type='bool'),
            state=dict(required=True, choices=['absent', 'present'], type='str'),
            allow_creation=dict(required=False, default=True, type='bool'),
            contact=dict(required=False, type='list', default=[]),
            validate_certs=dict(required=False, default=True, type='bool'),
        ),
        required_one_of=(
            ['account_key_src', 'account_key_content'],
        ),
        mutually_exclusive=(
            ['account_key_src', 'account_key_content'],
        ),
        supports_check_mode=True,
    )

    if not module.params.get('validate_certs'):
        module.warn(warning='Disabling certificate validation for communications with ACME endpoint. ' +
                            'This should only be done for testing against a local ACME server for ' +
                            'development purposes, but *never* for production purposes.')
    if module.params.get('acme_version') < 2:
        module.fail_json(msg='The letsencrypt_account module requires the ACME v2 protocol!')

    state = module.params.get('state')
    try:
        account = ACMEAccount(module)
        if state == 'absent':
            changed = account.init_account(
                [],
                allow_creation=False,
                update_contact=False,
            )
            if changed:
                raise AssertionError('Unwanted account change')
            if account.uri is not None:
                # Account does exist
                account_data = account.get_account_data()
                if account_data is not None:
                    # Account is not yet deactivated
                    if not module.check_mode:
                        # Deactivate it
                        payload = {
                            'status': 'deactivated'
                        }
                        result, info = account.send_signed_request(account.uri, payload)
                        if info['status'] != 200:
                            raise ModuleFailException('Error deactivating account: {0} {1}'.format(info['status'], result))
                    module.exit_json(changed=True, account_uri=account.uri)
            module.exit_json(changed=False, account_uri=account.uri)
        else:
            allow_creation = module.params.get('allow_creation')
            contact = module.params.get('contact')
            terms_agreed = module.params.get('terms_agreed')
            changed = account.init_account(
                contact,
                terms_agreed=terms_agreed,
                allow_creation=allow_creation,
            )
            if account.uri is None:
                raise ModuleFailException(msg='Account does not exist or is deactivated.')
            module.exit_json(changed=changed, account_uri=account.uri)
    except ModuleFailException as e:
        e.do_fail(module)


if __name__ == '__main__':
    main()
