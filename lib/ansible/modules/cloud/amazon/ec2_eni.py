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
author:
    - "Rob White (@wimnat)"
    - "Mike Healey (@healem)"
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
      - Specifies if network interface should be attached or detached from instance. If omitted, attachment status
        won't change
    version_added: 2.2
    type: bool
  force_detach:
    description:
      - Force detachment of the interface. This applies either when explicitly detaching the interface by setting instance_id
        to None or when deleting an interface with state=absent.
    default: 'no'
    type: bool
  delete_on_termination:
    description:
      - Delete the interface when the instance it is attached to is terminated. You can only specify this flag when the
        interface is being modified, not on creation.
    required: false
    type: bool
  source_dest_check:
    description:
      - By default, interfaces perform source/destination checks. NAT instances however need this check to be disabled.
        You can only specify this flag when the interface is being modified, not on creation.
    required: false
    type: bool
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
    type: bool
    version_added: 2.5
  secondary_private_ip_address_count:
    description:
      - The number of secondary IP addresses to assign to the network interface. This option is mutually exclusive of secondary_private_ip_addresses
    required: false
    version_added: 2.2
  allow_reassignment:
    description:
      - Indicates whether to allow an IP address that is already assigned to another network interface or instance
        to be reassigned to the specified network interface.
    required: false
    default: 'no'
    type: bool
    version_added: 2.7
  name:
    description:
      - Name for the ENI. This will create a tag called "Name" with the value assigned here.
      - This can be used in conjunction with I(subnet_id) as another means of identifiying a network interface.
      - AWS does not enforce unique Name tags, so duplicate names are possible if you configure it that way.
        If that is the case, you will need to provide other identifying information such as I(private_ip_address) or I(eni_id).
    required: false
    version_added: "2.10"
  tags:
    description:
      - A hash/dictionary of tags to add to the new ENI or to add/remove from an existing one. Please note that
        the name field sets the "Name" tag.
      - To clear all tags, set this option to an empty dictionary to use in conjunction with I(purge_tags).
        If you provide I(name), that tag will not be removed.
      - To prevent removing any tags set I(purge_tags) to false.
    required: false
    version_added: "2.10"
  purge_tags:
    description:
      - Indicates whether to remove tags not specified in I(tags) or I(name). This means you have to specify all
        the desired tags on each task affecting a network interface.
      - If I(tags) is omitted or None this option is disregarded.
    default: true
    type: bool
    version_added: "2.10"
extends_documentation_fragment:
    - aws
    - ec2
notes:
    - This module identifies an ENI based on either the eni_id, the name and subnet_id,
      a combination of private_ip_address and subnet_id, or a combination of instance_id and device_id.
      Any of these options will let you specify a particular ENI.
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create an ENI. As no security group is defined, ENI will be created in default security group
- ec2_eni:
    name: eni-20
    private_ip_address: 172.31.0.20
    subnet_id: subnet-xxxxxxxx
    state: present
    tags:
      group: Finance

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

# Update an ENI using name and subnet_id
- ec2_eni:
    name: eni-20
    subnet_id: subnet-xxxxxxx
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
      type: str
      sample: Firewall network interface
    groups:
      description: list of security groups
      type: list of dictionaries
      sample: [ { "sg-f8a8a9da": "default" } ]
    id:
      description: network interface id
      type: str
      sample: "eni-1d889198"
    mac_address:
      description: interface's physical address
      type: str
      sample: "00:00:5E:00:53:23"
    name:
      description: The name of the ENI
      type: str
      sample: "my-eni-20"
    owner_id:
      description: aws account id
      type: str
      sample: 812381371
    private_ip_address:
      description: primary ip address of this interface
      type: str
      sample: 10.20.30.40
    private_ip_addresses:
      description: list of all private ip addresses associated to this interface
      type: list of dictionaries
      sample: [ { "primary_address": true, "private_ip_address": "10.20.30.40" } ]
    source_dest_check:
      description: value of source/dest check flag
      type: bool
      sample: True
    status:
      description: network interface status
      type: str
      sample: "pending"
    subnet_id:
      description: which vpc subnet the interface is bound
      type: str
      sample: subnet-b0a0393c
    tags:
      description: The dictionary of tags associated with the ENI
      type: dict
      sample: { "Name": "my-eni", "group": "Finance" }
    vpc_id:
      description: which vpc this network interface is bound
      type: str
      sample: vpc-9a9a9da

