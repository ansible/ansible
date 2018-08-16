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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: oneandone_server
short_description: Create, destroy, start, stop, and reboot a 1&1 Host server.
description:
     - Create, destroy, update, start, stop, and reboot a 1&1 Host server.
       When the server is created it can optionally wait for it to be 'running' before returning.
version_added: "2.5"
options:
  state:
    description:
      - Define a server's state to create, remove, start or stop it.
    default: present
    choices: [ "present", "absent", "running", "stopped" ]
  auth_token:
    description:
      - Authenticating API token provided by 1&1. Overrides the
        ONEANDONE_AUTH_TOKEN environement variable.
    required: true
  api_url:
    description:
      - Custom API URL. Overrides the
        ONEANDONE_API_URL environement variable.
  datacenter:
    description:
      - The datacenter location.
    default: US
    choices: [ "US", "ES", "DE", "GB" ]
  hostname:
    description:
      - The hostname or ID of the server. Only used when state is 'present'.
  description:
    description:
      - The description of the server.
  appliance:
    description:
      - The operating system name or ID for the server.
        It is required only for 'present' state.
  fixed_instance_size:
    description:
      - The instance size name or ID of the server.
        It is required only for 'present' state, and it is mutually exclusive with
        vcore, cores_per_processor, ram, and hdds parameters.
    required: true
    choices: [ "S", "M", "L", "XL", "XXL", "3XL", "4XL", "5XL" ]
  vcore:
    description:
      - The total number of processors.
        It must be provided with cores_per_processor, ram, and hdds parameters.
  cores_per_processor:
    description:
      - The number of cores per processor.
        It must be provided with vcore, ram, and hdds parameters.
  ram:
    description:
      - The amount of RAM memory.
        It must be provided with with vcore, cores_per_processor, and hdds parameters.
  hdds:
    description:
      - A list of hard disks with nested "size" and "is_main" properties.
        It must be provided with vcore, cores_per_processor, and ram parameters.
  private_network:
    description:
      - The private network name or ID.
  firewall_policy:
    description:
      - The firewall policy name or ID.
  load_balancer:
    description:
      - The load balancer name or ID.
  monitoring_policy:
    description:
      - The monitoring policy name or ID.
  server:
    description:
      - Server identifier (ID or hostname). It is required for all states except 'running' and 'present'.
  count:
    description:
      - The number of servers to create.
    default: 1
  ssh_key:
    description:
      - User's public SSH key (contents, not path).
  server_type:
    description:
      - The type of server to be built.
    default: "cloud"
    choices: [ "cloud", "baremetal", "k8s_node" ]
  wait:
    description:
      - Wait for the server to be in state 'running' before returning.
        Also used for delete operation (set to 'false' if you don't want to wait
        for each individual server to be deleted before moving on with
        other tasks.)
    type: bool
    default: 'yes'
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 600
  wait_interval:
    description:
      - Defines the number of seconds to wait when using the wait_for methods
    default: 5
  auto_increment:
    description:
      - When creating multiple servers at once, whether to differentiate
        hostnames by appending a count after them or substituting the count
        where there is a %02d or %03d in the hostname string.
    type: bool
    default: 'yes'

requirements:
  - "1and1"
  - "python >= 2.6"

author:
  -  "Amel Ajdinovic (@aajdinov)"
  -  "Ethan Devenport (@edevenport)"

'''

EXAMPLES = '''

# Provisioning example. Creates three servers and enumerate their names.

- oneandone_server:
    auth_token: oneandone_private_api_key
    hostname: node%02d
    fixed_instance_size: XL
    datacenter: US
    appliance: C5A349786169F140BCBC335675014C08
    auto_increment: true
    count: 3

# Create three servers, passing in an ssh_key.

- oneandone_server:
    auth_token: oneandone_private_api_key
    hostname: node%02d
    vcore: 2
    cores_per_processor: 4
    ram: 8.0
    hdds:
      - size: 50
        is_main: false
    datacenter: ES
    appliance: C5A349786169F140BCBC335675014C08
    count: 3
    wait: yes
    wait_timeout: 600
    wait_interval: 10
    ssh_key: SSH_PUBLIC_KEY

# Removing server

- oneandone_server:
    auth_token: oneandone_private_api_key
    state: absent
    server: 'node01'

# Starting server.

- oneandone_server:
    auth_token: oneandone_private_api_key
    state: running
    server: 'node01'

# Stopping server

- oneandone_server:
    auth_token: oneandone_private_api_key
    state: stopped
    server: 'node01'
'''

RETURN = '''
servers:
    description: Information about each server that was processed
    type: list
    sample: '[{"hostname": "my-server", "id": "server-id"}]'
    returned: always
