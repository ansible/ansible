#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: acme_account_info
author: "Felix Fontein (@felixfontein)"
version_added: "2.7"
short_description: Retrieves information on ACME accounts
description:
   - "Allows to retrieve information on accounts a CA supporting the
      L(ACME protocol,https://tools.ietf.org/html/rfc8555),
      such as L(Let's Encrypt,https://letsencrypt.org/)."
   - "This module only works with the ACME v2 protocol."
notes:
   - "The M(acme_account) module allows to modify, create and delete ACME accounts."
   - "This module was called C(acme_account_facts) before Ansible 2.8. The usage
      did not change."
seealso:
  - module: acme_account
    description: Allows to create, modify or delete an ACME account.
extends_documentation_fragment:
  - acme
'''

EXAMPLES = '''
- name: Check whether an account with the given account key exists
  acme_account_info:
    account_key_src: /etc/pki/cert/private/account.key
    register: account_data
- name: Verify that account exists
  assert:
    that:
      - account_data.exists
- name: Print account URI
  debug: var=account_data.account_uri
- name: Print account contacts
  debug: var=account_data.account.contact

- name: Check whether the account exists and is accessible with the given account key
  acme_account_info:
    account_key_content: "{{ acme_account_key }}"
    account_uri: "{{ acme_account_uri }}"
    register: account_data
- name: Verify that account exists
  assert:
    that:
      - account_data.exists
- name: Print account contacts
  debug: var=account_data.account.contact
'''

RETURN = '''
exists:
  description: Whether the account exists.
  returned: always
  type: bool

account_uri:
  description: ACME account URI, or None if account does not exist.
  returned: always
  type: str

account:
  description: The account information, as retrieved from the ACME server.
  returned: if account exists
  type: complex
  contains:
    contact:
      description: the challenge resource that must be created for validation
      returned: always
      type: list
      sample: "['mailto:me@example.com', 'tel:00123456789']"
    status:
      description: the account's status
      returned: always
      type: str
      choices: ['valid', 'deactivated', 'revoked']
      sample: valid
    orders:
      description: a URL where a list of orders can be retrieved for this account
      returned: always
      type: str
      sample: https://example.ca/account/1/orders
    public_account_key:
      description: the public account key as a L(JSON Web Key,https://tools.ietf.org/html/rfc7517).
      returned: always
      type: str
      sample: https://example.ca/account/1/orders
'''

from ansible.module_utils.acme import (
    ModuleFailException, ACMEAccount, set_crypto_backend,
)

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            account_key_src=dict(type='path', aliases=['account_key']),
            account_key_content=dict(type='str', no_log=True),
            account_uri=dict(type='str'),
            acme_directory=dict(type='str', default='https://acme-staging.api.letsencrypt.org/directory'),
            acme_version=dict(type='int', default=1, choices=[1, 2]),
            validate_certs=dict(type='bool', default=True),
            select_crypto_backend=dict(type='str', default='auto', choices=['auto', 'openssl', 'cryptography']),
        ),
        required_one_of=(
            ['account_key_src', 'account_key_content'],
        ),
        mutually_exclusive=(
            ['account_key_src', 'account_key_content'],
        ),
        supports_check_mode=True,
    )
    if module._name == 'acme_account_facts':
        module.deprecate("The 'acme_account_facts' module has been renamed to 'acme_account_info'", version='2.12')
    set_crypto_backend(module)

    if not module.params.get('validate_certs'):
        module.warn(warning='Disabling certificate validation for communications with ACME endpoint. ' +
                            'This should only be done for testing against a local ACME server for ' +
                            'development purposes, but *never* for production purposes.')
    if module.params.get('acme_version') < 2:
        module.fail_json(msg='The acme_account module requires the ACME v2 protocol!')

    try:
        account = ACMEAccount(module)
        # Check whether account exists
        created, account_data = account.setup_account(
            [],
            allow_creation=False,
            remove_account_uri_if_not_exists=True,
        )
        if created:
            raise AssertionError('Unwanted account creation')
        result = {
            'changed': False,
            'exists': account.uri is not None,
            'account_uri': account.uri,
        }
        if account.uri is not None:
            # Make sure promised data is there
            if 'contact' not in account_data:
                account_data['contact'] = []
            account_data['public_account_key'] = account.key_data['jwk']
            result['account'] = account_data
        module.exit_json(**result)
    except ModuleFailException as e:
        e.do_fail(module)


if __name__ == '__main__':
    main()
