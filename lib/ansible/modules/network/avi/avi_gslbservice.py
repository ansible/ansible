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
module: avi_gslbservice
author: Gaurav Rastogi (@grastogi23) <grastogi@avinetworks.com>

short_description: Module for setup of GslbService Avi RESTful Object
description:
    - This module is used to configure GslbService object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: "2.4"
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
    application_persistence_profile_ref:
        description:
            - The federated application persistence associated with gslbservice site persistence functionality.
            - It is a reference to an object of type applicationpersistenceprofile.
            - Field introduced in 17.2.1.
        version_added: "2.5"
    controller_health_status_enabled:
        description:
            - Gs member's overall health status is derived based on a combination of controller and datapath health-status inputs.
            - Note that the datapath status is determined by the association of health monitor profiles.
            - Only the controller provided status is determined through this configuration.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        type: bool
    created_by:
        description:
            - Creator name.
            - Field introduced in 17.1.2.
    description:
        description:
            - User defined description for the object.
    domain_names:
        description:
            - Fully qualified domain name of the gslb service.
    down_response:
        description:
            - Response to the client query when the gslb service is down.
    enabled:
        description:
            - Enable or disable the gslb service.
            - If the gslb service is enabled, then the vips are sent in the dns responses based on reachability and configured algorithm.
            - If the gslb service is disabled, then the vips are no longer available in the dns response.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        type: bool
    groups:
        description:
            - Select list of pools belonging to this gslb service.
    health_monitor_refs:
        description:
            - Verify vs health by applying one or more health monitors.
            - Active monitors generate synthetic traffic from dns service engine and to mark a vs up or down based on the response.
            - It is a reference to an object of type healthmonitor.
    health_monitor_scope:
        description:
            - Health monitor probe can be executed for all the members or it can be executed only for third-party members.
            - This operational mode is useful to reduce the number of health monitor probes in case of a hybrid scenario.
            - In such a case, avi members can have controller derived status while non-avi members can be probed by via health monitor probes in dataplane.
            - Enum options - GSLB_SERVICE_HEALTH_MONITOR_ALL_MEMBERS, GSLB_SERVICE_HEALTH_MONITOR_ONLY_NON_AVI_MEMBERS.
            - Default value when not specified in API or module is interpreted by Avi Controller as GSLB_SERVICE_HEALTH_MONITOR_ALL_MEMBERS.
    is_federated:
        description:
            - This field indicates that this object is replicated across gslb federation.
            - Field introduced in 17.1.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        type: bool
    min_members:
        description:
            - The minimum number of members to distribute traffic to.
            - Allowed values are 1-65535.
            - Special values are 0 - 'disable'.
            - Field introduced in 17.2.4.
            - Default value when not specified in API or module is interpreted by Avi Controller as 0.
        version_added: "2.5"
    name:
        description:
            - Name for the gslb service.
        required: true
    num_dns_ip:
        description:
            - Number of ip addresses of this gslb service to be returned by the dns service.
            - Enter 0 to return all ip addresses.
            - Allowed values are 1-20.
            - Special values are 0- 'return all ip addresses'.
    pool_algorithm:
        description:
            - The load balancing algorithm will pick a gslb pool within the gslb service list of available pools.
            - Enum options - GSLB_SERVICE_ALGORITHM_PRIORITY, GSLB_SERVICE_ALGORITHM_GEO.
            - Field introduced in 17.2.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as GSLB_SERVICE_ALGORITHM_PRIORITY.
        version_added: "2.5"
    site_persistence_enabled:
        description:
            - Enable site-persistence for the gslbservice.
            - Field introduced in 17.2.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.5"
        type: bool
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    ttl:
        description:
            - Ttl value (in seconds) for records served for this gslb service by the dns service.
            - Allowed values are 1-86400.
            - Units(SEC).
    url:
        description:
            - Avi controller URL of the object.
    use_edns_client_subnet:
        description:
            - Use the client ip subnet from the edns option as source ipaddress for client geo-location and consistent hash algorithm.
            - Default is true.
            - Field introduced in 17.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
        type: bool
    uuid:
        description:
            - Uuid of the gslb service.
    wildcard_match:
        description:
            - Enable wild-card match of fqdn  if an exact match is not found in the dns table, the longest match is chosen by wild-carding the fqdn in the dns
            - request.
            - Default is false.
            - Field introduced in 17.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        type: bool
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Example to create GslbService object
  avi_gslbservice:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_gslbservice
"""

RETURN = '''
obj:
    description: GslbService (api/gslbservice) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.network.avi.avi import (
        avi_common_argument_spec, HAS_AVI, avi_ansible_api)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
        avi_api_update_method=dict(default='put',
                                   choices=['put', 'patch']),
        avi_api_patch_op=dict(choices=['add', 'replace', 'delete']),
        application_persistence_profile_ref=dict(type='str',),
        controller_health_status_enabled=dict(type='bool',),
        created_by=dict(type='str',),
        description=dict(type='str',),
        domain_names=dict(type='list',),
        down_response=dict(type='dict',),
        enabled=dict(type='bool',),
        groups=dict(type='list',),
        health_monitor_refs=dict(type='list',),
        health_monitor_scope=dict(type='str',),
        is_federated=dict(type='bool',),
        min_members=dict(type='int',),
        name=dict(type='str', required=True),
        num_dns_ip=dict(type='int',),
        pool_algorithm=dict(type='str',),
        site_persistence_enabled=dict(type='bool',),
        tenant_ref=dict(type='str',),
        ttl=dict(type='int',),
        url=dict(type='str',),
        use_edns_client_subnet=dict(type='bool',),
        uuid=dict(type='str',),
        wildcard_match=dict(type='bool',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs, supports_check_mode=True)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'gslbservice',
                           set([]))


if __name__ == '__main__':
    main()
