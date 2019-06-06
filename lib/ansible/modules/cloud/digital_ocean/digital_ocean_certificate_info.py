#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
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
module: digital_ocean_certificate_info
short_description: Gather information about DigitalOcean certificates
description:
    - This module can be used to gather information about DigitalOcean provided certificates.
    - This module was called C(digital_ocean_certificate_facts) before Ansible 2.9. The usage did not change.
author: "Abhijeet Kasurde (@Akasurde)"
version_added: "2.6"
options:
  certificate_id:
    description:
     - Certificate ID that can be used to identify and reference a certificate.
    required: false
requirements:
  - "python >= 2.6"
extends_documentation_fragment: digital_ocean.documentation
'''


EXAMPLES = '''
- name: Gather information about all certificates
  digital_ocean_certificate_info:
    oauth_token: "{{ oauth_token }}"

- name: Gather information about certificate with given id
  digital_ocean_certificate_info:
    oauth_token: "{{ oauth_token }}"
    certificate_id: "892071a0-bb95-49bc-8021-3afd67a210bf"

- name: Get not after information about certificate
  digital_ocean_certificate_info:
  register: resp_out
- set_fact:
    not_after_date: "{{ item.not_after }}"
  loop: "{{ resp_out.data|json_query(name) }}"
  vars:
    name: "[?name=='web-cert-01']"
- debug: var=not_after_date
'''


RETURN = '''
data:
    description: DigitalOcean certificate information
    returned: success
    type: list
    sample: [
        {
          "id": "892071a0-bb95-49bc-8021-3afd67a210bf",
          "name": "web-cert-01",
          "not_after": "2017-02-22T00:23:00Z",
          "sha1_fingerprint": "dfcc9f57d86bf58e321c2c6c31c7a971be244ac7",
          "created_at": "2017-02-08T16:02:37Z"
        },
    ]
'''

from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native


def core(module):
    certificate_id = module.params.get('certificate_id', None)
    rest = DigitalOceanHelper(module)

    base_url = 'certificates?'
    if certificate_id is not None:
        response = rest.get("%s/%s" % (base_url, certificate_id))
        status_code = response.status_code

        if status_code != 200:
            module.fail_json(msg="Failed to retrieve certificates for DigitalOcean")

        resp_json = response.json
        certificate = resp_json['certificate']
    else:
        certificate = rest.get_paginated_data(base_url=base_url, data_key_name='certificates')

    module.exit_json(changed=False, data=certificate)


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        certificate_id=dict(type='str', required=False),
    )
    module = AnsibleModule(argument_spec=argument_spec)
    if module._name == 'digital_ocean_certificate_facts':
        module.deprecate("The 'digital_ocean_certificate_facts' module has been renamed to 'digital_ocean_certificate_info'", version='2.13')

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()
