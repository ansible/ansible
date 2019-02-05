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
module: utm_proxy_profile_info

author:
    - Stephan Schwarz (@stearz)

short_description: query info for reverse_proxy profile entry in Sophos UTM

description:
    - Gathers info for reverse_proxy profile entry in SOPHOS UTM.
    - This module needs to have the REST Ability of the UTM to be activated.

version_added: "2.8"

options:
    name:
        description:
          - The name of the object. Will be used to identify the entry
        required: true

extends_documentation_fragment:
    - utm
"""

EXAMPLES = """
- name: Reading UTM proxy_profile
  utm_proxy_profile_info:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestProfileEntry
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
        av:
            description: Enable antivirus scanning
            type: boolean
        av_block_unscannable:
            description: Block unscannable content
            type: boolean
        av_directions:
            description: scanning download, uploads or both
            type: string
        av_engines:
            description: single or dual scan mode
            type: string
        av_size_limit:
            description: size limit for av scanner in mb
            type: integer
        av_timeout:
            description: timeout for av scanner in seconds
            type: integer
        bad_clients:
            description: Block clients with bad reputation
            type: boolean
        bad_clients_no_dnslookup:
            description: Skip remote lookups for clients with bad reputation
            type: boolean
        comment:
            description: Optionally enable encryption
            type: string
        cookiesign:
            description: Cookie signing
            type: boolean
        cookiesign_drop_unsigned:
            description: Drop unsigned cookies
            type: boolean
        custom_threats_filters:
            description: Common Threat Filter Categories
            type: list
        extensions:
            description: Extensions
            type: list
        filter:
            description: Filter rules
            type: list
        filter_mode:
            description: Filter mode
            type: string
        formhardening:
            description: Form hardening
            type: boolean
        outlookanywhere:
            description: Pass Outlook Anywhere
            type: boolean
        sec_request_body_no_files_limit:
            description: Limit
            type: integer
        skipwafrules:
            description: Skip WAF Rules
            type: list
        tft:
            description: Use True File Type Control
            type: boolean
        tft_block_unscannable:
            description: True File Type Control Block unscannable
            type: boolean
        tft_blocked_mime_types:
            description: True File Type Control Blocked MIME Types
            type: list
        threats_filter:
            description: Threads Filter
            type: boolean
        threats_filter_categories:
            description: Threads Filter Categories
            type: list
        threats_filter_rigid:
            description: Threads Filter Rigid
            type: boolean
        urlhardening:
            description: Static URL hardening
            type: boolean
        urlhardening_entrypages:
            description: Static URL hardening entrypages
            type: list
        urlhardening_entrypages_source:
            description: Static URL hardening entrypages source
            type: string
        urlhardening_sitemap_update:
            description: Static URL hardening sitemap update
            type: integer
        urlhardening_sitemap_url:
            description: Static URL hardening sitemap URL
            type: string
        waf:
            description: Enable Web Application Firewall (WAF)
            type: boolean
        wafmode:
            description: WAF mode (Reject or Monitor)
            type: string
        wafparanoia:
            description: WAF Paranoia
            type: boolean
"""

from ansible.module_utils.utm_utils import UTM, UTMModule
from ansible.module_utils._text import to_native


def main():
    endpoint = "reverse_proxy/profile"
    key_to_check_for_changes = []
    module = UTMModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
        )
    )
    try:
        UTM(module, endpoint, key_to_check_for_changes, info_only=True).execute()
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
