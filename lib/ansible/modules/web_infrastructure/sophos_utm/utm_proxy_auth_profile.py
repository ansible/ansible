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
module: utm_proxy_auth_profile

author:
    - Stephan Schwarz (@stearz)

short_description: create, update or destroy reverse_proxy auth_profile entry in Sophos UTM

description:
    - Create, update or destroy a reverse_proxy auth_profile entry in SOPHOS UTM.
    - This module needs to have the REST Ability of the UTM to be activated.

version_added: "2.8"

options:
    name:
        description:
          - The name of the object. Will be used to identify the entry
        required: true
    aaa:
        description:
          - List of references to utm_aaa objects (allowed users or groups)
        required: true
    basic_prompt:
        description:
          - The message in the basic authentication prompt
        required: true
    backend_mode:
        description:
          - Specifies if the backend server needs authentication ([Basic|None])
        default: None
        choices:
          - Basic
          - None
    backend_strip_basic_auth:
        description:
          - Should the login data be stripped when proxying the request to the backend host
        type: bool
        default: True
        choices:
          - True
          - False
    backend_user_prefix:
        description:
          - Prefix string to prepend to the username for backend authentication
        default: ""
    backend_user_suffix:
        description:
          - Suffix string to append to the username for backend authentication
        default: ""
    comment:
        description:
          - Optional comment string
        default: ""
    frontend_cookie:
        description:
          - Frontend cookie name
    frontend_cookie_secret:
        description:
          - Frontend cookie secret
    frontend_form:
        description:
          - Frontend authentication form name
    frontend_form_template:
        description:
          - Frontend authentication form template
        default: ""
    frontend_login:
        description:
          - Frontend login name
    frontend_logout:
        description:
          - Frontend logout name
    frontend_mode:
        description:
          - Frontend authentication mode (Form|Basic)
        default: Basic
        choices:
          - Basic
          - Form
    frontend_realm:
        description:
          - Frontend authentication realm
    frontend_session_allow_persistency:
        description:
          - Allow session persistency
        type: bool
        default: False
        choices:
          - True
          - False
    frontend_session_lifetime:
        description:
          - session lifetime
        required: true
    frontend_session_lifetime_limited:
        description:
          - Specifies if limitation of session lifetime is active
        type: bool
        default: True
        choices:
          - True
          - False
    frontend_session_lifetime_scope:
        description:
          - scope for frontend_session_lifetime (days|hours|minutes)
        default: hours
        choices:
          - days
          - hours
          - minutes
    frontend_session_timeout:
        description:
          - session timeout
        required: true
    frontend_session_timeout_enabled:
        description:
          - Specifies if session timeout is active
        type: bool
        default: True
        choices:
          - True
          - False
    frontend_session_timeout_scope:
        description:
          - scope for frontend_session_timeout (days|hours|minutes)
        default: minutes
        choices:
          - days
          - hours
          - minutes
    logout_delegation_urls:
        description:
          - List of logout URLs that logouts are delegated to
        default: []
    logout_mode:
        description:
          - Mode of logout (None|Delegation)
        default: None
        choices:
          - None
          - Delegation
    redirect_to_requested_url:
        description:
          - Should a redirect to the requested URL be made
        type: bool
        default: False
        choices:
          - True
          - False

extends_documentation_fragment:
    - utm
"""

EXAMPLES = """
- name: Create UTM proxy_auth_profile
  utm_proxy_auth_profile:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestAuthProfileEntry
    aaa: [REF_OBJECT_STRING,REF_ANOTHEROBJECT_STRING]
    basic_prompt: "Authentication required: Please login"
    frontend_session_lifetime: 1
    frontend_session_timeout: 1
    state: present

- name: Remove UTM proxy_auth_profile
  utm_proxy_auth_profile:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestAuthProfileEntry
    state: absent

