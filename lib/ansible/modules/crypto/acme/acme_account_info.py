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
options:
  retrieve_orders:
    description:
      - "Whether to retrieve the list of order URLs or order objects, if provided
         by the ACME server."
      - "A value of C(ignore) will not fetch the list of orders."
      - "Currently, Let's Encrypt does not return orders, so the C(orders) result
         will always be empty."
    type: str
    choices:
      - ignore
      - url_list
      - object_list
    default: ignore
    version_added: "2.9"
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
      description:
        - A URL where a list of orders can be retrieved for this account.
        - Use the I(retrieve_orders) option to query this URL and retrieve the
          complete list of orders.
      returned: always
      type: str
      sample: https://example.ca/account/1/orders
    public_account_key:
      description: the public account key as a L(JSON Web Key,https://tools.ietf.org/html/rfc7517).
      returned: always
      type: str
      sample: https://example.ca/account/1/orders

orders:
  description:
    - "The list of orders."
    - "If I(retrieve_orders) is C(url_list), this will be a list of URLs."
    - "If I(retrieve_orders) is C(object_list), this will be a list of objects."
  type: list
  returned: if account exists, I(retrieve_orders) is not C(ignore), and server supports order listing
  contains:
    status:
      description: The order's status.
      type: str
      choices:
        - pending
        - ready
        - processing
        - valid
        - invalid
    expires:
      description:
        - When the order expires.
        - Timestamp should be formatted as described in RFC3339.
        - Only required to be included in result when I(status) is C(pending) or C(valid).
      type: str
      returned: when server gives expiry date
    identifiers:
      description:
        - List of identifiers this order is for.
      type: list
      contains:
        type:
          description: Type of identifier. C(dns) or C(ip).
          type: str
        value:
          description: Name of identifier. Hostname or IP address.
          type: str
        wildcard:
          description: "Whether I(value) is actually a wildcard. The wildcard
                        prefix C(*.) is not included in I(value) if this is C(true)."
          type: bool
          returned: required to be included if the identifier is wildcarded
    notBefore:
      description:
        - The requested value of the C(notBefore) field in the certificate.
        - Date should be formatted as described in RFC3339.
        - Server is not required to return this.
      type: str
      returned: when server returns this
    notAfter:
      description:
        - The requested value of the C(notAfter) field in the certificate.
        - Date should be formatted as described in RFC3339.
        - Server is not required to return this.
      type: str
      returned: when server returns this
    error:
      description:
        - In case an error occurred during processing, this contains information about the error.
        - The field is structured as a problem document (RFC7807).
      type: complex
      returned: when an error occurred
    authorizations:
      description:
        - A list of URLs for authorizations for this order.
      type: list
    finalize:
      description:
        - A URL used for finalizing an ACME order.
      type: str
    certificate:
      description:
        - The URL for retrieving the certificate.
      type: str
      returned: when certificate was issued
'''

from ansible.module_utils.acme import (
    ModuleFailException,
    ACMEAccount,
    handle_standard_module_arguments,
    process_links,
    get_default_argspec,
)

from ansible.module_utils.basic import AnsibleModule


def get_orders_list(module, account, orders_url):
    '''
    Retrieves orders list (handles pagination).
    '''
    orders = []
    while orders_url:
        # Get part of orders list
        res, info = account.get_request(orders_url, parse_json_result=True, fail_on_error=True)
        if not res.get('orders'):
            if orders:
                module.warn('When retrieving orders list part {0}, got empty result list'.format(orders_url))
            break
        # Add order URLs to result list
        orders.extend(res['orders'])
        # Extract URL of next part of results list
        new_orders_url = []

        def f(link, relation):
            if relation == 'next':
                new_orders_url.append(link)

        process_links(info, f)
        new_orders_url.append(None)
        previous_orders_url, orders_url = orders_url, new_orders_url.pop(0)
        if orders_url == previous_orders_url:
            # Prevent infinite loop
            orders_url = None
    return orders


def get_order(account, order_url):
    '''
    Retrieve order data.
    '''
    return account.get_request(order_url, parse_json_result=True, fail_on_error=True)[0]


def main():
    argument_spec = get_default_argspec()
    argument_spec.update(dict(
        retrieve_orders=dict(type='str', default='ignore', choices=['ignore', 'url_list', 'object_list']),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
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
    handle_standard_module_arguments(module, needs_acme_v2=True)

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
            # Retrieve orders list
            if account_data.get('orders') and module.params['retrieve_orders'] != 'ignore':
                orders = get_orders_list(module, account, account_data['orders'])
                if module.params['retrieve_orders'] == 'url_list':
                    result['orders'] = orders
                else:
                    result['orders'] = [get_order(account, order) for order in orders]
        module.exit_json(**result)
    except ModuleFailException as e:
        e.do_fail(module)


if __name__ == '__main__':
    main()
