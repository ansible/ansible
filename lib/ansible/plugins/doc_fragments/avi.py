# -*- coding: utf-8 -*-

# Created on December 12, 2016
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
# Avi Version: 16.3.4
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Avi common documentation fragment
    DOCUMENTATION = r'''
options:
    controller:
        description:
            - IP address or hostname of the controller. The default value is the environment variable C(AVI_CONTROLLER).
        type: str
        default: ''
    username:
        description:
            - Username used for accessing Avi controller. The default value is the environment variable C(AVI_USERNAME).
        type: str
        default: ''
    password:
        description:
            - Password of Avi user in Avi controller. The default value is the environment variable C(AVI_PASSWORD).
        type: str
        default: ''
    tenant:
        description:
            - Name of tenant used for all Avi API calls and context of object.
        type: str
        default: admin
    tenant_uuid:
        description:
            - UUID of tenant used for all Avi API calls and context of object.
        type: str
        default: ''
    api_version:
        description:
            - Avi API version of to use for Avi API and objects.
        type: str
        default: 16.4.4
    avi_credentials:
        description:
            - Avi Credentials dictionary which can be used in lieu of enumerating Avi Controller login details.
        suboptions:
            controller:
                description:
                  - Avi controller IP or SQDN
            username:
                description:
                  - Avi controller username
            password:
                description:
                  - Avi controller password
            api_version:
                description:
                  - Avi controller version
                default: 16.4.4
            tenant:
                description:
                  - Avi controller tenant
                default: admin
            tenant_uuid:
                description:
                  - Avi controller tenant UUID
            port:
                description:
                  - Avi controller port
            token:
                description:
                  - Avi controller API token
            timeout:
                description:
                  - Avi controller request timeout
                default: 300
            session_id:
                description:
                  - Avi controller API session id to reuse existing session with csrftoken
            csrftoken:
                description:
                  - Avi controller API csrftoken to reuse existing session with session id
        type: dict
        version_added: "2.5"
    api_context:
        description:
            - Avi API context that includes current session ID and CSRF Token.
            - This allows user to perform single login and re-use the session.
        type: dict
        version_added: "2.5"
    avi_disable_session_cache_as_fact:
        description:
            - It disables avi session information to be cached as a fact.
        type: bool
        version_added: "2.6"

notes:
  - For more information on using Ansible to manage Avi Network devices see U(https://www.ansible.com/ansible-avi-networks).
'''
