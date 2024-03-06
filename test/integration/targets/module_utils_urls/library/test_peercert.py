#!/usr/bin/python

# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r'''
---
module: test_perrcert
short_description: Test getting the peer certificate of a HTTP response
description: Test getting the peer certificate of a HTTP response.
options:
  url:
    description: The endpoint to get the peer cert for
    required: true
    type: str
author:
- Ansible Project
'''

EXAMPLES = r'''
#
'''

RETURN = r'''
#
'''

import base64

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.urls import getpeercert, Request


def get_x509_shorthand(name, value):
    prefix = {
        'countryName': 'C',
        'stateOrProvinceName': 'ST',
        'localityName': 'L',
        'organizationName': 'O',
        'commonName': 'CN',
        'organizationalUnitName': 'OU',
    }[name]

    return '%s=%s' % (prefix, value)


def main():
    module_args = dict(
        url=dict(type='str', required=True),
    )
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )
    result = {
        'changed': False,
        'cert': None,
        'raw_cert': None,
    }

    req = Request().get(module.params['url'])
    try:
        cert = getpeercert(req)
        b_cert = getpeercert(req, binary_form=True)

    finally:
        req.close()

    if cert:
        processed_cert = {
            'issuer': '',
            'not_after': cert.get('notAfter', None),
            'not_before': cert.get('notBefore', None),
            'serial_number': cert.get('serialNumber', None),
            'subject': '',
            'version': cert.get('version', None),
        }

        for field in ['issuer', 'subject']:
            field_values = []
            for x509_part in cert.get(field, []):
                field_values.append(get_x509_shorthand(x509_part[0][0], x509_part[0][1]))

            processed_cert[field] = ",".join(field_values)

        result['cert'] = processed_cert

    if b_cert:
        result['raw_cert'] = to_text(base64.b64encode(b_cert))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
