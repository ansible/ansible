#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_eni
short_description: Create and optionally attach an Elastic Network Interface (ENI) to an instance
description:
    - Create and optionally attach an Elastic Network Interface (ENI) to an instance. If an ENI ID or private_ip is
      provided, the existing ENI (if any) will be modified. The 'attached' parameter controls the attachment status
      of the network interface.
version_added: "2.0"
author: "Rob White (@wimnat)"
options:
  eni_id:
    description:
      - The ID of the ENI (to modify); if null and state is present, a new eni will be created.
  instance_id:
    description:
      - Instance ID that you wish to attach ENI to. Since version 2.2, use the 'attached' parameter to attach or
        detach an ENI. Prior to 2.2, to detach an ENI from an instance, use 'None'.
  private_ip_address:
    description:
      - Private IP address.
  subnet_id:
    description:
      - ID of subnet in which to create the ENI.
  description:
    description:
      - Optional description of the ENI.
  security_groups:
    description:
      - List of security groups associated with the interface. Only used when state=present. Since version 2.2, you
        can specify security groups by ID or by name or a combination of both. Prior to 2.2, you can specify only by ID.
  state:
    description:
      - Create or delete ENI
    default: present
    choices: [ 'present', 'absent' ]
  device_index:
    description:
      - The index of the device for the network interface attachment on the instance.
    default: 0
  attached:
    description:
      - Specifies if network interface should be attached or detached from instance. If ommited, attachment status
        won't change
    default: 'yes'
    version_added: 2.2
    type: bool
  force_detach:
    description:
      - Force detachment of the interface. This applies either when explicitly detaching the interface by setting instance_id
        to None or when deleting an interface with state=absent.
    default: 'no'
  delete_on_termination:
    description:
      - Delete the interface when the instance it is attached to is terminated. You can only specify this flag when the
        interface is being modified, not on creation.
    required: false
  source_dest_check:
    description:
      - By default, interfaces perform source/destination checks. NAT instances however need this check to be disabled.
        You can only specify this flag when the interface is being modified, not on creation.
    required: false
  secondary_private_ip_addresses:
    description:
      - A list of IP addresses to assign as secondary IP addresses to the network interface.
        This option is mutually exclusive of secondary_private_ip_address_count
    required: false
    version_added: 2.2
  purge_secondary_private_ip_addresses:
    description:
      - To be used with I(secondary_private_ip_addresses) to determine whether or not to remove any secondary IP addresses other than those specified.
        Set secondary_private_ip_addresses to an empty list to purge all secondary addresses.
    default: no
    version_added: 2.5
  secondary_private_ip_address_count:
    description:
      - The number of secondary IP addresses to assign to the network interface. This option is mutually exclusive of secondary_private_ip_addresses
    required: false
    version_added: 2.2
extends_documentation_fragment:
    - aws
    - ec2
notes:
    - This module identifies and ENI based on either the eni_id, a combination of private_ip_address and subnet_id,
      or a combination of instance_id and device_id. Any of these options will let you specify a particular ENI.
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create an ENI. As no security group is defined, ENI will be created in default security group
- ec2_eni:
    private_ip_address: 172.31.0.20
    subnet_id: subnet-xxxxxxxx
    state: present

# Create an ENI and attach it to an instance
- ec2_eni:
    instance_id: i-xxxxxxx
    device_index: 1
    private_ip_address: 172.31.0.20
    subnet_id: subnet-xxxxxxxx
    state: present

# Create an ENI with two secondary addresses
- ec2_eni:
    subnet_id: subnet-xxxxxxxx
    state: present
    secondary_private_ip_address_count: 2

# Assign a secondary IP address to an existing ENI
# This will purge any existing IPs
- ec2_eni:
    subnet_id: subnet-xxxxxxxx
    eni_id: eni-yyyyyyyy
    state: present
    secondary_private_ip_addresses:
      - 172.16.1.1

# Remove any secondary IP addresses from an existing ENI
- ec2_eni:
    subnet_id: subnet-xxxxxxxx
    eni_id: eni-yyyyyyyy
    state: present
    secondary_private_ip_address_count: 0

# Destroy an ENI, detaching it from any instance if necessary
- ec2_eni:
    eni_id: eni-xxxxxxx
    force_detach: yes
    state: absent

# Update an ENI
- ec2_eni:
    eni_id: eni-xxxxxxx
    description: "My new description"
    state: present

# Update an ENI identifying it by private_ip_address and subnet_id
- ec2_eni:
    subnet_id: subnet-xxxxxxx
    private_ip_address: 172.16.1.1
    description: "My new description"

