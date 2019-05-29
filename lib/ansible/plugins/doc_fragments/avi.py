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
            - Avi Credentials dictionary which can be used in lieu of enumerating Avi Controller login secrets.
            - info of this dict will not be logged.
            - THis dict will contain only the login secrets like password.
            - Ansible dose complete search and replace of no log params so all controller information should go in avi_login_info
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
    avi_login_info:
        description:
            - Avi login info dictionary which can be used in lieu of enumerating Avi Controller login details.
            - This dictionary should not contain login secrets avi_credentials should be used for login secrets.
            - This should contain information like controller, username, tenant, api_version
        type: dict
        version_added: "2.9"
notes:
  - For more information on using Ansible to manage Avi Network devices see U(https://www.ansible.com/ansible-avi-networks).
'''
