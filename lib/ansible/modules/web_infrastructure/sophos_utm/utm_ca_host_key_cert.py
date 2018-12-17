#!/usr/bin/python

# Copyright: (c) 2018, Stephan Schwarz <stearz@gmx.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
---
module: utm_ca_host_key_cert

author:
    - Stephan Schwarz (@stearz)

short_description: create, update or destroy ca host_key_cert entry in Sophos UTM

description:
    - Create, update or destroy a ca host_key_cert entry in SOPHOS UTM.
    - This module needs to have the REST Ability of the UTM to be activated.

version_added: "2.8"

options:
    name:
        description:
          - The name of the object. Will be used to identify the entry.
        required: true
    ca:
        description:
          - A reference to an existing utm_ca_signing_ca or utm_ca_verification_ca object.
        required: true
    meta:
        description:
          - A reference to an existing utm_ca_meta_x509 object.
        required: true
    certificate:
        description:
          - The certificate in PEM format.
        required: true
    comment:
        description:
          - Optional comment string.
    encrypted:
        description:
          - Optionally enable encryption.
        default: False
        type: bool
    key:
        description:
          - Optional private key in PEM format.

extends_documentation_fragment:
    - utm
"""

EXAMPLES = """
# Create a ca_host_key_cert entry
- name: utm ca_host_key_cert
  utm_ca_host_key_cert:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestHostKeyCertEntry
    ca: REF_ca/signing_ca_OBJECT_STRING
    meta: REF_ca/meta_x509_OBJECT_STRING
    certificate: |
      --- BEGIN CERTIFICATE ---
      . . .
       . . .
      . . .
      --- END CERTIFICATE ---
    state: present

# Remove a ca_host_key_cert entry
- name: utm ca_host_key_cert
  utm_ca_host_key_cert:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestHostKeyCertEntry
    state: absent

# Read a ca_host_key_cert entry
- name: utm ca_host_key_cert
  utm_ca_host_key_cert:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestHostKeyCertEntry
    state: info

"""

RETURN = """
result:
    description: The utm object that was created
    returned: success
    type: complex
    contains:
        _ref:
            description: The reference name of the object
            type: string
        _locked:
            description: Whether or not the object is currently locked
            type: boolean
        _type:
            description: The type of the object
            type: string
        name:
            description: The name of the object
            type: string
        ca:
            description: A reference to an existing utm_ca_signing_ca or utm_ca_verification_ca object.
            type: string
        meta:
            description: A reference to an existing utm_ca_meta_x509 object.
            type: string
        certificate:
            description: The certificate in PEM format
            type: string
        comment:
            description: Comment string (may be empty string)
            type: string
        encrypted:
            description: If encryption is enabled
            type: bool
        key:
            description: Private key in PEM format (may be empty string)
            type: string
"""

from ansible.module_utils.utm_utils import UTM, UTMModule
from ansible.module_utils._text import to_native


def main():
    endpoint = "ca/host_key_cert"
    key_to_check_for_changes = ["ca", "certificate", "comment", "encrypted", "key", "meta"]
    module = UTMModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            ca=dict(type='str', required=True),
            meta=dict(type='str', required=True),
            certificate=dict(type='str', required=True),
            comment=dict(type='str', required=False),
            encrypted=dict(type='bool', required=False, default=False),
            key=dict(type='str', required=False, no_log=True),
        )
    )
    try:
        # This is needed because the bool value only accepts int values in the backend
        UTM(module, endpoint, key_to_check_for_changes).execute()
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