# Detach an ENI from an instance
- ec2_eni:
    eni_id: eni-xxxxxxx
    instance_id: None
    state: present

### Delete an interface on termination
# First create the interface
- ec2_eni:
    instance_id: i-xxxxxxx
    device_index: 1
    private_ip_address: 172.31.0.20
    subnet_id: subnet-xxxxxxxx
    state: present
  register: eni

# Modify the interface to enable the delete_on_terminaton flag
- ec2_eni:
    eni_id: "{{ eni.interface.id }}"
    delete_on_termination: true

'''


RETURN = '''
interface:
  description: Network interface attributes
  returned: when state != absent
  type: complex
  contains:
    description:
      description: interface description
      type: string
      sample: Firewall network interface
    groups:
      description: list of security groups
      type: list of dictionaries
      sample: [ { "sg-f8a8a9da": "default" } ]
    id:
      description: network interface id
      type: string
      sample: "eni-1d889198"
    mac_address:
      description: interface's physical address
      type: string
      sample: "00:00:5E:00:53:23"
    owner_id:
      description: aws account id
      type: string
      sample: 812381371
    private_ip_address:
      description: primary ip address of this interface
      type: string
      sample: 10.20.30.40
    private_ip_addresses:
      description: list of all private ip addresses associated to this interface
      type: list of dictionaries
      sample: [ { "primary_address": true, "private_ip_address": "10.20.30.40" } ]
    source_dest_check:
      description: value of source/dest check flag
      type: boolean
      sample: True
    status:
      description: network interface status
      type: string
      sample: "pending"
    subnet_id:
      description: which vpc subnet the interface is bound
      type: string
      sample: subnet-b0a0393c
    vpc_id:
      description: which vpc this network interface is bound
      type: string
      sample: vpc-9a9a9da

