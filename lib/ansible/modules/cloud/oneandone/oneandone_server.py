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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: oneandone_server
short_description: Create, destroy, start, stop, and reboot a 1&1 Host machine.
description:
     - Create, destroy, update, start, stop, and reboot a 1&1 Host machine.
       When the machine is created it can optionally wait for it to be 'running' before returning.
version_added: "2.4"
options:
  state:
    description:
      - Define a machine's state to create, remove, start or stop it.
    required: false
    default: present
    choices: [ "present", "absent", "running", "stopped" ]
  auth_token:
    description:
      - Authenticating API token provided by 1&1. Overrides the
        ONEANDONE_AUTH_TOKEN environement variable.
    required: true
  datacenter:
    description:
      - The datacenter location.
    required: false
    default: US
    choices: [ "US", "ES", "DE", "GB" ]
  hostname:
    description:
      - The hostname or ID of the machine. Only used when state is 'present'.
    required: true
  description:
    description:
      - The description of the machine.
    required: false
  appliance:
    description:
      - The operating system name or ID for the machine.
        It is required only for 'present' state.
    required: true
  fixed_instance_size:
    description:
      - The instance size name or ID of the machine.
        It is required only for 'present' state, and it is mutually exclusive with
        vcore, cores_per_processor, ram, and hdds parameters.
    required: true
    choices: [ "S", "M", "L", "XL", "XXL", "3XL", "4XL", "5XL" ]
  vcore:
    description:
      - The total number of processors.
        It must be provided with cores_per_processor, ram, and hdds parameters.
    required: true
  cores_per_processor:
    description:
      - The number of cores per processor.
        It must be provided with vcore, ram, and hdds parameters.
    required: true
  ram:
    description:
      - The amount of RAM memory.
        It must be provided with with vcore, cores_per_processor, and hdds parameters.
    required: true
  hdds:
    description:
      - A list of hard disks with nested "size" and "is_main" properties.
        It must be provided with vcore, cores_per_processor, and ram parameters.
    required: true
  private_network:
    description:
      - The private network name or ID.
    required: false
  firewall_policy:
    description:
      - The firewall policy name or ID.
    required: false
  load_balancer:
    description:
      - The load balancer name or ID.
    required: false
  monitoring_policy:
    description:
      - The monitoring policy name or ID.
    required: false
  instance_ids:
    description:
      - List of machine IDs or hostnames. It is required for all states except 'running'.
    required: true
  count:
    description:
      - The number of machines to create.
    required: false
    default: 1
  ssh_key:
    description:
      - User's public SSH key (contents, not path).
    required: false
    default: None
  wait:
    description:
      - Wait for the instance to be in state 'running' before returning.
        Also used for delete operation (set to 'false' if you don't want to wait
        for each individual server to be deleted before moving on with
        other tasks.)
    required: false
    default: "yes"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 600
  auto_increment:
    description:
      - When creating multiple machines at once, whether to differentiate
        hostnames by appending a count after them or substituting the count
        where there is a %02d or %03d in the hostname string.
    default: "yes"
    choices: [ "yes", "no" ]

requirements:
  - "1and1"
  - "python >= 2.6"
author: "Amel Ajdinovic (@aajdinov), Ethan Devenport (@edevenport)"
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

# Create three machines, passing in an ssh_key.

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
    ssh_key: SSH_PUBLIC_KEY

# Removing machines

- oneandone_server:
    auth_token: oneandone_private_api_key
    state: absent
    instance_ids:
      - 'node01'
      - 'node02'
      - 'node03'

# Starting Machines.

- oneandone_server:
    auth_token: oneandone_private_api_key
    state: running
    instance_ids:
      - 'node01'
      - 'node02'
      - 'node03'

# Stopping Machines

- oneandone_server:
    auth_token: oneandone_private_api_key
    state: stopped
    instance_ids:
      - 'node01'
      - 'node02'
      - 'node03'
'''

RETURN = '''
changed:
    description: True if a machine created, modified or removed
    type: bool
    sample: True
    returned: always
machines:
    description: Information about each machine that was processed
    type: list
    sample: '[{"hostname": "my-server", "id": "server-id"}]'
    returned: always
