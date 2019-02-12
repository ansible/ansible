#!/usr/bin/python

# Copyright: (c) 2018, Sebastian Schenzel <sebastian.schenzel@mailbox.org>
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
module: utm_proxy_exception

author:
    - Sebastian Schenzel (@RickS-C137)

short_description: Create, update or destroy reverse_proxy exception entry in Sophos UTM

description:
    - Create, update or destroy a reverse_proxy exception entry in SOPHOS UTM.
    - This module needs to have the REST Ability of the UTM to be activated.

version_added: "2.8"

options:
    name:
        description:
            - The name of the object. Will be used to identify the entry
        required: True
        type: str
    op:
        description:
            - The operand to be used with the entries of the path parameter
        default: 'AND'
        choices:
            - 'AND'
            - 'OR'
        required: False
        type: str
    path:
        description:
            - The paths the exception in the reverse proxy is defined for
        type: list
        default: []
        required: False
    skip_custom_threats_filters:
        description:
            - A list of threats to be skipped
        type: list
        default: []
        required: False
    skip_threats_filter_categories:
        description:
            - Define which categories of threats are skipped
        type: list
        default: []
        required: False
    skipav:
        description:
            - Skip the Antivirus Scanning
        default: False
        type: bool
        required: False
    skipbadclients:
        description:
            - Block clients with bad reputation
        default: False
        type: bool
        required: False
    skipcookie:
        description:
            - Skip the Cookie Signing check
        default: False
        type: bool
        required: False
    skipform:
        description:
            - Enable form hardening
        default: False
        type: bool
        required: False
    skipform_missingtoken:
        description:
            - Enable form hardening with missing tokens
        default: False
        type: bool
        required: False
    skiphtmlrewrite:
        description:
            - Protection against SQL
        default: False
        type: bool
        required: False
    skiptft:
        description:
            - Enable true file type control
        default: False
        type: bool
        required: False
    skipurl:
        description:
            - Enable static URL hardening
        default: False
        type: bool
        required: False
    source:
        description:
            - Define which categories of threats are skipped
        type: list
        default: []
        required: False
    status:
        description:
            - Status of the exception rule set
        default: True
        type: bool
        required: False

extends_documentation_fragment:
    - utm
"""

EXAMPLES = """
- name: Create UTM proxy_exception
  utm_proxy_exception:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestExceptionEntry
    backend: REF_OBJECT_STRING
    state: present

- name: Remove UTM proxy_exception
  utm_proxy_exception:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestExceptionEntry
    state: absent
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
        comment:
            description: The optional comment string
        op:
            description: The operand to be used with the entries of the path parameter
            type: string
        path:
            description: The paths the exception in the reverse proxy is defined for
            type: array
        skip_custom_threats_filters:
            description: A list of threats to be skipped
            type: array
        skip_threats_filter_categories:
            description: Define which categories of threats are skipped
            type: array
        skipav:
            description: Skip the Antivirus Scanning
            type: bool
        skipbadclients:
            description: Block clients with bad reputation
            type: bool
        skipcookie:
            description: Skip the Cookie Signing check
            type: bool
        skipform:
            description: Enable form hardening
            type: bool
        skipform_missingtoken:
            description: Enable form hardening with missing tokens
            type: bool
        skiphtmlrewrite:
            description: Protection against SQL
            type: bool
        skiptft:
            description: Enable true file type control
            type: bool
        skipurl:
            description: Enable static URL hardening
            type: bool
        source:
            description: Define which categories of threats are skipped
            type: array
"""

from ansible.module_utils.utm_utils import UTM, UTMModule
from ansible.module_utils._text import to_native


def main():
    endpoint = "reverse_proxy/exception"
    key_to_check_for_changes = ["op", "path", "skip_custom_threats_filters", "skip_threats_filter_categories", "skipav",
                                "comment", "skipbadclients", "skipcookie", "skipform", "status", "skipform_missingtoken",
                                "skiphtmlrewrite", "skiptft", "skipurl", "source"]
    module = UTMModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            op=dict(type='str', required=False, default='AND', choices=['AND', 'OR']),
            path=dict(type='list', elements='string', required=False, default=[]),
            skip_custom_threats_filters=dict(type='list', elements='string', required=False, default=[]),
            skip_threats_filter_categories=dict(type='list', elements='string', required=False, default=[]),
            skipav=dict(type='bool', required=False, default=False),
            skipbadclients=dict(type='bool', required=False, default=False),
            skipcookie=dict(type='bool', required=False, default=False),
            skipform=dict(type='bool', required=False, default=False),
            skipform_missingtoken=dict(type='bool', required=False, default=False),
            skiphtmlrewrite=dict(type='bool', required=False, default=False),
            skiptft=dict(type='bool', required=False, default=False),
            skipurl=dict(type='bool', required=False, default=False),
            source=dict(type='list', elements='string', required=False, default=[]),
            status=dict(type='bool', required=False, default=True),
        )
    )
    try:
        UTM(module, endpoint, key_to_check_for_changes).execute()
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
