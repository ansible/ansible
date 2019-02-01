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
module: avi_healthmonitor
author: Gaurav Rastogi (@grastogi23) <grastogi@avinetworks.com>

short_description: Module for setup of HealthMonitor Avi RESTful Object
description:
    - This module is used to configure HealthMonitor object
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
    description:
        description:
            - User defined description for the object.
    dns_monitor:
        description:
            - Healthmonitordns settings for healthmonitor.
    external_monitor:
        description:
            - Healthmonitorexternal settings for healthmonitor.
    failed_checks:
        description:
            - Number of continuous failed health checks before the server is marked down.
            - Allowed values are 1-50.
            - Default value when not specified in API or module is interpreted by Avi Controller as 2.
    http_monitor:
        description:
            - Healthmonitorhttp settings for healthmonitor.
    https_monitor:
        description:
            - Healthmonitorhttp settings for healthmonitor.
    is_federated:
        description:
            - This field describes the object's replication scope.
            - If the field is set to false, then the object is visible within the controller-cluster and its associated service-engines.
            - If the field is set to true, then the object is replicated across the federation.
            - Field introduced in 17.1.3.
            - Default value when not specified in API or module is interpreted by Avi Controller as False.
        version_added: "2.4"
        type: bool
    monitor_port:
        description:
            - Use this port instead of the port defined for the server in the pool.
            - If the monitor succeeds to this port, the load balanced traffic will still be sent to the port of the server defined within the pool.
            - Allowed values are 1-65535.
            - Special values are 0 - 'use server port'.
    name:
        description:
            - A user friendly name for this health monitor.
        required: true
    receive_timeout:
        description:
            - A valid response from the server is expected within the receive timeout window.
            - This timeout must be less than the send interval.
            - If server status is regularly flapping up and down, consider increasing this value.
            - Allowed values are 1-2400.
            - Default value when not specified in API or module is interpreted by Avi Controller as 4.
            - Units(SEC).
    send_interval:
        description:
            - Frequency, in seconds, that monitors are sent to a server.
            - Allowed values are 1-3600.
            - Default value when not specified in API or module is interpreted by Avi Controller as 10.
            - Units(SEC).
    successful_checks:
        description:
            - Number of continuous successful health checks before server is marked up.
            - Allowed values are 1-50.
            - Default value when not specified in API or module is interpreted by Avi Controller as 2.
    tcp_monitor:
        description:
            - Healthmonitortcp settings for healthmonitor.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    type:
        description:
            - Type of the health monitor.
            - Enum options - HEALTH_MONITOR_PING, HEALTH_MONITOR_TCP, HEALTH_MONITOR_HTTP, HEALTH_MONITOR_HTTPS, HEALTH_MONITOR_EXTERNAL, HEALTH_MONITOR_UDP,
            - HEALTH_MONITOR_DNS, HEALTH_MONITOR_GSLB.
        required: true
    udp_monitor:
        description:
            - Healthmonitorudp settings for healthmonitor.
    url:
        description:
            - Avi controller URL of the object.
    uuid:
        description:
            - Uuid of the health monitor.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = """
- name: Create a HTTPS health monitor
  avi_healthmonitor:
    controller: 10.10.27.90
    username: admin
    password: AviNetworks123!
    https_monitor:
      http_request: HEAD / HTTP/1.0
      http_response_code:
        - HTTP_2XX
        - HTTP_3XX
    receive_timeout: 4
    failed_checks: 3
    send_interval: 10
    successful_checks: 3
    type: HEALTH_MONITOR_HTTPS
    name: MyWebsite-HTTPS
"""

RETURN = '''
obj:
    description: HealthMonitor (api/healthmonitor) object
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
        description=dict(type='str',),
        dns_monitor=dict(type='dict',),
        external_monitor=dict(type='dict',),
        failed_checks=dict(type='int',),
        http_monitor=dict(type='dict',),
        https_monitor=dict(type='dict',),
        is_federated=dict(type='bool',),
        monitor_port=dict(type='int',),
        name=dict(type='str', required=True),
        receive_timeout=dict(type='int',),
        send_interval=dict(type='int',),
        successful_checks=dict(type='int',),
        tcp_monitor=dict(type='dict',),
        tenant_ref=dict(type='str',),
        type=dict(type='str', required=True),
        udp_monitor=dict(type='dict',),
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
    return avi_ansible_api(module, 'healthmonitor',
                           set([]))


if __name__ == '__main__':
    main()
