#!/usr/bin/python
#
# Created on Aug 25, 2016
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
#          Eric Anderson (eanderson@avinetworks.com)
# module_check: not supported
# Avi Version: 16.3.6
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

ANSIBLE_METADATA = {'status': ['preview'], 'supported_by': 'community', 'version': '1.0'}

DOCUMENTATION = '''
---
module: avi_healthmonitor
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Module for setup of HealthMonitor Avi RESTful Object
description:
    - This module is used to configure HealthMonitor object
    - more examples at U(https://github.com/avinetworks/devops)
requirements: [ avisdk ]
version_added: 2.3
options:
    state:
        description:
            - The state that should be applied on the entity.
        required: false
        default: present
        choices: ["absent","present"]
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
        default: 2
    http_monitor:
        description:
            - Healthmonitorhttp settings for healthmonitor.
    https_monitor:
        description:
            - Healthmonitorhttp settings for healthmonitor.
    monitor_port:
        description:
            - Use this port instead of the port defined for the server in the pool.
            - If the monitor succeeds to this port, the load balanced traffic will still be sent to the port of the server defined within the pool.
    name:
        description:
            - A user friendly name for this health monitor.
        required: true
    receive_timeout:
        description:
            - A valid response from the server is expected within the receive timeout window.
            - This timeout must be less than the send interval.
            - If server status is regularly flapping up and down, consider increasing this value.
        default: 4
    send_interval:
        description:
            - Frequency, in seconds, that monitors are sent to a server.
        default: 10
    successful_checks:
        description:
            - Number of continuous successful health checks before server is marked up.
        default: 2
    tcp_monitor:
        description:
            - Healthmonitortcp settings for healthmonitor.
    tenant_ref:
        description:
            - It is a reference to an object of type tenant.
    type:
        description:
            - Type of the health monitor.
        required: true
    udp_monitor:
        description:
            - Healthmonitorudp settings for healthmonitor.
    url:
        description:
            - Avi controller URL of the object.
        required: true
    uuid:
        description:
            - Uuid of the health monitor.
extends_documentation_fragment:
    - avi
'''


EXAMPLES = '''
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
'''
RETURN = '''
obj:
    description: HealthMonitor (api/healthmonitor) object
    returned: success, changed
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.avi import avi_common_argument_spec

HAS_AVI = True
try:
    from avi.sdk.utils.ansible_utils import avi_ansible_api
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
        name=dict(type='str',),
        receive_timeout=dict(type='int',),
        send_interval=dict(type='int',),
        successful_checks=dict(type='int',),
        tcp_monitor=dict(type='dict',),
        tenant_ref=dict(type='str',),
        type=dict(type='str',),
        udp_monitor=dict(type='dict',),
        url=dict(type='str',),
        uuid=dict(type='str',),
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(
        argument_spec=argument_specs)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    return avi_ansible_api(module, 'healthmonitor',
                           set([]))


if __name__ == '__main__':
    main()
