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
short_description: Create, modify or delete accounts with Let's Encrypt
description:
   - "Allows to create, modify or delete accounts with Let's Encrypt.
      Let's Encrypt is a free, automated, and open certificate authority
      (CA), run for the public's benefit. For details see U(https://letsencrypt.org)."
   - "This module only works with the ACME v2 protocol."
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
    required: true
    choices:
    - present
    - absent
    - changed_key
  allow_creation:
    description:
      - "Whether account creation is allowed (when state is C(present))."
    default: yes
    type: bool
  contact:
    description:
      - "A list of contact URLs."
      - "Email addresses must be prefixed with C(mailto:)."
      - "See https://tools.ietf.org/html/draft-ietf-acme-acme-10#section-7.1.2
         for what is allowed."
      - "Must be specified when state is C(present). Will be ignored
         if state is C(absent) or C(changed_key)."
    default: []
  terms_agreed:
    description:
      - "Boolean indicating whether you agree to the terms of service document."
      - "ACME servers can require this to be true."
    default: no
    type: bool
  new_account_key_src:
    description:
      - "Path to a file containing the Let's Encrypt account RSA or Elliptic Curve
         key to change to."
      - "Same restrictions apply as to C(account_key_src)."
      - "Mutually exclusive with C(new_account_key_content)."
      - "Required if C(new_account_key_content) is not used and state is C(changed_key)."
  new_account_key_content:
    description:
      - "Content of the Let's Encrypt account RSA or Elliptic Curve key to change to."
      - "Same restrictions apply as to C(account_key_content)."
      - "Mutually exclusive with C(new_account_key_src)."
      - "Required if C(new_account_key_src) is not used and state is C(changed_key)."
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
  type: string
'''

from ansible.module_utils.acme import (
    ModuleFailException, ACMEAccount
)

import os
import tempfile
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def main():
    module = AnsibleModule(
        argument_spec=dict(
            account_key_src=dict(type='path', aliases=['account_key']),
            account_key_content=dict(type='str', no_log=True),
            acme_directory=dict(required=False, default='https://acme-staging.api.letsencrypt.org/directory', type='str'),
            acme_version=dict(required=False, default=1, choices=[1, 2], type='int'),
            validate_certs=dict(required=False, default=True, type='bool'),
            terms_agreed=dict(required=False, default=False, type='bool'),
            state=dict(required=True, choices=['absent', 'present', 'changed_key'], type='str'),
            allow_creation=dict(required=False, default=True, type='bool'),
            contact=dict(required=False, type='list', default=[]),
            new_account_key_src=dict(type='path'),
            new_account_key_content=dict(type='str', no_log=True),
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

    if not module.params.get('validate_certs'):
        module.warn(warning='Disabling certificate validation for communications with ACME endpoint. ' +
                            'This should only be done for testing against a local ACME server for ' +
                            'development purposes, but *never* for production purposes.')
    if module.params.get('acme_version') < 2:
        module.fail_json(msg='The acme_account module requires the ACME v2 protocol!')

    try:
        account = ACMEAccount(module)
        state = module.params.get('state')
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
        elif state == 'present':
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
        elif state == 'changed_key':
            # Get hold of new account key
            new_key = module.params.get('new_account_key_src')
            if new_key is None:
                fd, tmpsrc = tempfile.mkstemp()
                module.add_cleanup_file(tmpsrc)  # Ansible will delete the file on exit
                f = os.fdopen(fd, 'wb')
                try:
                    f.write(module.params.get('new_account_key_content').encode('utf-8'))
                    new_key = tmpsrc
                except Exception as err:
                    try:
                        f.close()
                    except Exception as e:
                        pass
                    raise ModuleFailException("failed to create temporary content file: %s" % to_native(err), exception=traceback.format_exc())
                f.close()
            # Parse new account key
            error, new_key_data = account.parse_account_key(new_key)
            if error:
                raise ModuleFailException("error while parsing account key: %s" % error)
            # Verify that the account exists and has not been deactivated
            changed = account.init_account(
                [],
                allow_creation=False,
                update_contact=False,
            )
            if changed:
                raise AssertionError('Unwanted account change')
            if account.uri is None or account.get_account_data() is None:
                raise ModuleFailException(msg='Account does not exist or is deactivated.')
            # Now we can start the account key rollover
            if not module.check_mode:
                # Compose inner signed message
                # https://tools.ietf.org/html/draft-ietf-acme-acme-12#section-7.3.6
                url = account.directory['keyChange']
                protected = {
                    "alg": new_key_data['alg'],
                    "jwk": new_key_data['jwk'],
                    "url": url,
                }
                payload = {
                    "account": account.uri,
                    "newKey": new_key_data['jwk'],  # specified in draft 12
                    "oldKey": account.jwk,  # discussed in https://github.com/ietf-wg-acme/acme/pull/425,
                                            # might be required in draft 13
                }
                data = account.sign_request(protected, payload, new_key_data, new_key)
                # Send request and verify result
                result, info = account.send_signed_request(url, data)
                if info['status'] != 200:
                    raise ModuleFailException('Error account key rollover: {0} {1}'.format(info['status'], result))
            module.exit_json(changed=True, account_uri=account.uri)
    except ModuleFailException as e:
        e.do_fail(module)


if __name__ == '__main__':
    main()
