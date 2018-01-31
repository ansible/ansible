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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: avi_gslbhealthmonitor
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of GslbHealthMonitor Avi RESTful Object
description:
    - This module is used to configure GslbHealthMonitor object
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
    dns_monitor:
        description:
            - Healthmonitordns settings for gslbhealthmonitor.
    external_monitor:
        description:
            - Healthmonitorexternal settings for gslbhealthmonitor.
    failed_checks:
        description:
            - Number of continuous failed health checks before the server is marked down.
            - Allowed values are 1-50.
            - Default value when not specified in API or module is interpreted by Avi Controller as 2.
    http_monitor:
        description:
            - Healthmonitorhttp settings for gslbhealthmonitor.
    https_monitor:
        description:
            - Healthmonitorhttp settings for gslbhealthmonitor.
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
            - Allowed values are 1-300.
            - Default value when not specified in API or module is interpreted by Avi Controller as 4.
    send_interval:
        description:
            - Frequency, in seconds, that monitors are sent to a server.
            - Allowed values are 1-3600.
            - Default value when not specified in API or module is interpreted by Avi Controller as 5.
    successful_checks:
        description:
            - Number of continuous successful health checks before server is marked up.
            - Allowed values are 1-50.
            - Default value when not specified in API or module is interpreted by Avi Controller as 2.
    tcp_monitor:
        description:
            - Healthmonitortcp settings for gslbhealthmonitor.
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
            - Healthmonitorudp settings for gslbhealthmonitor.
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
- name: Example to create GslbHealthMonitor object
  avi_gslbhealthmonitor:
    controller: 10.10.25.42
    username: admin
    password: something
    state: present
    name: sample_gslbhealthmonitor
"""

RETURN = '''
obj:
    description: GslbHealthMonitor (api/gslbhealthmonitor) object
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
        description=dict(type='str',),
        dns_monitor=dict(type='dict',),
        external_monitor=dict(type='dict',),
        failed_checks=dict(type='int',),
        http_monitor=dict(type='dict',),
        https_monitor=dict(type='dict',),
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
    return avi_ansible_api(module, 'gslbhealthmonitor',
                           set([]))

if __name__ == '__main__':
    main()