'''

import time
import re

try:
    import boto3
    import botocore.exceptions
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.ec2 import (
    AWSRetry,
    ec2_argument_spec,
    get_ec2_security_group_ids_from_names,
    compare_aws_tags,
    boto3_tag_list_to_ansible_dict,
    ansible_dict_to_boto3_tag_list
)

from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code
from ansible.module_utils.aws.waiters import get_waiter


def get_eni_info(interface):

    # Private addresses
    private_addresses = []
    if "PrivateIpAddresses" in interface:
        for ip in interface["PrivateIpAddresses"]:
            private_addresses.append({'private_ip_address': ip["PrivateIpAddress"], 'primary_address': ip["Primary"]})

    groups = {}
    if "Groups" in interface:
        for group in interface["Groups"]:
            groups[group["GroupId"]] = group["GroupName"]

    interface_info = {'id': interface.get("NetworkInterfaceId"),
                      'subnet_id': interface.get("SubnetId"),
                      'vpc_id': interface.get("VpcId"),
                      'description': interface.get("Description"),
                      'owner_id': interface.get("OwnerId"),
                      'status': interface.get("Status"),
                      'mac_address': interface.get("MacAddress"),
                      'private_ip_address': interface.get("PrivateIpAddress"),
                      'source_dest_check': interface.get("SourceDestCheck"),
                      'groups': groups,
                      'private_ip_addresses': private_addresses
                      }

    if "TagSet" in interface:
        tags = {}
        name = None
        for tag in interface["TagSet"]:
            tags[tag["Key"]] = tag["Value"]
            if tag["Key"] == "Name":
                name = tag["Value"]
        interface_info["tags"] = tags

        if name is not None:
            interface_info["name"] = name

    if "Attachment" in interface:
        interface_info['attachment'] = {
            'attachment_id': interface["Attachment"].get("AttachmentId"),
            'instance_id': interface["Attachment"].get("InstanceId"),
            'device_index': interface["Attachment"].get("DeviceIndex"),
            'status': interface["Attachment"].get("Status"),
            'attach_time': interface["Attachment"].get("AttachTime"),
            'delete_on_termination': interface["Attachment"].get("DeleteOnTermination"),
        }

    return interface_info


def correct_ips(connection, ip_list, module, eni=None):
    all_there = True
    eni = uniquely_find_eni(connection, module, eni)
    private_addresses = set()
    if "PrivateIpAddresses" in eni:
        for ip in eni["PrivateIpAddresses"]:
            private_addresses.add(ip["PrivateIpAddress"])

    for ip in ip_list:
        if ip not in private_addresses:
            all_there = False
            break

    if all_there:
        return True
    else:
        return False


def correct_ip_count(connection, ip_count, module, eni=None):
    eni = uniquely_find_eni(connection, module, eni)
    private_addresses = set()
    if "PrivateIpAddresses" in eni:
        for ip in eni["PrivateIpAddresses"]:
            private_addresses.add(ip["PrivateIpAddress"])

    if len(private_addresses) == ip_count:
        return True
    else:
        return False


def wait_for(function_pointer, *args):
    max_wait = 30
    interval_time = 3
    current_wait = 0
    while current_wait < max_wait:
        time.sleep(interval_time)
        current_wait += interval_time
        if function_pointer(*args):
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
    security_groups = get_ec2_security_group_ids_from_names(
        module.params.get('security_groups'),
        connection,
        vpc_id=vpc_id,
        boto3=True
    )
    secondary_private_ip_addresses = module.params.get("secondary_private_ip_addresses")
    secondary_private_ip_address_count = module.params.get("secondary_private_ip_address_count")
    changed = False
    tags = module.params.get("tags")
    name = module.params.get("name")
    purge_tags = module.params.get("purge_tags")

    try:
        args = {"SubnetId": subnet_id}
        if private_ip_address:
            args["PrivateIpAddress"] = private_ip_address
        if description:
            args["Description"] = description
        if len(security_groups) > 0:
            args["Groups"] = security_groups
        eni_dict = connection.create_network_interface(**args)
        eni = eni_dict["NetworkInterface"]
        if attached and instance_id is not None:
            try:
                connection.attach_network_interface(
                    InstanceId=instance_id,
                    DeviceIndex=device_index,
                    NetworkInterfaceId=eni["NetworkInterfaceId"]
                )
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError):
                connection.delete_network_interface(NetworkInterfaceId=eni["NetworkInterfaceId"])
                raise
            # Wait to allow creation / attachment to finish
            get_waiter(connection, 'network_interface_attached').wait(NetworkInterfaceIds=[eni["NetworkInterfaceId"]])
            eni = uniquely_find_eni(connection, module, eni)

        if secondary_private_ip_address_count is not None:
            try:
                connection.assign_private_ip_addresses(
                    NetworkInterfaceId=eni["NetworkInterfaceId"],
                    SecondaryPrivateIpAddressCount=secondary_private_ip_address_count
                )
                eni = uniquely_find_eni(connection, module, eni)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError):
                connection.delete_network_interface(NetworkInterfaceId=eni["NetworkInterfaceId"])
                raise

        if secondary_private_ip_addresses is not None:
            try:
                connection.assign_private_ip_addresses(
                    NetworkInterfaceId=eni["NetworkInterfaceId"],
                    PrivateIpAddresses=secondary_private_ip_addresses
                )
                eni = uniquely_find_eni(connection, module, eni)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError):
                connection.delete_network_interface(NetworkInterfaceId=eni["NetworkInterfaceId"])
                raise

        manage_tags(eni, name, tags, purge_tags, connection)

        # Refresh the eni data on last time
        eni = uniquely_find_eni(connection, module, eni)

        changed = True

    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(
            e,
            "Failed to create eni {0} for {1} in {2} with {3}".format(name, subnet_id, vpc_id, private_ip_address)
        )

    module.exit_json(changed=changed, interface=get_eni_info(eni))


def modify_eni(connection, module, eni):

    instance_id = module.params.get("instance_id")
    attached = module.params.get("attached")
    device_index = module.params.get("device_index")
    description = module.params.get('description')
    security_groups = module.params.get('security_groups')
    force_detach = module.params.get("force_detach")
    source_dest_check = module.params.get("source_dest_check")
    delete_on_termination = module.params.get("delete_on_termination")
    secondary_private_ip_addresses = module.params.get("secondary_private_ip_addresses")
    purge_secondary_private_ip_addresses = module.params.get("purge_secondary_private_ip_addresses")
    secondary_private_ip_address_count = module.params.get("secondary_private_ip_address_count")
    allow_reassignment = module.params.get("allow_reassignment")
    changed = False
    tags = module.params.get("tags")
    name = module.params.get("name")
    purge_tags = module.params.get("purge_tags")

    eni = uniquely_find_eni(connection, module, eni)

    try:
        if description is not None:
            if "Description" not in eni or eni["Description"] != description:
                connection.modify_network_interface_attribute(
                    NetworkInterfaceId=eni["NetworkInterfaceId"],
                    Description={'Value': description}
                )
                changed = True
        if len(security_groups) > 0:
            groups = get_ec2_security_group_ids_from_names(security_groups, connection, vpc_id=eni["VpcId"], boto3=True)
            if sorted(get_sec_group_list(eni["Groups"])) != sorted(groups):
                connection.modify_network_interface_attribute(
                    NetworkInterfaceId=eni["NetworkInterfaceId"],
                    Groups=groups
                )
                changed = True
        if source_dest_check is not None:
            if "SourceDestCheck" not in eni or eni["SourceDestCheck"] != source_dest_check:
                connection.modify_network_interface_attribute(
                    NetworkInterfaceId=eni["NetworkInterfaceId"],
                    SourceDestCheck={'Value': source_dest_check}
                )
                changed = True
        if delete_on_termination is not None and "Attachment" in eni:
            if eni["Attachment"]["DeleteOnTermination"] is not delete_on_termination:
                connection.modify_network_interface_attribute(
                    NetworkInterfaceId=eni["NetworkInterfaceId"],
                    Attachment={'AttachmentId': eni["Attachment"]["AttachmentId"],
                                'DeleteOnTermination': delete_on_termination}
                )
                changed = True

        current_secondary_addresses = []
        if "PrivateIpAddresses" in eni:
            current_secondary_addresses = [i["PrivateIpAddress"] for i in eni["PrivateIpAddresses"] if not i["Primary"]]

        if secondary_private_ip_addresses is not None:
            secondary_addresses_to_remove = list(set(current_secondary_addresses) - set(secondary_private_ip_addresses))
            if secondary_addresses_to_remove and purge_secondary_private_ip_addresses:
                connection.unassign_private_ip_addresses(
                    NetworkInterfaceId=eni["NetworkInterfaceId"],
                    PrivateIpAddresses=list(set(current_secondary_addresses) - set(secondary_private_ip_addresses)),
                )
                changed = True
            secondary_addresses_to_add = list(set(secondary_private_ip_addresses) - set(current_secondary_addresses))
            if secondary_addresses_to_add:
                connection.assign_private_ip_addresses(
                    NetworkInterfaceId=eni["NetworkInterfaceId"],
                    PrivateIpAddresses=secondary_addresses_to_add,
                    AllowReassignment=allow_reassignment
                )
                wait_for(correct_ips, connection, secondary_addresses_to_add, module, eni)
                changed = True

        if secondary_private_ip_address_count is not None:
            current_secondary_address_count = len(current_secondary_addresses)
            if secondary_private_ip_address_count > current_secondary_address_count:
                connection.assign_private_ip_addresses(
                    NetworkInterfaceId=eni["NetworkInterfaceId"],
                    SecondaryPrivateIpAddressCount=(secondary_private_ip_address_count - current_secondary_address_count),
                    AllowReassignment=allow_reassignment
                )
                wait_for(correct_ip_count, connection, secondary_private_ip_address_count, module, eni)
                changed = True
            elif secondary_private_ip_address_count < current_secondary_address_count:
                # How many of these addresses do we want to remove
                secondary_addresses_to_remove_count = current_secondary_address_count - secondary_private_ip_address_count
                connection.unassign_private_ip_addresses(
                    NetworkInterfaceId=eni["NetworkInterfaceId"],
                    PrivateIpAddresses=current_secondary_addresses[:secondary_addresses_to_remove_count]
                )

        if attached is True:
            if "Attachment" in eni and eni["Attachment"]["InstanceId"] != instance_id:
                detach_eni(connection, eni, module)
                connection.attach_network_interface(
                    InstanceId=instance_id,
                    DeviceIndex=device_index,
                    NetworkInterfaceId=eni["NetworkInterfaceId"]
                )
                get_waiter(connection, 'network_interface_attached').wait(NetworkInterfaceIds=[eni["NetworkInterfaceId"]])
                changed = True
            if "Attachment" not in eni:
                connection.attach_network_interface(
                    InstanceId=instance_id,
                    DeviceIndex=device_index,
                    NetworkInterfaceId=eni["NetworkInterfaceId"]
                )
                get_waiter(connection, 'network_interface_attached').wait(NetworkInterfaceIds=[eni["NetworkInterfaceId"]])
                changed = True

        elif attached is False:
            detach_eni(connection, eni, module)

        changed |= manage_tags(eni, name, tags, purge_tags, connection)

    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "Failed to modify eni {0}".format(eni['NetworkInterfaceId']))

    eni = uniquely_find_eni(connection, module, eni)
    module.exit_json(changed=changed, interface=get_eni_info(eni))


def delete_eni(connection, module):

    eni = uniquely_find_eni(connection, module)
    if not eni:
        module.exit_json(changed=False)

    eni_id = eni["NetworkInterfaceId"]
    force_detach = module.params.get("force_detach")

    try:
        if force_detach is True:
            if "Attachment" in eni:
                connection.detach_network_interface(
                    AttachmentId=eni["Attachment"]["AttachmentId"],
                    Force=True
                )
                # Wait to allow detachment to finish
                connection.get_waiter('network_interface_available').wait(NetworkInterfaceIds=[eni["NetworkInterfaceId"]])
            connection.delete_network_interface(NetworkInterfaceId=eni_id)
            changed = True
        else:
            connection.delete_network_interface(NetworkInterfaceId=eni_id)
            changed = True

        module.exit_json(changed=changed)
    except is_boto3_error_code('InvalidNetworkInterfaceID.NotFound'):
        module.exit_json(changed=False)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, "Failure during delete of {0}".format(eni_id))


def detach_eni(connection, eni, module):

    attached = module.params.get("attached")

    force_detach = module.params.get("force_detach")
    if "Attachment" in eni:
        connection.detach_network_interface(
            AttachmentId=eni["Attachment"]["AttachmentId"],
            Force=force_detach
        )
        connection.get_waiter('network_interface_available').wait(NetworkInterfaceIds=[eni["NetworkInterfaceId"]])
        if attached:
            return
        eni = uniquely_find_eni(connection, module)
        module.exit_json(changed=True, interface=get_eni_info(eni))
    else:
        module.exit_json(changed=False, interface=get_eni_info(eni))


def uniquely_find_eni(connection, module, eni=None):

    if eni:
        # In the case of create, eni_id will not be a param but we can still get the eni_id after creation
        if "NetworkInterfaceId" in eni:
            eni_id = eni["NetworkInterfaceId"]
        else:
            eni_id = None
    else:
        eni_id = module.params.get("eni_id")

    private_ip_address = module.params.get('private_ip_address')
    subnet_id = module.params.get('subnet_id')
    instance_id = module.params.get('instance_id')
    device_index = module.params.get('device_index')
    attached = module.params.get('attached')
    name = module.params.get("name")

    filters = []

    # proceed only if we're unequivocally specifying an ENI
    if eni_id is None and private_ip_address is None and (instance_id is None and device_index is None):
        return None

    if eni_id:
        filters.append({'Name': 'network-interface-id',
                        'Values': [eni_id]})

    if private_ip_address and subnet_id and not filters:
        filters.append({'Name': 'private-ip-address',
                        'Values': [private_ip_address]})
        filters.append({'Name': 'subnet-id',
                        'Values': [subnet_id]})

    if not attached and instance_id and device_index and not filters:
        filters.append({'Name': 'attachment.instance-id',
                        'Values': [instance_id]})
        filters.append({'Name': 'attachment.device-index',
                        'Values': [device_index]})

    if name and subnet_id and not filters:
        filters.append({'Name': 'tag:Name',
                        'Values': [name]})
        filters.append({'Name': 'subnet-id',
                        'Values': [subnet_id]})

    if not filters:
        return None

    try:
        eni_result = connection.describe_network_interfaces(Filters=filters)["NetworkInterfaces"]
        if len(eni_result) == 1:
            return eni_result[0]
        else:
            return None
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "Failed to find unique eni with filters: {0}".format(filters))

    return None


def get_sec_group_list(groups):

    # Build list of remote security groups
    remote_security_groups = []
    for group in groups:
        remote_security_groups.append(group["GroupId"].encode())

    return remote_security_groups


def _get_vpc_id(connection, module, subnet_id):

    try:
        subnets = connection.describe_subnets(SubnetIds=[subnet_id])
        return subnets["Subnets"][0]["VpcId"]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "Failed to get vpc_id for {0}".format(subnet_id))


@AWSRetry.jittered_backoff()
def manage_tags(eni, name, new_tags, purge_tags, connection):
    changed = False

    if "TagSet" in eni:
        old_tags = boto3_tag_list_to_ansible_dict(eni['TagSet'])
    elif new_tags:
        old_tags = {}
    else:
        # No new tags and nothing in TagSet
        return False

    # Do not purge tags unless tags is not None
    if new_tags is None:
        purge_tags = False
        new_tags = {}

    if name:
        new_tags['Name'] = name

    tags_to_set, tags_to_delete = compare_aws_tags(
        old_tags, new_tags,
        purge_tags=purge_tags,
    )
    if tags_to_set:
        connection.create_tags(
            Resources=[eni['NetworkInterfaceId']],
            Tags=ansible_dict_to_boto3_tag_list(tags_to_set))
        changed |= True
    if tags_to_delete:
        delete_with_current_values = dict((k, old_tags.get(k)) for k in tags_to_delete)
        connection.delete_tags(
            Resources=[eni['NetworkInterfaceId']],
            Tags=ansible_dict_to_boto3_tag_list(delete_with_current_values))
        changed |= True
    return changed


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
            allow_reassignment=dict(default=False, type='bool'),
            attached=dict(default=None, type='bool'),
            name=dict(default=None, type='str'),
            tags=dict(type='dict'),
            purge_tags=dict(default=True, type='bool')
        )
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[
            ['secondary_private_ip_addresses', 'secondary_private_ip_address_count']
        ],
        required_if=([
            ('attached', True, ['instance_id']),
            ('purge_secondary_private_ip_addresses', True, ['secondary_private_ip_addresses'])
        ])
    )

    connection = module.client('ec2')
    state = module.params.get("state")

    if state == 'present':
        eni = uniquely_find_eni(connection, module)
        if eni is None:
            subnet_id = module.params.get("subnet_id")
            if subnet_id is None:
                module.fail_json(msg="subnet_id is required when creating a new ENI")

            vpc_id = _get_vpc_id(connection, module, subnet_id)
            create_eni(connection, vpc_id, module)
        else:
            modify_eni(connection, module, eni)

    elif state == 'absent':
        delete_eni(connection, module)


if __name__ == '__main__':
    main()