'''

import time
import re

try:
    import boto.ec2
    import boto.vpc
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (AnsibleAWSError, connect_to_aws,
                                      ec2_argument_spec, get_aws_connection_info,
                                      get_ec2_security_group_ids_from_names)


def get_eni_info(interface):

    # Private addresses
    private_addresses = []
    for ip in interface.private_ip_addresses:
        private_addresses.append({'private_ip_address': ip.private_ip_address, 'primary_address': ip.primary})

    interface_info = {'id': interface.id,
                      'subnet_id': interface.subnet_id,
                      'vpc_id': interface.vpc_id,
                      'description': interface.description,
                      'owner_id': interface.owner_id,
                      'status': interface.status,
                      'mac_address': interface.mac_address,
                      'private_ip_address': interface.private_ip_address,
                      'source_dest_check': interface.source_dest_check,
                      'groups': dict((group.id, group.name) for group in interface.groups),
                      'private_ip_addresses': private_addresses
                      }

    if interface.attachment is not None:
        interface_info['attachment'] = {'attachment_id': interface.attachment.id,
                                        'instance_id': interface.attachment.instance_id,
                                        'device_index': interface.attachment.device_index,
                                        'status': interface.attachment.status,
                                        'attach_time': interface.attachment.attach_time,
                                        'delete_on_termination': interface.attachment.delete_on_termination,
                                        }

    return interface_info


def wait_for_eni(eni, status):

    while True:
        time.sleep(3)
        eni.update()
        # If the status is detached we just need attachment to disappear
        if eni.attachment is None:
            if status == "detached":
                break
        else:
            if status == "attached" and eni.attachment.status == "attached":
                break


def create_eni(connection, vpc_id, module):

    instance_id = module.params.get("instance_id")
    attached = module.params.get("attached")
    if instance_id == 'None':
        instance_id = None
    device_index = module.params.get("device_index")
    subnet_id = module.params.get('subnet_id')
    private_ip_address = module.params.get('private_ip_address')
    description = module.params.get('description')
    security_groups = get_ec2_security_group_ids_from_names(module.params.get('security_groups'), connection, vpc_id=vpc_id, boto3=False)
    secondary_private_ip_addresses = module.params.get("secondary_private_ip_addresses")
    secondary_private_ip_address_count = module.params.get("secondary_private_ip_address_count")
    changed = False

    try:
        eni = connection.create_network_interface(subnet_id, private_ip_address, description, security_groups)
        if attached and instance_id is not None:
            try:
                eni.attach(instance_id, device_index)
            except BotoServerError:
                eni.delete()
                raise
            # Wait to allow creation / attachment to finish
            wait_for_eni(eni, "attached")
            eni.update()

        if secondary_private_ip_address_count is not None:
            try:
                connection.assign_private_ip_addresses(network_interface_id=eni.id, secondary_private_ip_address_count=secondary_private_ip_address_count)
            except BotoServerError:
                eni.delete()
                raise

        if secondary_private_ip_addresses is not None:
            try:
                connection.assign_private_ip_addresses(network_interface_id=eni.id, private_ip_addresses=secondary_private_ip_addresses)
            except BotoServerError:
                eni.delete()
                raise

        changed = True

    except BotoServerError as e:
        module.fail_json(msg=e.message)

    module.exit_json(changed=changed, interface=get_eni_info(eni))


def modify_eni(connection, vpc_id, module, eni):

    instance_id = module.params.get("instance_id")
    attached = module.params.get("attached")
    do_detach = module.params.get('state') == 'detached'
    device_index = module.params.get("device_index")
    description = module.params.get('description')
    security_groups = module.params.get('security_groups')
    force_detach = module.params.get("force_detach")
    source_dest_check = module.params.get("source_dest_check")
    delete_on_termination = module.params.get("delete_on_termination")
    secondary_private_ip_addresses = module.params.get("secondary_private_ip_addresses")
    purge_secondary_private_ip_addresses = module.params.get("purge_secondary_private_ip_addresses")
    secondary_private_ip_address_count = module.params.get("secondary_private_ip_address_count")
    changed = False

    try:
        if description is not None:
            if eni.description != description:
                connection.modify_network_interface_attribute(eni.id, "description", description)
                changed = True
        if len(security_groups) > 0:
            groups = get_ec2_security_group_ids_from_names(security_groups, connection, vpc_id=vpc_id, boto3=False)
            if sorted(get_sec_group_list(eni.groups)) != sorted(groups):
                connection.modify_network_interface_attribute(eni.id, "groupSet", groups)
                changed = True
        if source_dest_check is not None:
            if eni.source_dest_check != source_dest_check:
                connection.modify_network_interface_attribute(eni.id, "sourceDestCheck", source_dest_check)
                changed = True
        if delete_on_termination is not None and eni.attachment is not None:
            if eni.attachment.delete_on_termination is not delete_on_termination:
                connection.modify_network_interface_attribute(eni.id, "deleteOnTermination", delete_on_termination, eni.attachment.id)
                changed = True

        current_secondary_addresses = [i.private_ip_address for i in eni.private_ip_addresses if not i.primary]
        if secondary_private_ip_addresses is not None:
            secondary_addresses_to_remove = list(set(current_secondary_addresses) - set(secondary_private_ip_addresses))
            if secondary_addresses_to_remove and purge_secondary_private_ip_addresses:
                connection.unassign_private_ip_addresses(network_interface_id=eni.id,
                                                         private_ip_addresses=list(set(current_secondary_addresses) -
                                                                                   set(secondary_private_ip_addresses)),
                                                         dry_run=False)
                changed = True

            secondary_addresses_to_add = list(set(secondary_private_ip_addresses) - set(current_secondary_addresses))
            if secondary_addresses_to_add:
                connection.assign_private_ip_addresses(network_interface_id=eni.id,
                                                       private_ip_addresses=secondary_addresses_to_add,
                                                       secondary_private_ip_address_count=None,
                                                       allow_reassignment=False, dry_run=False)
                changed = True
        if secondary_private_ip_address_count is not None:
            current_secondary_address_count = len(current_secondary_addresses)

            if secondary_private_ip_address_count > current_secondary_address_count:
                connection.assign_private_ip_addresses(network_interface_id=eni.id,
                                                       private_ip_addresses=None,
                                                       secondary_private_ip_address_count=(secondary_private_ip_address_count -
                                                                                           current_secondary_address_count),
                                                       allow_reassignment=False, dry_run=False)
                changed = True
            elif secondary_private_ip_address_count < current_secondary_address_count:
                # How many of these addresses do we want to remove
                secondary_addresses_to_remove_count = current_secondary_address_count - secondary_private_ip_address_count
                connection.unassign_private_ip_addresses(network_interface_id=eni.id,
                                                         private_ip_addresses=current_secondary_addresses[:secondary_addresses_to_remove_count],
                                                         dry_run=False)

        if attached is True:
            if eni.attachment and eni.attachment.instance_id != instance_id:
                detach_eni(eni, module)
                eni.attach(instance_id, device_index)
                wait_for_eni(eni, "attached")
                changed = True
            if eni.attachment is None:
                eni.attach(instance_id, device_index)
                wait_for_eni(eni, "attached")
                changed = True
        elif attached is False:
            detach_eni(eni, module)

    except BotoServerError as e:
        module.fail_json(msg=e.message)

    eni.update()
    module.exit_json(changed=changed, interface=get_eni_info(eni))


def delete_eni(connection, module):

    eni_id = module.params.get("eni_id")
    force_detach = module.params.get("force_detach")

    try:
        eni_result_set = connection.get_all_network_interfaces(eni_id)
        eni = eni_result_set[0]

        if force_detach is True:
            if eni.attachment is not None:
                eni.detach(force_detach)
                # Wait to allow detachment to finish
                wait_for_eni(eni, "detached")
                eni.update()
            eni.delete()
            changed = True
        else:
            eni.delete()
            changed = True

        module.exit_json(changed=changed)
    except BotoServerError as e:
        regex = re.compile('The networkInterface ID \'.*\' does not exist')
        if regex.search(e.message) is not None:
            module.exit_json(changed=False)
        else:
            module.fail_json(msg=e.message)


def detach_eni(eni, module):

    attached = module.params.get("attached")

    force_detach = module.params.get("force_detach")
    if eni.attachment is not None:
        eni.detach(force_detach)
        wait_for_eni(eni, "detached")
        if attached:
            return
        eni.update()
        module.exit_json(changed=True, interface=get_eni_info(eni))
    else:
        module.exit_json(changed=False, interface=get_eni_info(eni))


def uniquely_find_eni(connection, module):

    eni_id = module.params.get("eni_id")
    private_ip_address = module.params.get('private_ip_address')
    subnet_id = module.params.get('subnet_id')
    instance_id = module.params.get('instance_id')
    device_index = module.params.get('device_index')
    attached = module.params.get('attached')

    try:
        filters = {}

        # proceed only if we're univocally specifying an ENI
        if eni_id is None and private_ip_address is None and (instance_id is None and device_index is None):
            return None

        if private_ip_address and subnet_id:
            filters['private-ip-address'] = private_ip_address
            filters['subnet-id'] = subnet_id

        if not attached and instance_id and device_index:
            filters['attachment.instance-id'] = instance_id
            filters['attachment.device-index'] = device_index

        if eni_id is None and len(filters) == 0:
            return None

        eni_result = connection.get_all_network_interfaces(eni_id, filters=filters)
        if len(eni_result) == 1:
            return eni_result[0]
        else:
            return None

    except BotoServerError as e:
        module.fail_json(msg=e.message)

    return None


def get_sec_group_list(groups):

    # Build list of remote security groups
    remote_security_groups = []
    for group in groups:
        remote_security_groups.append(group.id.encode())

    return remote_security_groups


def _get_vpc_id(connection, module, subnet_id):

    try:
        return connection.get_all_subnets(subnet_ids=[subnet_id])[0].vpc_id
    except BotoServerError as e:
        module.fail_json(msg=e.message)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            eni_id=dict(default=None, type='str'),
            instance_id=dict(default=None, type='str'),
            private_ip_address=dict(type='str'),
            subnet_id=dict(type='str'),
            description=dict(type='str'),
            security_groups=dict(default=[], type='list'),
            device_index=dict(default=0, type='int'),
            state=dict(default='present', choices=['present', 'absent']),
            force_detach=dict(default='no', type='bool'),
            source_dest_check=dict(default=None, type='bool'),
            delete_on_termination=dict(default=None, type='bool'),
            secondary_private_ip_addresses=dict(default=None, type='list'),
            purge_secondary_private_ip_addresses=dict(default=False, type='bool'),
            secondary_private_ip_address_count=dict(default=None, type='int'),
            attached=dict(default=None, type='bool')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=[
                               ['secondary_private_ip_addresses', 'secondary_private_ip_address_count']
                           ],
                           required_if=([
                               ('state', 'absent', ['eni_id']),
                               ('attached', True, ['instance_id']),
                               ('purge_secondary_private_ip_addresses', True, ['secondary_private_ip_addresses'])
                           ])
                           )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)

    if region:
        try:
            connection = connect_to_aws(boto.ec2, region, **aws_connect_params)
            vpc_connection = connect_to_aws(boto.vpc, region, **aws_connect_params)
        except (boto.exception.NoAuthHandlerFound, AnsibleAWSError) as e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    state = module.params.get("state")

    if state == 'present':
        eni = uniquely_find_eni(connection, module)
        if eni is None:
            subnet_id = module.params.get("subnet_id")
            if subnet_id is None:
                module.fail_json(msg="subnet_id is required when creating a new ENI")

            vpc_id = _get_vpc_id(vpc_connection, module, subnet_id)
            create_eni(connection, vpc_id, module)
        else:
            vpc_id = eni.vpc_id
            modify_eni(connection, vpc_id, module, eni)

    elif state == 'absent':
        delete_eni(connection, module)


if __name__ == '__main__':
    main()
