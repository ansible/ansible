#!/usr/bin/python
#
# Created on Aug 25, 2016
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
# Avi Version: 16.3.8
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
module: avi_sslprofile
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of SSLProfile Avi RESTful Object
description:
    - This module is used to configure SSLProfile object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.3"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent","present"]
    accepted_ciphers:
        description:
            - Ciphers suites represented as defined by U(http://www.openssl.org/docs/apps/ciphers.html).
            - Default value when not specified in API or module is interpreted by Avi Controller as AES:3DES:RC4.
    accepted_versions:
        description:
            - Set of versions accepted by the server.
    cipher_enums:
        description:
            - Cipher_enums of sslprofile.
    description:
        description:
            - User defined description for the object.
    dhparam:
        description:
            - Dh parameters used in ssl.
            - At this time, it is not configurable and is set to 2048 bits.
    enable_ssl_session_reuse:
        description:
            - Enable ssl session re-use.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
    name:
        description:
            - Name of the object.
        required: true
    prefer_client_cipher_ordering:
        description:
            - Prefer the ssl cipher ordering presented by the client during the ssl handshake over the one specified in the ssl profile.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
    send_close_notify:
        description:
            - Send 'close notify' alert message for a clean shutdown of the ssl connection.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
    ssl_rating:
        description:
            - Sslrating settings for sslprofile.
    ssl_session_timeout:
        description:
            - The amount of time before an ssl session expires.
            - Default value when not specified in API or module is interpreted by Avi Controller as 86400.
    tags:
        description:
            - List of tag.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Unique object identifier of the object.
extends_documentation_fragment:
    - avi
'''


EXAMPLES = '''
  - name: Create SSL profile with list of allowed ciphers
    avi_sslprofile:
      controller: ''
      username: ''
      password: ''
      accepted_ciphers: >
        ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-SHA:ECDHE-ECDSA-AES256-SHA:
        ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-ECDSA-AES256-SHA384:
        AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:
        AES256-SHA:DES-CBC3-SHA:ECDHE-RSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:
        ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-SHA
      accepted_versions:
      - type: SSL_VERSION_TLS1
      - type: SSL_VERSION_TLS1_1
      - type: SSL_VERSION_TLS1_2
      cipher_enums:
      - TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
      - TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA
      - TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA
      - TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
      - TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA256
      - TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA384
      - TLS_RSA_WITH_AES_128_GCM_SHA256
      - TLS_RSA_WITH_AES_256_GCM_SHA384
      - TLS_RSA_WITH_AES_128_CBC_SHA256
      - TLS_RSA_WITH_AES_256_CBC_SHA256
      - TLS_RSA_WITH_AES_128_CBC_SHA
      - TLS_RSA_WITH_AES_256_CBC_SHA
      - TLS_RSA_WITH_3DES_EDE_CBC_SHA
      - TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA
      - TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA384
      - TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256
      - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
      - TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
      - TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA
      name: PFS-BOTH-RSA-EC
      send_close_notify: true
      ssl_rating:
        compatibility_rating: SSL_SCORE_EXCELLENT
        performance_rating: SSL_SCORE_EXCELLENT
        security_score: '100.0'
      tenant_ref: Demo
'''
RETURN = '''
obj:
    description: SSLProfile (api/sslprofile) object
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
        accepted_ciphers=dict(type='str',),
        accepted_versions=dict(type='list',),
        cipher_enums=dict(type='list',),
        description=dict(type='str',),
        dhparam=dict(type='str',),
        enable_ssl_session_reuse=dict(type='bool',),
        name=dict(type='str', required=True),
        prefer_client_cipher_ordering=dict(type='bool',),
        send_close_notify=dict(type='bool',),
        ssl_rating=dict(type='dict',),
        ssl_session_timeout=dict(type='int',),
        tags=dict(type='list',),
        tenant_ref=dict(type='str',),
        url=dict(type='str',),
        uuid=dict(type='str',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=16.3.5.post1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'sslprofile',
                           set([]))


if __name__ == '__main__':
    main()
