#!/usr/bin/python
#
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: supported
# Avi Version: 17.1.1
#
# Copyright: (c) 2017 Gaurav Rastogi, <grastogi@avinetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_applicationprofile
author: Gaurav Rastogi (@grastogi23) <grastogi@avinetworks.com>

short_description: Module for setup of ApplicationProfile Avi RESTful Object
description:
    - This module is used to configure ApplicationProfile object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.3"
options:
    state:
        description:
            - The state that should be applied on the entity.
        default: present
        choices: ["absent", "present"]
    avi_api_update_method:
        description:
            - Default method for object update is HTTP PUT.
            - Setting to patch will override that behavior to use HTTP PATCH.
        version_added: "2.5"
        default: put
        choices: ["put", "patch"]
    avi_api_patch_op:
        description:
            - Patch operation to use when using avi_api_update_method as patch.
        version_added: "2.5"
        choices: ["add", "replace", "delete"]
    cloud_config_cksum:
        description:
            - Checksum of application profiles.
            - Internally set by cloud connector.
            - Field introduced in 17.2.14, 18.1.5, 18.2.1.
        version_added: "2.9"
    created_by:
        description:
            - Name of the application profile creator.
            - Field introduced in 17.2.14, 18.1.5, 18.2.1.
        version_added: "2.9"
    description:
        description:
            - User defined description for the object.
    dns_service_profile:
        description:
            - Specifies various dns service related controls for virtual service.
    dos_rl_profile:
        description:
            - Specifies various security related controls for virtual service.
    http_profile:
        description:
            - Specifies the http application proxy profile parameters.
    name:
        description:
            - The name of the application profile.
        required: true
    preserve_client_ip:
        description:
            - Specifies if client ip needs to be preserved for backend connection.
            - Not compatible with connection multiplexing.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
    preserve_client_port:
        description:
            - Specifies if we need to preserve client port while preserving client ip for backend connections.
            - Field introduced in 17.2.7.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.6"
        type: bool
    sip_service_profile:
        description:
            - Specifies various sip service related controls for virtual service.
            - Field introduced in 17.2.8, 18.1.3, 18.2.1.
        version_added: "2.9"
    tcp_app_profile:
        description:
            - Specifies the tcp application proxy profile parameters.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    type:
        description:
            - Specifies which application layer proxy is enabled for the virtual service.
            - Enum options - APPLICATION_PROFILE_TYPE_L4, APPLICATION_PROFILE_TYPE_HTTP, APPLICATION_PROFILE_TYPE_SYSLOG, APPLICATION_PROFILE_TYPE_DNS,
            - APPLICATION_PROFILE_TYPE_SSL, APPLICATION_PROFILE_TYPE_SIP.
        required: true
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Uuid of the application profile.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
  - name: Create an Application Profile for HTTP application enabled for SSL traffic
    avi_applicationprofile:
      controller: '{{ controller }}'
      username: '{{ username }}'
      password: '{{ password }}'
      http_profile:
        cache_config:
          age_header: true
          aggressive: false
          date_header: true
          default_expire: 600
          enabled: false
          heuristic_expire: false
          max_cache_size: 0
          max_object_size: 4194304
          mime_types_group_refs:
          - admin:System-Cacheable-Resource-Types
          min_object_size: 100
          query_cacheable: false
          xcache_header: true
        client_body_timeout: 0
        client_header_timeout: 10000
        client_max_body_size: 0
        client_max_header_size: 12
        client_max_request_size: 48
        compression_profile:
          compressible_content_ref: admin:System-Compressible-Content-Types
          compression: false
          remove_accept_encoding_header: true
          type: AUTO_COMPRESSION
        connection_multiplexing_enabled: true
        hsts_enabled: false
        hsts_max_age: 365
        http_to_https: false
        httponly_enabled: false
        keepalive_header: false
        keepalive_timeout: 30000
        max_bad_rps_cip: 0
        max_bad_rps_cip_uri: 0
        max_bad_rps_uri: 0
        max_rps_cip: 0
        max_rps_cip_uri: 0
        max_rps_unknown_cip: 0
        max_rps_unknown_uri: 0
        max_rps_uri: 0
        post_accept_timeout: 30000
        secure_cookie_enabled: false
        server_side_redirect_to_https: false
        spdy_enabled: false
        spdy_fwd_proxy_mode: false
        ssl_client_certificate_mode: SSL_CLIENT_CERTIFICATE_NONE
        ssl_everywhere_enabled: false
        websockets_enabled: true
        x_forwarded_proto_enabled: false
        xff_alternate_name: X-Forwarded-For
        xff_enabled: true
      name: System-HTTP
      tenant_ref: admin
      type: APPLICATION_PROFILE_TYPE_HTTP
"""

RETURN = '''
obj:
    description: ApplicationProfile (api/applicationprofile) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.network.avi.avi import (
        avi_common_argument_spec, avi_ansible_api, HAS_AVI)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        avi_api_update_method=dict(default='put',
                                   choices=['put', 'patch']),
        avi_api_patch_op=dict(choices=['add', 'replace', 'delete']),
        cloud_config_cksum=dict(type='str',),
        created_by=dict(type='str',),
        description=dict(type='str',),
        dns_service_profile=dict(type='dict',),
        dos_rl_profile=dict(type='dict',),
        http_profile=dict(type='dict',),
        name=dict(type='str', required=True),
        preserve_client_ip=dict(type='bool',),
        preserve_client_port=dict(type='bool',),
        sip_service_profile=dict(type='dict',),
        tcp_app_profile=dict(type='dict',),
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
            'Avi python API SDK (avisdk>=17.1) or requests is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'applicationprofile',
                           set([]))


if __name__ == '__main__':
    main()