'''

import os
import time
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

ONEANDONE_MACHINE_STATES = (
    'DEPLOYING',
    'POWERED_OFF',
    'POWERED_ON',
    'POWERING_ON',
    'POWERING_OFF',
)


def _create_machine(module, oneandone_conn, hostname, description,
                    fixed_instance_size_id, vcore, cores_per_processor, ram,
                    hdds, datacenter_id, appliance_id, ssh_key,
                    private_network_id, firewall_policy_id, load_balancer_id,
                    monitoring_policy_id, wait, wait_timeout):

    try:
        machine = oneandone_conn.create_server(
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
                monitoring_policy_id=monitoring_policy_id,), hdds)

        if wait:
            wait_for_resource_creation_completion(
                oneandone_conn,
                OneAndOneResources.server,
                machine['id'],
                wait_timeout)
            machine = oneandone_conn.get_server(machine['id'])  # refresh

        return machine
    except Exception as ex:
        module.fail_json(msg=str(ex))


def _insert_network_data(machine):
    for addr_data in machine['ips']:
        if addr_data['type'] == 'IPV6':
            machine['public_ipv6'] = addr_data['ip']
        elif addr_data['type'] == 'IPV4':
            machine['public_ipv4'] = addr_data['ip']
    return machine


def create_machine(module, oneandone_conn):
    """
    Create new machine

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object

    Returns a dictionary containing a 'changed' attribute indicating whether
    any machine was added, and a 'machines' attribute with the list of the
    created machines's hostname, id and ip addresses.
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
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    datacenter_id = get_datacenter(oneandone_conn, datacenter)
    if datacenter_id is None:
        module.fail_json(
            msg='datacenter %s not found.' % datacenter)

    fixed_instance_size_id = None
    if fixed_instance_size:
        fixed_instance_size_id = get_fixed_instance_size(
            oneandone_conn,
            fixed_instance_size)
        if fixed_instance_size_id is None:
            module.fail_json(
                msg='fixed_instance_size %s not found.' % fixed_instance_size)

    appliance_id = get_appliance(oneandone_conn, appliance)
    if appliance_id is None:
        module.fail_json(
            msg='datacenter %s not found.' % appliance)

    private_network_id = None
    if private_network:
        private_network_id = get_private_network(
            oneandone_conn,
            private_network)
        if private_network_id is None:
            module.fail_json(
                msg='private network %s not found.' % private_network)

    monitoring_policy_id = None
    if monitoring_policy:
        monitoring_policy_id = get_monitoring_policy(
            oneandone_conn,
            monitoring_policy)
        if monitoring_policy_id is None:
            module.fail_json(
                msg='monitoring policy %s not found.' % monitoring_policy)

    firewall_policy_id = None
    if firewall_policy:
        firewall_policy_id = get_firewall_policy(
            oneandone_conn,
            firewall_policy)
        if firewall_policy_id is None:
            module.fail_json(
                msg='firewall policy %s not found.' % firewall_policy)

    load_balancer_id = None
    if load_balancer:
        load_balancer_id = get_load_balancer(
            oneandone_conn,
            load_balancer)
        if load_balancer_id is None:
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

    machines = []
    for index, name in enumerate(hostnames):
        machines.append(
            _create_machine(
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
                wait=wait,
                wait_timeout=wait_timeout))

    changed = True if machines else False
    machines = [_insert_network_data(machine) for machine in machines]

    return (changed, machines)


def remove_machine(module, oneandone_conn):
    """
    Remove machines.

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object.

    Returns a dictionary containing a 'changed' attribute indicating whether
    any machines were removed, and a 'machines' attribute with the list of the
    removed machines's hostname and id.
    """
    instance_ids = module.params.get('instance_ids')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    if not isinstance(instance_ids, list) or len(instance_ids) < 1:
        module.fail_json(
            msg='instance_ids should be a list of machine ids or names.')

    removed_machines = []
    for instance in instance_ids:
        machine = get_server(oneandone_conn, instance, True)
        if machine is None:
            continue

        try:
            oneandone_conn.delete_server(server_id=machine['id'])
            if wait:
                wait_for_resource_deletion_completion(oneandone_conn, OneAndOneResources.server, machine['id'], wait_timeout)
            removed_machines.append(machine)
        except Exception as ex:
            module.fail_json(
                msg="failed to terminate the machine: %s" % str(ex))

    changed = True if removed_machines else False
    machines = [{
        'id': removed_machine['id'],
        'hostname': removed_machine['name'],
    } for removed_machine in removed_machines]

    return (changed, machines)


def startstop_machine(module, oneandone_conn):
    """
    Starts or Stops a machine.

    module : AnsibleModule object
    oneandone_conn: authenticated oneandone object.

    Returns a dictionary with a 'changed' attribute indicating whether
    anything has changed for any of the machines as a result of this function
    being run, and a 'machines' attribute with basic information for
    each machine.
    """
    state = module.params.get('state')
    instance_ids = module.params.get('instance_ids')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    if not isinstance(instance_ids, list) or len(instance_ids) < 1:
        module.fail_json(msg='instance_ids should be a list of virtual machine ids or names.')

    machines = []
    changed = False
    for instance_id in instance_ids:

        # Resolve machine
        machine = get_server(oneandone_conn, instance_id, True)
        if machine is None:
            continue

        # Attempt to change the machine state, only if it's not already there
        # or on its way.
        try:
            if state == 'stopped':
                if machine['status']['state'] == 'POWERED_OFF':
                    machines.append(machine)
                    continue
                oneandone_conn.modify_server_status(
                    server_id=machine['id'],
                    action='POWER_OFF',
                    method='SOFTWARE')
            elif state == 'running':
                if machine['status']['state'] == 'POWERED_ON':
                    machines.append(machine)
                    continue
                oneandone_conn.modify_server_status(
                    server_id=machine['id'],
                    action='POWER_ON',
                    method='SOFTWARE')
        except Exception as ex:
            module.fail_json(
                msg="failed to set machine %s to state %s: %s" % (
                    instance_id, state, str(ex)))

        # Make sure the machine has reached the desired state
        if wait:
            operation_completed = False
            wait_timeout = time.time() + wait_timeout
            while wait_timeout > time.time():
                time.sleep(5)
                machine = oneandone_conn.get_server(machine['id'])  # refresh
                machine_state = machine['status']['state']
                if state == 'stopped' and machine_state == 'POWERED_OFF':
                    operation_completed = True
                    break
                if state == 'running' and machine_state == 'POWERED_ON':
                    operation_completed = True
                    break
            if not operation_completed:
                module.fail_json(
                    msg="Timeout waiting for machine %s to get to state %s" % (
                        instance_id, state))

        changed = True
        machines.append(machine)

    machines = [_insert_network_data(_machine) for _machine in machines]

    return (changed, machines)


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
            hostname=dict(type='str'),
            description=dict(type='str'),
            appliance=dict(type='str'),
            fixed_instance_size=dict(type='str'),
            vcore=dict(type='int'),
            cores_per_processor=dict(type='int'),
            ram=dict(type='float'),
            hdds=dict(type='list'),
            count=dict(type='int', default=1),
            ssh_key=dict(type='raw', default=None),
            auto_increment=dict(type='bool', default=True),
            instance_ids=dict(type='list'),
            datacenter=dict(
                choices=DATACENTERS,
                default='US'),
            private_network=dict(type='str'),
            firewall_policy=dict(type='str'),
            load_balancer=dict(type='str'),
            monitoring_policy=dict(type='str'),
            wait=dict(type='bool', default=True),
            wait_timeout=dict(type='int', default=600),
            state=dict(type='str', default='present'),
        ),
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

    oneandone_conn = oneandone.client.OneAndOneService(
        api_token=module.params.get('auth_token'))

    state = module.params.get('state')

    if state == 'absent':
        try:
            (changed, machines) = remove_machine(module, oneandone_conn)
        except Exception as ex:
            module.fail_json(msg=str(ex))

    elif state in ('running', 'stopped'):
        try:
            (changed, machines) = startstop_machine(module, oneandone_conn)
        except Exception as ex:
            module.fail_json(msg=str(ex))

    elif state == 'present':
        for param in ('hostname',
                      'appliance',
                      'datacenter'):
            if not module.params.get(param):
                module.fail_json(
                    msg="%s parameter is required for new instance." % param)
        try:
            (changed, machines) = create_machine(module, oneandone_conn)
        except Exception as ex:
            module.fail_json(msg=str(ex))

    module.exit_json(changed=changed, machines=machines)


if __name__ == '__main__':
    main()