- name: Read UTM proxy_auth_profile
  utm_proxy_auth_profile:
    utm_host: sophos.host.name
    utm_token: abcdefghijklmno1234
    name: TestAuthProfileEntry
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
            type: str
        _locked:
            description: Whether or not the object is currently locked
            type: bool
        _type:
            description: The type of the object
            type: str
        name:
            description: The name of the object
            type: str
        aaa:
            description: List of references to utm_aaa objects (allowed users or groups)
            type: list
        basic_prompt:
            description: The message in the basic authentication prompt
            type: str
        backend_mode:
            description: Specifies if the backend server needs authentication ([Basic|None])
            type: str
        backend_strip_basic_auth:
            description: Should the login data be stripped when proxying the request to the backend host
            type: bool
        backend_user_prefix:
            description: Prefix string to prepend to the username for backend authentication
            type: str
        backend_user_suffix:
            description: Suffix string to append to the username for backend authentication
            type: str
        comment:
            description: Optional comment string
            type: str
        frontend_cookie:
            description: Frontend cookie name
            type: str
        frontend_cookie_secret:
            description: Frontend cookie secret
            type: str
        frontend_form:
            description: Frontend authentication form name
            type: str
        frontend_form_template:
            description: Frontend authentication form template
            type: str
        frontend_login:
            description: Frontend login name
            type: str
        frontend_logout:
            description: Frontend logout name
            type: str
        frontend_mode:
            description: Frontend authentication mode (Form|Basic)
            type: str
        frontend_realm:
            description: Frontend authentication realm
            type: str
        frontend_session_allow_persistency:
            description: Allow session persistency
            type: bool
        frontend_session_lifetime:
            description: session lifetime
            type: int
        frontend_session_lifetime_limited:
            description: Specifies if limitation of session lifetime is active
            type: bool
        frontend_session_lifetime_scope:
            description: scope for frontend_session_lifetime (days|hours|minutes)
            type: str
        frontend_session_timeout:
            description: session timeout
            type: int
        frontend_session_timeout_enabled:
            description: Specifies if session timeout is active
            type: bool
        frontend_session_timeout_scope:
            description: scope for frontend_session_timeout (days|hours|minutes)
            type: str
        logout_delegation_urls:
            description: List of logout URLs that logouts are delegated to
            type: list
        logout_mode:
            description: Mode of logout (None|Delegation)
            type: str
        redirect_to_requested_url:
            description: Should a redirect to the requested URL be made
            type: bool
"""

from ansible.module_utils.utm_utils import UTM, UTMModule
from ansible.module_utils._text import to_native


def main():
    endpoint = "reverse_proxy/auth_profile"
    key_to_check_for_changes = ["aaa", "basic_prompt", "backend_mode", "backend_strip_basic_auth",
                                "backend_user_prefix", "backend_user_suffix", "comment", "frontend_cookie",
                                "frontend_cookie_secret", "frontend_form", "frontend_form_template",
                                "frontend_login", "frontend_logout", "frontend_mode", "frontend_realm",
                                "frontend_session_allow_persistency", "frontend_session_lifetime",
                                "frontend_session_lifetime_limited", "frontend_session_lifetime_scope",
                                "frontend_session_timeout", "frontend_session_timeout_enabled",
                                "frontend_session_timeout_scope", "logout_delegation_urls", "logout_mode",
                                "redirect_to_requested_url"]

    module = UTMModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            aaa=dict(type='list', elements='str', required=True),
            basic_prompt=dict(type='str', required=True),
            backend_mode=dict(type='str', required=False, default="None", choices=['Basic', 'None']),
            backend_strip_basic_auth=dict(type='bool', required=False, default=True, choices=[True, False]),
            backend_user_prefix=dict(type='str', required=False, default=""),
            backend_user_suffix=dict(type='str', required=False, default=""),
            comment=dict(type='str', required=False, default=""),
            frontend_cookie=dict(type='str', required=False),
            frontend_cookie_secret=dict(type='str', required=False, no_log=True),
            frontend_form=dict(type='str', required=False),
            frontend_form_template=dict(type='str', required=False, default=""),
            frontend_login=dict(type='str', required=False),
            frontend_logout=dict(type='str', required=False),
            frontend_mode=dict(type='str', required=False, default="Basic", choices=['Basic', 'Form']),
            frontend_realm=dict(type='str', required=False),
            frontend_session_allow_persistency=dict(type='bool', required=False, default=False, choices=[True, False]),
            frontend_session_lifetime=dict(type='int', required=True),
            frontend_session_lifetime_limited=dict(type='bool', required=False, default=True, choices=[True, False]),
            frontend_session_lifetime_scope=dict(type='str', required=False, default="hours", choices=['days', 'hours', 'minutes']),
            frontend_session_timeout=dict(type='int', required=True),
            frontend_session_timeout_enabled=dict(type='bool', required=False, default=True, choices=[True, False]),
            frontend_session_timeout_scope=dict(type='str', required=False, default="minutes", choices=['days', 'hours', 'minutes']),
            logout_delegation_urls=dict(type='list', elements='str', required=False, default=[]),
            logout_mode=dict(type='str', required=False, default="None", choices=['None', 'Delegation']),
            redirect_to_requested_url=dict(type='bool', required=False, default=False, choices=[True, False])
        )
    )
    try:
        UTM(module, endpoint, key_to_check_for_changes).execute()
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
