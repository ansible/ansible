#!/usr/bin/python
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

DOCUMENTATION = '''
---
module: profitbricks_firewall_rule
short_description: Create or remove a firewall rule.
description:
     - This module allows you to create or remove a firewlal rule. This module has a dependency on profitbricks >= 1.0.0
version_added: "2.2"
options:
  datacenter:
    description:
      - The datacenter name or UUID in which to operate.
    required: true
  server:
    description:
      - The server name or UUID.
    required: true
  nic:
    description:
      - The NIC name or UUID.
    required: true
  name:
    description:
      - The name or UUID of the firewall rule.
    required: false
  protocol:
    description:
      - The protocol for the firewall rule.
    choices: [ "TCP", "UDP", "ICMP" ]
    required: true
  source_mac:
    description:
      - Only traffic originating from the respective MAC address is allowed. No value allows all source MAC addresses.
    required: false
  source_ip:
    description:
      - Only traffic originating from the respective IPv4 address is allowed. No value allows all source IPs.
    required: false
  target_ip:
    description:
      - In case the target NIC has multiple IP addresses, only traffic directed to the respective IP address of the NIC is allowed. No value allows all target IPs.
    required: false
  port_range_start:
    description:
      - Defines the start range of the allowed port (from 1 to 65534) if protocol TCP or UDP is chosen. Leave value empty to allow all ports.
    required: false
  port_range_end:
    description:
      - Defines the end range of the allowed port (from 1 to 65534) if the protocol TCP or UDP is chosen. Leave value empty to allow all ports.
    required: false
  icmp_type:
    description:
      - Defines the allowed type (from 0 to 254) if the protocol ICMP is chosen. No value allows all types.
    required: false
  icmp_code:
    description:
      - Defines the allowed code (from 0 to 254) if protocol ICMP is chosen. No value allows all codes.
    required: false
  subscription_user:
    description:
      - The ProfitBricks username. Overrides the PB_SUBSCRIPTION_ID environement variable.
    required: false
  subscription_password:
    description:
      - THe ProfitBricks password. Overrides the PB_PASSWORD environement variable.
    required: false
  wait:
    description:
      - wait for the operation to complete before returning
    required: false
    default: "yes"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 600
  state:
    description:
      - Indicate desired state of the resource
    required: false
    default: 'present'
    choices: ["present", "absent"]

requirements: [ "profitbricks" ]
author: Ethan Devenport (ethand@stackpointcloud.com)
'''

EXAMPLES = '''
# Create a firewall rule
- name: Create SSH firewall rule
  profitbricks_firewall_rule:
    datacenter: Virtual Datacenter
    server: node001
    nic: 7341c2454f
    name: Allow SSH
    protocol: TCP
    source_ip: 0.0.0.0
    port_range_start: 22
    port_range_end: 22
    state: present

- name: Create ping firewall rule
  profitbricks_firewall_rule:
    datacenter: Virtual Datacenter
    server: node001
    nic: 7341c2454f
    name: Allow Ping
    protocol: ICMP
    source_ip: 0.0.0.0
    icmp_type: 8
    icmp_code: 0
    state: present

# Remove a firewall rule
- name: Remove public ping firewall rule
  profitbricks_firewall_rule:
    datacenter: Virtual Datacenter
    server: node001
    nic: aa6c261b9c
    name: Allow Ping
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the firewall rule.
  returned: success
  type: string
  sample: be60aa97-d9c7-4c22-bebe-f5df7d6b675d
name:
  description: Name of the firwall rule.
  returned: success
  type: string
  sample: Allow SSH
protocol:
  description: Protocol of the firewall rule.
  returned: success
  type: string
  sample: TCP
source_mac:
  description: MAC address of the firewall rule.
  returned: success
  type: string
  sample: 02:01:97:d7:ed:49
source_ip:
  description: Source IP of the firewall rule.
  returned: success
  type: string
  sample: tcp
target_ip:
  description: Target IP of the firewal rule.
  returned: success
  type: string
  sample: 10.0.0.1
port_range_start:
  description: Start port of the firewall rule.
  returned: success
  type: int
  sample: 80
port_range_end:
  description: End port of the firewall rule.
  returned: success
  type: int
  sample: 80
icmp_type:
  description: ICMP type of the firewall rule.
  returned: success
  type: int
  sample: 8
icmp_code:
  description: ICMP code of the firewall rule.
  returned: success
  type: int
  sample: 0
'''

# import uuid
import time

HAS_PB_SDK = True

try:
    from profitbricks.client import ProfitBricksService, FirewallRule
except ImportError:
    HAS_PB_SDK = False


def _wait_for_completion(profitbricks, promise, wait_timeout, msg):
    if not promise: return
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time():
        time.sleep(5)
        operation_result = profitbricks.get_request(
            request_id=promise['requestId'],
            status=True)

        if operation_result['metadata']['status'] == 'DONE':
            return
        elif operation_result['metadata']['status'] == 'FAILED':
            raise Exception(
                'Request failed to complete ' + msg + ' "' + str(
                    promise['requestId']) + '" to complete.')

    raise Exception(
        'Timed out waiting for async operation ' + msg + ' "' + str(
            promise['requestId']
            ) + '" to complete.')