'''

import os
import time
from ansible.module_utils.six.moves import xrange
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.oneandone import (
    get_datacenter,
    get_fixed_instance_size,
    get_appliance,
    get_private_network,
    get_monitoring_policy,
    get_firewall_policy,
    get_load_balancer,
    get_server,
    OneAndOneResources,
    wait_for_resource_creation_completion,
    wait_for_resource_deletion_completion
)

HAS_ONEANDONE_SDK = True

try:
    import oneandone.client
except ImportError:
    HAS_ONEANDONE_SDK = False

DATACENTERS = ['US', 'ES', 'DE', 'GB']

ONEANDONE_SERVER_STATES = (
    'DEPLOYING',
    'POWERED_OFF',
    'POWERED_ON',
    'POWERING_ON',
    'POWERING_OFF',
)


def _check_mode(module, result):
    if module.check_mode:
        module.exit_json(
            changed=result
        )


def _create_server(module, oneandone_conn, hostname, description,
                   fixed_instance_size_id, vcore, cores_per_processor, ram,
                   hdds, datacenter_id, appliance_id, ssh_key,
                   private_network_id, firewall_policy_id, load_balancer_id,
                   monitoring_policy_id, server_type, wait, wait_timeout,
                   wait_interval):

    try:
        existing_server = get_server(oneandone_conn, hostname)

        if existing_server:
            if module.check_mode:
                return False
            return None

        if module.check_mode:
            return True

        server = oneandone_conn.create_server(
            oneandone.client.Server(
                name=hostname,
                description=description,
                fixed_instance_size_id=fixed_instance_size_id,
                vcore=vcore,
                cores_per_processor=cores_per_processor,
                ram=ram,
                appliance_id=appliance_id,
                datacenter_id=datacenter_id,
                rsa_key=ssh_key,
                private_network_id=private_network_id,
                firewall_policy_id=firewall_policy_id,
                load_balancer_id=load_balancer_id,
                monitoring_policy_id=monitoring_policy_id,
                server_type=server_type,), hdds)

        if wait:
            wait_for_resource_creation_completion(
                oneandone_conn,
                OneAndOneResources.server,
                server['id'],
                wait_timeout,
                wait_interval)
            server = oneandone_conn.get_server(server['id'])  # refresh

        return server
    except Exception as ex:
        module.fail_json(msg=str(ex))


def _insert_network_data(server):
    for addr_data in server['ips']:
        if addr_data['type'] == 'IPV6':
            server['public_ipv6'] = addr_data['ip']
        elif addr_data['type'] == 'IPV4':
            server['public_ipv4'] = addr_data['ip']
    return server


def create_server(module, oneandone_conn):
    """
    Create new server

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object

    Returns a dictionary containing a 'changed' attribute indicating whether
    any server was added, and a 'servers' attribute with the list of the
    created servers' hostname, id and ip addresses.
    """
    hostname = module.params.get('hostname')
    description = module.params.get('description')
    auto_increment = module.params.get('auto_increment')
    count = module.params.get('count')
    fixed_instance_size = module.params.get('fixed_instance_size')
    vcore = module.params.get('vcore')
    cores_per_processor = module.params.get('cores_per_processor')
    ram = module.params.get('ram')
    hdds = module.params.get('hdds')
    datacenter = module.params.get('datacenter')
    appliance = module.params.get('appliance')
    ssh_key = module.params.get('ssh_key')
    private_network = module.params.get('private_network')
    monitoring_policy = module.params.get('monitoring_policy')
    firewall_policy = module.params.get('firewall_policy')
    load_balancer = module.params.get('load_balancer')
    server_type = module.params.get('server_type')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')
    wait_interval = module.params.get('wait_interval')

    datacenter_id = get_datacenter(oneandone_conn, datacenter)
    if datacenter_id is None:
        _check_mode(module, False)
        module.fail_json(
            msg='datacenter %s not found.' % datacenter)

    fixed_instance_size_id = None
    if fixed_instance_size:
        fixed_instance_size_id = get_fixed_instance_size(
            oneandone_conn,
            fixed_instance_size)
        if fixed_instance_size_id is None:
            _check_mode(module, False)
            module.fail_json(
                msg='fixed_instance_size %s not found.' % fixed_instance_size)

    appliance_id = get_appliance(oneandone_conn, appliance)
    if appliance_id is None:
        _check_mode(module, False)
        module.fail_json(
            msg='appliance %s not found.' % appliance)

    private_network_id = None
    if private_network:
        private_network_id = get_private_network(
            oneandone_conn,
            private_network)
        if private_network_id is None:
            _check_mode(module, False)
            module.fail_json(
                msg='private network %s not found.' % private_network)

    monitoring_policy_id = None
    if monitoring_policy:
        monitoring_policy_id = get_monitoring_policy(
            oneandone_conn,
            monitoring_policy)
        if monitoring_policy_id is None:
            _check_mode(module, False)
            module.fail_json(
                msg='monitoring policy %s not found.' % monitoring_policy)

    firewall_policy_id = None
    if firewall_policy:
        firewall_policy_id = get_firewall_policy(
            oneandone_conn,
            firewall_policy)
        if firewall_policy_id is None:
            _check_mode(module, False)
            module.fail_json(
                msg='firewall policy %s not found.' % firewall_policy)

    load_balancer_id = None
    if load_balancer:
        load_balancer_id = get_load_balancer(
            oneandone_conn,
            load_balancer)
        if load_balancer_id is None:
            _check_mode(module, False)
            module.fail_json(
                msg='load balancer %s not found.' % load_balancer)

    if auto_increment:
        hostnames = _auto_increment_hostname(count, hostname)
        descriptions = _auto_increment_description(count, description)
    else:
        hostnames = [hostname] * count
        descriptions = [description] * count

    hdd_objs = []
    if hdds:
        for hdd in hdds:
            hdd_objs.append(oneandone.client.Hdd(
                size=hdd['size'],
                is_main=hdd['is_main']
            ))

    servers = []
    for index, name in enumerate(hostnames):
        server = _create_server(
            module=module,
            oneandone_conn=oneandone_conn,
            hostname=name,
            description=descriptions[index],
            fixed_instance_size_id=fixed_instance_size_id,
            vcore=vcore,
            cores_per_processor=cores_per_processor,
            ram=ram,
            hdds=hdd_objs,
            datacenter_id=datacenter_id,
            appliance_id=appliance_id,
            ssh_key=ssh_key,
            private_network_id=private_network_id,
            monitoring_policy_id=monitoring_policy_id,
            firewall_policy_id=firewall_policy_id,
            load_balancer_id=load_balancer_id,
            server_type=server_type,
            wait=wait,
            wait_timeout=wait_timeout,
            wait_interval=wait_interval)
        if server:
            servers.append(server)

    changed = False

    if servers:
        for server in servers:
            if server:
                _check_mode(module, True)
        _check_mode(module, False)
        servers = [_insert_network_data(_server) for _server in servers]
        changed = True

    _check_mode(module, False)

    return (changed, servers)


def remove_server(module, oneandone_conn):
    """
    Removes a server.

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object.

    Returns a dictionary containing a 'changed' attribute indicating whether
    the server was removed, and a 'removed_server' attribute with
    the removed server's hostname and id.
    """
    server_id = module.params.get('server')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')
    wait_interval = module.params.get('wait_interval')

    changed = False
    removed_server = None

    server = get_server(oneandone_conn, server_id, True)
    if server:
        _check_mode(module, True)
        try:
            oneandone_conn.delete_server(server_id=server['id'])
            if wait:
                wait_for_resource_deletion_completion(oneandone_conn,
                                                      OneAndOneResources.server,
                                                      server['id'],
                                                      wait_timeout,
                                                      wait_interval)
            changed = True
        except Exception as ex:
            module.fail_json(
                msg="failed to terminate the server: %s" % str(ex))

        removed_server = {
            'id': server['id'],
            'hostname': server['name']
        }
    _check_mode(module, False)

    return (changed, removed_server)


def startstop_server(module, oneandone_conn):
    """
    Starts or Stops a server.

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object.

    Returns a dictionary with a 'changed' attribute indicating whether
    anything has changed for the server as a result of this function
    being run, and a 'server' attribute with basic information for
    the server.
    """
    state = module.params.get('state')
    server_id = module.params.get('server')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')
    wait_interval = module.params.get('wait_interval')

    changed = False

    # Resolve server
    server = get_server(oneandone_conn, server_id, True)
    if server:
        # Attempt to change the server state, only if it's not already there
        # or on its way.
        try:
            if state == 'stopped' and server['status']['state'] == 'POWERED_ON':
                _check_mode(module, True)
                oneandone_conn.modify_server_status(
                    server_id=server['id'],
                    action='POWER_OFF',
                    method='SOFTWARE')
            elif state == 'running' and server['status']['state'] == 'POWERED_OFF':
                _check_mode(module, True)
                oneandone_conn.modify_server_status(
                    server_id=server['id'],
                    action='POWER_ON',
                    method='SOFTWARE')
        except Exception as ex:
            module.fail_json(
                msg="failed to set server %s to state %s: %s" % (
                    server_id, state, str(ex)))

        _check_mode(module, False)

        # Make sure the server has reached the desired state
        if wait:
            operation_completed = False
            wait_timeout = time.time() + wait_timeout
            while wait_timeout > time.time():
                time.sleep(wait_interval)
                server = oneandone_conn.get_server(server['id'])  # refresh
                server_state = server['status']['state']
                if state == 'stopped' and server_state == 'POWERED_OFF':
                    operation_completed = True
                    break
                if state == 'running' and server_state == 'POWERED_ON':
                    operation_completed = True
                    break
            if not operation_completed:
                module.fail_json(
                    msg="Timeout waiting for server %s to get to state %s" % (
                        server_id, state))

        changed = True
        server = _insert_network_data(server)

    _check_mode(module, False)

    return (changed, server)


def _auto_increment_hostname(count, hostname):
    """
    Allow a custom incremental count in the hostname when defined with the
    string formatting (%) operator. Otherwise, increment using name-01,
    name-02, name-03, and so forth.
    """
    if '%' not in hostname:
        hostname = "%s-%%01d" % hostname

    return [
        hostname % i
        for i in xrange(1, count + 1)
    ]


def _auto_increment_description(count, description):
    """
    Allow the incremental count in the description when defined with the
    string formatting (%) operator. Otherwise, repeat the same description.
    """
    if '%' in description:
        return [
            description % i
            for i in xrange(1, count + 1)
        ]
    else:
        return [description] * count


def main():
    module = AnsibleModule(
        argument_spec=dict(
            auth_token=dict(
                type='str',
                default=os.environ.get('ONEANDONE_AUTH_TOKEN'),
                no_log=True),
            api_url=dict(
                type='str',
                default=os.environ.get('ONEANDONE_API_URL')),
            hostname=dict(type='str'),
            description=dict(type='str'),
            appliance=dict(type='str'),
            fixed_instance_size=dict(type='str'),
            vcore=dict(type='int'),
            cores_per_processor=dict(type='int'),
            ram=dict(type='float'),
            hdds=dict(type='list'),
            count=dict(type='int', default=1),
            ssh_key=dict(type='raw'),
            auto_increment=dict(type='bool', default=True),
            server=dict(type='str'),
            datacenter=dict(
                choices=DATACENTERS,
                default='US'),
            private_network=dict(type='str'),
            firewall_policy=dict(type='str'),
            load_balancer=dict(type='str'),
            monitoring_policy=dict(type='str'),
            server_type=dict(type='str', default='cloud', choices=['cloud', 'baremetal', 'k8s_node']),
            wait=dict(type='bool', default=True),
            wait_timeout=dict(type='int', default=600),
            wait_interval=dict(type='int', default=5),
            state=dict(type='str', default='present', choices=['present', 'absent', 'running', 'stopped']),
        ),
        supports_check_mode=True,
        mutually_exclusive=(['fixed_instance_size', 'vcore'], ['fixed_instance_size', 'cores_per_processor'],
                            ['fixed_instance_size', 'ram'], ['fixed_instance_size', 'hdds'],),
        required_together=(['vcore', 'cores_per_processor', 'ram', 'hdds'],)
    )

    if not HAS_ONEANDONE_SDK:
        module.fail_json(msg='1and1 required for this module')

    if not module.params.get('auth_token'):
        module.fail_json(
            msg='The "auth_token" parameter or ' +
            'ONEANDONE_AUTH_TOKEN environment variable is required.')

    if not module.params.get('api_url'):
        oneandone_conn = oneandone.client.OneAndOneService(
            api_token=module.params.get('auth_token'))
    else:
        oneandone_conn = oneandone.client.OneAndOneService(
            api_token=module.params.get('auth_token'), api_url=module.params.get('api_url'))

    state = module.params.get('state')

    if state == 'absent':
        if not module.params.get('server'):
            module.fail_json(
                msg="'server' parameter is required for deleting a server.")
        try:
            (changed, servers) = remove_server(module, oneandone_conn)
        except Exception as ex:
            module.fail_json(msg=str(ex))

    elif state in ('running', 'stopped'):
        if not module.params.get('server'):
            module.fail_json(
                msg="'server' parameter is required for starting/stopping a server.")
        try:
            (changed, servers) = startstop_server(module, oneandone_conn)
        except Exception as ex:
            module.fail_json(msg=str(ex))

    elif state == 'present':
        for param in ('hostname',
                      'appliance',
                      'datacenter'):
            if not module.params.get(param):
                module.fail_json(
                    msg="%s parameter is required for new server." % param)
        try:
            (changed, servers) = create_server(module, oneandone_conn)
        except Exception as ex:
            module.fail_json(msg=str(ex))

    module.exit_json(changed=changed, servers=servers)


if __name__ == '__main__':
    main()
