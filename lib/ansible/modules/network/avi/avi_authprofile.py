#!/usr/bin/python
#
# Created on Aug 25, 2016
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
# Avi Version: 17.1.1
#
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_authprofile
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of AuthProfile Avi RESTful Object
description:
    - This module is used to configure AuthProfile object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.4"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent","present"]
    description:
        description:
            - User defined description for the object.
    http:
        description:
            - Http user authentication params.
    ldap:
        description:
            - Ldap server and directory settings.
    name:
        description:
            - Name of the auth profile.
        required: true
    tacacs_plus:
        description:
            - Tacacs+ settings.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    type:
        description:
            - Type of the auth profile.
            - Enum options - AUTH_PROFILE_LDAP, AUTH_PROFILE_TACACS_PLUS.
        required: true
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Uuid of the auth profile.
extends_documentation_fragment:
    - avi
'''


EXAMPLES = '''
  - name: Create user authorization profile based on the LDAP
    avi_authprofile:
      controller: ''
      password: ''
      username: ''
      http:
        cache_expiration_time: 5
        group_member_is_full_dn: false
      ldap:
        base_dn: dc=avi,dc=local
        bind_as_administrator: true
        port: 389
        security_mode: AUTH_LDAP_SECURE_NONE
        server:
        - 10.10.0.100
        settings:
          admin_bind_dn: user@avi.local
          group_filter: (objectClass=*)
          group_member_attribute: member
          group_member_is_full_dn: true
          group_search_dn: dc=avi,dc=local
          group_search_scope: AUTH_LDAP_SCOPE_SUBTREE
          ignore_referrals: true
          password: password
          user_id_attribute: samAccountname
          user_search_dn: dc=avi,dc=local
          user_search_scope: AUTH_LDAP_SCOPE_ONE
      name: ProdAuth
      tenant_ref: admin
      type: AUTH_PROFILE_LDAP
'''
RETURN = '''
obj:
    description: AuthProfile (api/authprofile) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.avi import (
        avi_common_argument_spec, HAS_AVI, avi_ansible_api)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        description=dict(type='str',),
        http=dict(type='dict',),
        ldap=dict(type='dict',),
        name=dict(type='str', required=True),
        tacacs_plus=dict(type='dict',),
        tenant_ref=dict(type='str',),
        type=dict(type='str', required=True),
        url=dict(type='str',),
        uuid=dict(type='str',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'authprofile',
                           set([]))

if __name__ == '__main__':
    main()