def create_firewall_rule(module, profitbricks):
    """
    Creates a firewall rule.

    module : AnsibleModule object
    profitbricks: authenticated profitbricks object.

    Returns:
        True if the firewal rule creates, false otherwise
    """
    datacenter = module.params.get('datacenter')
    server = module.params.get('server')
    nic = module.params.get('nic')
    name = module.params.get('name')
    protocol = module.params.get('protocol')
    source_mac = module.params.get('source_mac')
    source_ip = module.params.get('source_ip')
    target_ip = module.params.get('target_ip')
    port_range_start = module.params.get('port_range_start')
    port_range_end = module.params.get('port_range_end')
    icmp_type = module.params.get('icmp_type')
    icmp_code = module.params.get('icmp_code')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    # Locate UUID for virtual datacenter
    datacenter_list = profitbricks.list_datacenters()
    datacenter_id = _get_resource_id(datacenter_list, datacenter)
    if not datacenter_id:
        module.fail_json(msg='Virtual data center \'%s\' not found.' % str(datacenter))

    # Locate UUID for server
    server_list = profitbricks.list_servers(datacenter_id)
    server_id = _get_resource_id(server_list, server)

    # Locate UUID for NIC
    nic_list = profitbricks.list_nics(datacenter_id, server_id)
    nic_id = _get_resource_id(nic_list, nic)

    try:
        profitbricks.update_nic(datacenter_id, server_id, nic_id,
                                firewall_active=True)
    except Exception as e:
        module.fail_json(msg='Unable to activate the NIC firewall.' % str(e))

    f = FirewallRule(
        name=name,
        protocol=protocol,
        source_mac=source_mac,
        source_ip=source_ip,
        target_ip=target_ip,
        port_range_start=port_range_start,
        port_range_end=port_range_end,
        icmp_type=icmp_type,
        icmp_code=icmp_code
        )

    try:
        firewall_rule_response = profitbricks.create_firewall_rule(
            datacenter_id, server_id, nic_id, f
        )

        if wait:
            _wait_for_completion(profitbricks, firewall_rule_response,
                                 wait_timeout, "create_firewall_rule")
        return firewall_rule_response

    except Exception as e:
        module.fail_json(msg="failed to create the firewall rule: %s" % str(e))


def delete_firewall_rule(module, profitbricks):
    """
    Removes a firewall rule

    module : AnsibleModule object
    profitbricks: authenticated profitbricks object.

    Returns:
        True if the firewall rule was removed, false otherwise
    """
    datacenter = module.params.get('datacenter')
    server = module.params.get('server')
    nic = module.params.get('nic')
    name = module.params.get('name')

    # Locate UUID for virtual datacenter
    datacenter_list = profitbricks.list_datacenters()
    datacenter_id = _get_resource_id(datacenter_list, datacenter)

    # Locate UUID for server
    server_list = profitbricks.list_servers(datacenter_id)
    server_id = _get_resource_id(server_list, server)

    # Locate UUID for NIC
    nic_list = profitbricks.list_nics(datacenter_id, server_id)
    nic_id = _get_resource_id(nic_list, nic)

    # Locate UUID for firewall rule
    firewall_rule_list = profitbricks.get_firewall_rules(datacenter_id, server_id, nic_id)
    firewall_rule_id = _get_resource_id(firewall_rule_list, name)

    try:
        firewall_rule_response = profitbricks.delete_firewall_rule(
            datacenter_id, server_id, nic_id, firewall_rule_id
        )
        return firewall_rule_response
    except Exception as e:
        module.fail_json(msg="failed to remove the firewall rule: %s" % str(e))


def _get_resource_id(resource_list, identity):
    """
    Fetch and return the UUID of a resource regardless of whether the name or
    UUID is passed.
    """
    for resource in resource_list['items']:
        if identity in (resource['properties']['name'], resource['id']):
            return resource['id']
    return None


def main():
    module = AnsibleModule(
        argument_spec=dict(
            datacenter=dict(type='str', required=True),
            server=dict(type='str', required=True),
            nic=dict(type='str', required=True),
            name=dict(type='str', required=True),
            protocol=dict(type='str', required=False),
            source_mac=dict(type='str', default=None),
            source_ip=dict(type='str', default=None),
            target_ip=dict(type='str', default=None),
            port_range_start=dict(type='int', default=None),
            port_range_end=dict(type='int', default=None),
            icmp_type=dict(type='int', default=None),
            icmp_code=dict(type='int', default=None),
            subscription_user=dict(type='str', required=True),
            subscription_password=dict(type='str', required=True),
            wait=dict(type='bool', default=True),
            wait_timeout=dict(type='int', default=600),
            state=dict(default='present'),
        )
    )

    if not HAS_PB_SDK:
        module.fail_json(msg='profitbricks required for this module')

    subscription_user = module.params.get('subscription_user')
    subscription_password = module.params.get('subscription_password')

    profitbricks = ProfitBricksService(
        username=subscription_user,
        password=subscription_password)

    state = module.params.get('state')

    if state == 'absent':
        try:
            (changed) = delete_firewall_rule(module, profitbricks)
            module.exit_json(changed=changed)
        except Exception as e:
            module.fail_json(msg='failed to set firewall rule state: %s' % str(e))

    elif state == 'present':
        try:
            (firewall_rule_dict) = create_firewall_rule(module, profitbricks)
            module.exit_json(firewall_rules=firewall_rule_dict)
        except Exception as e:
            module.fail_json(msg='failed to set firewall rules state: %s' % str(e))

from ansible.module_utils.basic import *

main()
