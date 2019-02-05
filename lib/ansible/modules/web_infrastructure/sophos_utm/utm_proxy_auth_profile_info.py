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
module: utm_proxy_auth_profile_info

author:
    - Stephan Schwarz (@stearz)

short_description: Get a reverse_proxy auth_profile entry in Sophos UTM

description:
    - Get a reverse_proxy auth_profile entry in SOPHOS UTM.
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
- name: Read UTM proxy_auth_profile
  utm_proxy_auth_profile:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestAuthProfileEntry
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
        aaa:
            description: List of references to utm_aaa objects (allowed users or groups)
            type: list
        basic_prompt:
            description: The message in the basic authentication prompt
            type: string
        backend_mode:
            description: Specifies if the backend server needs authentication ([Basic|None])
            type: string
        backend_strip_basic_auth:
            description: Should the login data be stripped when proxying the request to the backend host
            type: boolean
        backend_user_prefix:
            description: Prefix string to prepend to the username for backend authentication
            type: string
        backend_user_suffix:
            description: Suffix string to append to the username for backend authentication
            type: string
        comment:
            description: Optional comment string
            type: string
        frontend_cookie:
            description: Frontend cookie name
            type: string
        frontend_cookie_secret:
            description: Frontend cookie secret
            type: string
        frontend_form:
            description: Frontend authentication form name
            type: string
        frontend_form_template:
            description: Frontend authentication form template
            type: string
        frontend_login:
            description: Frontend login name
            type: string
        frontend_logout:
            description: Frontend logout name
            type: string
        frontend_mode:
            description: Frontend authentication mode (Form|Basic)
            type: string
        frontend_realm:
            description: Frontend authentication realm
            type: string
        frontend_session_allow_persistency:
            description: Allow session persistency
            type: boolean
        frontend_session_lifetime:
            description: session lifetime
            type: integer
        frontend_session_lifetime_limited:
            description: Specifies if limitation of session lifetime is active
            type: boolean
        frontend_session_lifetime_scope:
            description: scope for frontend_session_lifetime (days|hours|minutes)
            type: string
        frontend_session_timeout:
            description: session timeout
            type: integer
        frontend_session_timeout_enabled:
            description: Specifies if session timeout is active
            type: boolean
        frontend_session_timeout_scope:
            description: scope for frontend_session_timeout (days|hours|minutes)
            type: string
        logout_delegation_urls:
            description: List of logout URLs that logouts are delegated to
            type: list
        logout_mode:
            description: Mode of logout (None|Delegation)
            type: string
        redirect_to_requested_url:
            description: Should a redirect to the requested URL be made
            type: boolean
"""

from ansible.module_utils.utm_utils import UTM, UTMModule
from ansible.module_utils._text import to_native


def main():
    endpoint = "reverse_proxy/auth_profile"
    key_to_check_for_changes = []

    module = UTMModule(
        argument_spec=dict(
            name=dict(type='str', required=True)
        )
    )
    try:
        UTM(module, endpoint, key_to_check_for_changes, info_only=True).execute()
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
