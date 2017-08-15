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
module: avi_gslbservice
author: Gaurav Rastogi (grastogi@avinetworks.com)

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
        choices: ["absent","present"]
    controller_health_status_enabled:
        description:
            - Gs member's overall health status is derived based on a combination of controller and datapath health-status inputs.
            - Note that the datapath status is determined by the association of health monitor profiles.
            - Only the controller provided status is determined through this configuration.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
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
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    ttl:
        description:
            - Ttl value (in seconds) for records served for this gslb service by the dns service.
            - Allowed values are 1-86400.
    url:
        description:
            - Avi controller URL of the object.
    use_edns_client_subnet:
        description:
            - Use the client ip subnet from the edns option as source ipaddress for client geo-location and consistent hash algorithm.
            - Default is true.
            - Field introduced in 17.1.1.
            - Default value when not specified in API or module is interpreted by Avi Controller as True.
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
    from ansible.module_utils.avi import (
        avi_common_argument_spec, HAS_AVI, avi_ansible_api)
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        state=dict(default='present',
                   choices=['absent', 'present']),
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
        name=dict(type='str', required=True),
        num_dns_ip=dict(type='int',),
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
