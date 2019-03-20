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
module: acme_account
author: "Felix Fontein (@felixfontein)"
version_added: "2.6"
short_description: Create, modify or delete ACME accounts
description:
   - "Allows to create, modify or delete accounts with a CA supporting the
      L(ACME protocol,https://tools.ietf.org/html/rfc8555),
      such as L(Let's Encrypt,https://letsencrypt.org/)."
   - "This module only works with the ACME v2 protocol."
notes:
   - "The M(acme_certificate) module also allows to do basic account management.
      When using both modules, it is recommended to disable account management
      for M(acme_certificate). For that, use the C(modify_account) option of
      M(acme_certificate)."
seealso:
  - name: Automatic Certificate Management Environment (ACME)
    description: The specification of the ACME protocol (RFC 8555).
    link: https://tools.ietf.org/html/rfc8555
  - module: acme_account_info
    description: Retrieves facts about an ACME account.
  - module: openssl_privatekey
    description: Can be used to create a private account key.
  - module: acme_inspect
    description: Allows to debug problems.
extends_documentation_fragment:
  - acme
options:
  state:
    description:
      - "The state of the account, to be identified by its account key."
      - "If the state is C(absent), the account will either not exist or be
         deactivated."
      - "If the state is C(changed_key), the account must exist. The account
         key will be changed; no other information will be touched."
    type: str
    required: true
    choices:
    - present
    - absent
    - changed_key
  allow_creation:
    description:
      - "Whether account creation is allowed (when state is C(present))."
    type: bool
    default: yes
  contact:
    description:
      - "A list of contact URLs."
      - "Email addresses must be prefixed with C(mailto:)."
      - "See U(https://tools.ietf.org/html/rfc8555#section-7.3)
         for what is allowed."
      - "Must be specified when state is C(present). Will be ignored
         if state is C(absent) or C(changed_key)."
    type: list
    default: []
  terms_agreed:
    description:
      - "Boolean indicating whether you agree to the terms of service document."
      - "ACME servers can require this to be true."
    type: bool
    default: no
  new_account_key_src:
    description:
      - "Path to a file containing the ACME account RSA or Elliptic Curve key to change to."
      - "Same restrictions apply as to C(account_key_src)."
      - "Mutually exclusive with C(new_account_key_content)."
      - "Required if C(new_account_key_content) is not used and state is C(changed_key)."
    type: path
  new_account_key_content:
    description:
      - "Content of the ACME account RSA or Elliptic Curve key to change to."
      - "Same restrictions apply as to C(account_key_content)."
      - "Mutually exclusive with C(new_account_key_src)."
      - "Required if C(new_account_key_src) is not used and state is C(changed_key)."
    type: str
'''

EXAMPLES = '''
- name: Make sure account exists and has given contacts. We agree to TOS.
  acme_account:
    account_key_src: /etc/pki/cert/private/account.key
    state: present
    terms_agreed: yes
    contact:
    - mailto:me@example.com
    - mailto:myself@example.org

- name: Make sure account has given email address. Don't create account if it doesn't exist
  acme_account:
    account_key_src: /etc/pki/cert/private/account.key
    state: present
    allow_creation: no
    contact:
    - mailto:me@example.com

- name: Change account's key to the one stored in the variable new_account_key
  acme_account:
    account_key_src: /etc/pki/cert/private/account.key
    new_account_key_content: '{{ new_account_key }}'
    state: changed_key

- name: Delete account (we have to use the new key)
  acme_account:
    account_key_content: '{{ new_account_key }}'
    state: absent
'''

RETURN = '''
account_uri:
  description: ACME account URI, or None if account does not exist.
  returned: always
  type: str
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
            terms_agreed=dict(type='bool', default=False),
            state=dict(type='str', required=True, choices=['absent', 'present', 'changed_key']),
            allow_creation=dict(type='bool', default=True),
            contact=dict(type='list', elements='str', default=[]),
            new_account_key_src=dict(type='path'),
            new_account_key_content=dict(type='str', no_log=True),
            select_crypto_backend=dict(type='str', default='auto', choices=['auto', 'openssl', 'cryptography']),
        ),
        required_one_of=(
            ['account_key_src', 'account_key_content'],
        ),
        mutually_exclusive=(
            ['account_key_src', 'account_key_content'],
            ['new_account_key_src', 'new_account_key_content'],
        ),
        required_if=(
            # Make sure that for state == changed_key, one of
            # new_account_key_src and new_account_key_content are specified
            ['state', 'changed_key', ['new_account_key_src', 'new_account_key_content'], True],
        ),
        supports_check_mode=True,
    )
    set_crypto_backend(module)

    if not module.params.get('validate_certs'):
        module.warn(warning='Disabling certificate validation for communications with ACME endpoint. ' +
                            'This should only be done for testing against a local ACME server for ' +
                            'development purposes, but *never* for production purposes.')
    if module.params.get('acme_version') < 2:
        module.fail_json(msg='The acme_account module requires the ACME v2 protocol!')

    try:
        account = ACMEAccount(module)
        changed = False
        state = module.params.get('state')
        diff_before = {}
        diff_after = {}
        if state == 'absent':
            created, account_data = account.setup_account(allow_creation=False)
            if account_data:
                diff_before = dict(account_data)
                diff_before['public_account_key'] = account.key_data['jwk']
            if created:
                raise AssertionError('Unwanted account creation')
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
                changed = True
        elif state == 'present':
            allow_creation = module.params.get('allow_creation')
            # Make sure contact is a list of strings (unfortunately, Ansible doesn't do that for us)
            contact = [str(v) for v in module.params.get('contact')]
            terms_agreed = module.params.get('terms_agreed')
            created, account_data = account.setup_account(
                contact,
                terms_agreed=terms_agreed,
                allow_creation=allow_creation,
            )
            if account_data is None:
                raise ModuleFailException(msg='Account does not exist or is deactivated.')
            if created:
                diff_before = {}
            else:
                diff_before = dict(account_data)
                diff_before['public_account_key'] = account.key_data['jwk']
            updated = False
            if not created:
                updated, account_data = account.update_account(account_data, contact)
            changed = created or updated
            diff_after = dict(account_data)
            diff_after['public_account_key'] = account.key_data['jwk']
        elif state == 'changed_key':
            # Parse new account key
            error, new_key_data = account.parse_key(
                module.params.get('new_account_key_src'),
                module.params.get('new_account_key_content')
            )
            if error:
                raise ModuleFailException("error while parsing account key: %s" % error)
            # Verify that the account exists and has not been deactivated
            created, account_data = account.setup_account(allow_creation=False)
            if created:
                raise AssertionError('Unwanted account creation')
            if account_data is None:
                raise ModuleFailException(msg='Account does not exist or is deactivated.')
            diff_before = dict(account_data)
            diff_before['public_account_key'] = account.key_data['jwk']
            # Now we can start the account key rollover
            if not module.check_mode:
                # Compose inner signed message
                # https://tools.ietf.org/html/rfc8555#section-7.3.5
                url = account.directory['keyChange']
                protected = {
                    "alg": new_key_data['alg'],
                    "jwk": new_key_data['jwk'],
                    "url": url,
                }
                payload = {
                    "account": account.uri,
                    "newKey": new_key_data['jwk'],  # specified in draft 12 and older
                    "oldKey": account.jwk,  # specified in draft 13 and newer
                }
                data = account.sign_request(protected, payload, new_key_data)
                # Send request and verify result
                result, info = account.send_signed_request(url, data)
                if info['status'] != 200:
                    raise ModuleFailException('Error account key rollover: {0} {1}'.format(info['status'], result))
                if module._diff:
                    account.key_data = new_key_data
                    account.jws_header['alg'] = new_key_data['alg']
                    diff_after = account.get_account_data()
            elif module._diff:
                # Kind of fake diff_after
                diff_after = dict(diff_before)
            diff_after['public_account_key'] = new_key_data['jwk']
            changed = True
        result = {
            'changed': changed,
            'account_uri': account.uri,
        }
        if module._diff:
            result['diff'] = {
                'before': diff_before,
                'after': diff_after,
            }
        module.exit_json(**result)
    except ModuleFailException as e:
        e.do_fail(module)


if __name__ == '__main__':
    main()
