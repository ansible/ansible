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
module: avi_applicationpersistenceprofile
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of ApplicationPersistenceProfile Avi RESTful Object
description:
    - This module is used to configure ApplicationPersistenceProfile object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.3"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent","present"]
    app_cookie_persistence_profile:
        description:
            - Specifies the application cookie persistence profile parameters.
    description:
        description:
            - User defined description for the object.
    hdr_persistence_profile:
        description:
            - Specifies the custom http header persistence profile parameters.
    http_cookie_persistence_profile:
        description:
            - Specifies the http cookie persistence profile parameters.
    ip_persistence_profile:
        description:
            - Specifies the client ip persistence profile parameters.
    is_federated:
        description:
            - This field describes the object's replication scope.
            - If the field is set to false, then the object is visible within the controller-cluster and its associated service-engines.
            - If the field is set to true, then the object is replicated across the federation.
            - Field introduced in 17.1.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.4"
    name:
        description:
            - A user-friendly name for the persistence profile.
        required: true
    persistence_type:
        description:
            - Method used to persist clients to the same server for a duration of time or a session.
            - Enum options - PERSISTENCE_TYPE_CLIENT_IP_ADDRESS, PERSISTENCE_TYPE_HTTP_COOKIE, PERSISTENCE_TYPE_TLS, PERSISTENCE_TYPE_CLIENT_IPV6_ADDRESS,
            - PERSISTENCE_TYPE_CUSTOM_HTTP_HEADER, PERSISTENCE_TYPE_APP_COOKIE, PERSISTENCE_TYPE_GSLB_SITE.
            - Default value when not specified in API or module is interpreted by Avi Controller as PERSISTENCE_TYPE_CLIENT_IP_ADDRESS.
        required: true
    server_hm_down_recovery:
        description:
            - Specifies behavior when a persistent server has been marked down by a health monitor.
            - Enum options - HM_DOWN_PICK_NEW_SERVER, HM_DOWN_ABORT_CONNECTION, HM_DOWN_CONTINUE_PERSISTENT_SERVER.
            - Default value when not specified in API or module is interpreted by Avi Controller as HM_DOWN_PICK_NEW_SERVER.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Uuid of the persistence profile.
extends_documentation_fragment:
    - avi
'''


EXAMPLES = '''
  - name: Create an Application Persistence setting using http cookie.
    avi_applicationpersistenceprofile:
      controller: ''
      username: ''
      password: ''
      http_cookie_persistence_profile:
        always_send_cookie: false
        cookie_name: My-HTTP
        key:
        - aes_key: ShYGZdMks8j6Bpvm2sCvaXWzvXms2Z9ob+TTjRy46lQ=
          name: c1276819-550c-4adf-912d-59efa5fd7269
        - aes_key: OGsyVk84VCtyMENFOW0rMnRXVnNrb0RzdG5mT29oamJRb0dlbHZVSjR1az0=
          name: a080de57-77c3-4580-a3ea-e7a6493c14fd
        - aes_key: UVN0cU9HWmFUM2xOUzBVcmVXaHFXbnBLVUUxMU1VSktSVU5HWjJOWmVFMTBUMUV4UmxsNk4xQmFZejA9
          name: 60478846-33c6-484d-868d-bbc324fce4a5
        timeout: 15
      name: My-HTTP-Cookie
      persistence_type: PERSISTENCE_TYPE_HTTP_COOKIE
      server_hm_down_recovery: HM_DOWN_PICK_NEW_SERVER
      tenant_ref: Demo
'''
RETURN = '''
obj:
    description: ApplicationPersistenceProfile (api/applicationpersistenceprofile) object
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
        app_cookie_persistence_profile=dict(type='dict',),
        description=dict(type='str',),
        hdr_persistence_profile=dict(type='dict',),
        http_cookie_persistence_profile=dict(type='dict',),
        ip_persistence_profile=dict(type='dict',),
        is_federated=dict(type='bool',),
        name=dict(type='str', required=True),
        persistence_type=dict(type='str', required=True),
        server_hm_down_recovery=dict(type='str',),
        tenant_ref=dict(type='str',),
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
    return avi_ansible_api(module, 'applicationpersistenceprofile',
                           set([]))

if __name__ == '__main__':
    main()
