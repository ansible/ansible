#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017, Abhijeet Kasurde <akasurde@redhat.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: digital_ocean_certificate
short_description: Manage certificates in DigitalOcean.
description:
    - Create, Retrieve and remove certificates DigitalOcean.
author: "Abhijeet Kasurde (@Akasurde)"
version_added: "2.5"
options:
  name:
    description:
     - The name of the certificate.
    required: true
  private_key:
    description:
    - A PEM-formatted private key content of SSL Certificate.
  leaf_certificate:
    description:
    - A PEM-formatted public SSL Certificate.
  certificate_chain:
    description:
    - The full PEM-formatted trust chain between the certificate authority's certificate and your domain's SSL certificate.
  state:
    description:
     - Whether the certificate should be present or absent.
    default: present
    choices: ['present', 'absent']
extends_documentation_fragment: digital_ocean.documentation
notes:
  - Two environment variables can be used, DO_API_KEY, DO_OAUTH_TOKEN and DO_API_TOKEN.
    They both refer to the v2 token.
'''


EXAMPLES = '''
- name: create a certificate
  digital_ocean_certificate:
    name: production
    state: present
    private_key: "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkM8OI7pRpgyj1I\n-----END PRIVATE KEY-----"
    leaf_certificate: "-----BEGIN CERTIFICATE-----\nMIIFDmg2Iaw==\n-----END CERTIFICATE-----"
    oauth_token: b7d03a6947b217efb6f3ec3bd365652

- name: create a certificate using file lookup plugin
  digital_ocean_certificate:
    name: production
    state: present
    private_key: "{{ lookup('file', 'test.key') }}"
    leaf_certificate: "{{ lookup('file', 'test.cert') }}"
    oauth_token: "{{ oauth_token }}"

- name: create a certificate with trust chain
  digital_ocean_certificate:
    name: production
    state: present
    private_key: "{{ lookup('file', 'test.key') }}"
    leaf_certificate: "{{ lookup('file', 'test.cert') }}"
    certificate_chain: "{{ lookup('file', 'chain.cert') }}"
    oauth_token: "{{ oauth_token }}"

- name: remove a certificate
  digital_ocean_certificate:
    name: production
    state: absent
    oauth_token: "{{ oauth_token }}"

'''


RETURN = ''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native


def core(module):
    state = module.params['state']
    name = module.params['name']

    rest = DigitalOceanHelper(module)

    results = dict(changed=False)

    response = rest.get('certificates')
    status_code = response.status_code
    resp_json = response.json

    if status_code != 200:
        module.fail_json(msg="Failed to retrieve certificates for DigitalOcean")

    if state == 'present':
        for cert in resp_json['certificates']:
            if cert['name'] == name:
                module.fail_json(msg="Certificate name %s already exists" % name)

        # Certificate does not exist, let us create it
        cert_data = dict(name=name,
                         private_key=module.params['private_key'],
                         leaf_certificate=module.params['leaf_certificate'])

        if module.params['certificate_chain'] is not None:
            cert_data.update(certificate_chain=module.params['certificate_chain'])

        response = rest.post("certificates", data=cert_data)
        status_code = response.status_code
        if status_code == 500:
            module.fail_json(msg="Failed to upload certificates as the certificates are malformed.")

        resp_json = response.json
        if status_code == 201:
            results.update(changed=True, response=resp_json)
        elif status_code == 422:
            results.update(changed=False, response=resp_json)

    elif state == 'absent':
        cert_id_del = None
        for cert in resp_json['certificates']:
            if cert['name'] == name:
                cert_id_del = cert['id']

        if cert_id_del is not None:
            url = "certificates/{0}".format(cert_id_del)
            response = rest.delete(url)
            if response.status_code == 204:
                results.update(changed=True)
            else:
                results.update(changed=False)
        else:
            module.fail_json(msg="Failed to find certificate %s" % name)

    module.exit_json(**results)


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        leaf_certificate=dict(type='str'),
        private_key=dict(type='str', no_log=True),
        state=dict(choices=['present', 'absent'], default='present'),
        certificate_chain=dict(type='str')
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[('state', 'present', ['name', 'leaf_certificate', 'private_key']),
                     ('state', 'absent', ['name'])
                     ],
    )

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
