#!/usr/bin/python

# Copyright: (c) 2018, Johannes Brunswicker <johannes.brunswicker@gmail.com>
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
module: utm_proxy_form_template_info

author:
    - Johannes Brunswicker (@MatrixCrawler)

short_description: Query info for reverse_proxy form_template entry in Sophos UTM

description:
    - Gathers info for reverse_proxy form_template entry in SOPHOS UTM.
    - This module needs to have the REST Ability of the UTM to be activated.

version_added: "2.8"

options:
    name:
        description:
          - The name of the object. Will be used to identify the entry
        required: true
    assets:
        description:
          - A list of hashes of assets. In the form "filename":"fileContentAsBase64"
    comment:
        description:
          - The optional comment string
    filename:
        description:
          - A name for the file
    template:
        description:
          - The html template as base64 string that will be the content of C(filename)

extends_documentation_fragment:
    - utm
"""

EXAMPLES = """
- name: Create UTM proxy_form_template
  utm_proxy_form_template_info:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestFormTemplateEntry
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
        assets:
            description: A list of asset hashes
            type: list
        comment:
            description: The comment string
            type: string
        filename:
            description: The name of the template file
            type: string
        template:
            description: The content of the template file in base64
            type: string
"""

from ansible.module_utils.utm_utils import UTM, UTMModule
from ansible.module_utils._text import to_native


def main():
    endpoint = "reverse_proxy/form_template"
    key_to_check_for_changes = []
    module = UTMModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            assets=dict(type='list', elements='str', required=False),
            comment=dict(type='str', required=False, default=""),
            filename=dict(type='str', required=False),
            template=dict(type='str', required=False)
        )
    )
    try:
        UTM(module, endpoint, key_to_check_for_changes, info_only=True).execute()
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
