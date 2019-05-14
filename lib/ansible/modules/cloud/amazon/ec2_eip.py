#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_eip
short_description: manages EC2 elastic IP (EIP) addresses.
description:
    - This module can allocate or release an EIP.
    - This module can associate/disassociate an EIP with instances or network interfaces.
version_added: "1.4"
options:
  device_id:
    description:
      - The id of the device for the EIP. Can be an EC2 Instance id or Elastic Network Interface (ENI) id.
    required: false
    aliases: [ instance_id ]
    version_added: "2.0"
  public_ip:
    description:
      - The IP address of a previously allocated EIP.
      - If present and device is specified, the EIP is associated with the device.
      - If absent and device is specified, the EIP is disassociated from the device.
    aliases: [ ip ]
  state:
    description:
      - If present, allocate an EIP or associate an existing EIP with a device.
      - If absent, disassociate the EIP from the device and optionally release it.
    choices: ['present', 'absent']
    default: present
  reuse_existing_ip_allowed:
    description:
      - Reuse an EIP that is not associated to a device (when available), instead of allocating a new one.
    default: 'no'
    type: bool
    version_added: "1.6"
  release_on_disassociation:
    description:
      - whether or not to automatically release the EIP when it is disassociated
    default: 'no'
    type: bool
    version_added: "2.0"
  private_ip_address:
    description:
      - The primary or secondary private IP address to associate with the Elastic IP address.
    version_added: "2.3"
  allow_reassociation:
    description:
      -  Specify this option to allow an Elastic IP address that is already associated with another
         network interface or instance to be re-associated with the specified instance or interface.
    default: 'no'
    type: bool
    version_added: "2.5"
  name:
    description:
      - Name for the elastic IP.  If name is unique within the account, can be used to maintain idempotency.  This
        field is set as the "Name" tag and will overwrite any existing value in the "Name" tag
    required: false
    version_added: "2.9"
  tags:
    description:
      - A hash/dictionary of tags to add to the new EIP or to add/remove from an existing one.  Please note that
        the name field sets the "Name" tag.  So if you manually clear the Name tag, you will also clear the name.
    required: false
    version_added: "2.9"
  purge_tags:
    description:
      - Delete any tags not specified in the task that are on the instance.
        This means you have to specify all the desired tags on each task affecting an instance.
    default: false
    type: bool
    version_added: "2.9"
  ec2_classic:
    description:
      - Indicates that the elastic ip should be created in the EC2-Classic domain.  This is only needed when
        pre-allocating an EIP without associating it.  Otherwise, we will detect the correct EIP domain and allocate as
        needed to support the associated device.  This is false by default to reflect the fact that AWS is deprecating
        EC2-Classic in preference of VPC.  The old option of in_vpc is aliased to this option and the logic is inverted
        (if in_vpc is set to True, then ec2_classic is False. Likewise if in_vpc = False, then ec2-classic= True).
        The ec2_classic option was added in version 2.9, but its alias in_vpc was added in 1.4.  The version_added
        needs to be 1.4 to keep the sanity checks happy.
    required: false
    type: bool
    aliases: [ in_vpc ]
    version_added: "1.4"
extends_documentation_fragment:
    - aws
    - ec2
author:
   - "Rick Mendes (@rickmendes) <rmendes@illumina.com>"
   - "Mike Healey (@healem) <healem@gmail.com>"
notes:
   - There may be a delay between the time the EIP is assigned and when
     the cloud instance is reachable via the new address. Use wait_for and
     pause to delay further playbook execution until the instance is reachable,
     if necessary.
   - This module returns multiple changed statuses on disassociation or release.
     It returns an overall status based on any changes occurring. It also returns
     individual changed statuses for disassociation and release.
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: associate an elastic IP with an instance
  ec2_eip:
    name: myeip-finance
    device_id: i-1212f003
    ip: 93.184.216.119

- name: associate an elastic IP with a device
  ec2_eip:
    name: myeip-finance
    device_id: eni-c8ad70f3
    ip: 93.184.216.119
    tags:
      group: Finance

- name: associate an elastic IP with a device and allow reassociation
  ec2_eip:
    device_id: eni-c8ad70f3
    public_ip: 93.184.216.119
    allow_reassociation: yes

- name: disassociate an elastic IP from an instance
  ec2_eip:
    ip: 93.184.216.119
    state: absent

- name: disassociate an elastic IP from an instance using name
  ec2_eip:
    name: myeip-finance
    state: absent

- name: disassociate an elastic IP with a device
  ec2_eip:
    device_id: eni-c8ad70f3
    private_ip: 10.0.0.4
    ip: 93.184.216.119
    state: absent

- name: disassociate and release an elastic IP from an instance public_ip
  ec2_eip:
    release_on_disassociation: true
    public_ip: 93.184.216.119
    state: absent

- name: allocate a new elastic IP and associate it with an instance
  ec2_eip:
    name: myNewEIP
    device_id: i-1212f003

- name: allocate a new elastic IP without associating it to anything
  ec2_eip:
    name: myNewEIP
    state: present
  register: eip

- name: output the IP
  debug:
    msg: "Allocated IP is {{ eip.public_ip }}"

- name: provision new instances with ec2
  ec2:
    keypair: mykey
    instance_type: c1.medium
    image: ami-40603AD1
    wait: yes
    group: webserver
    count: 3
  register: ec2

- name: associate new elastic IPs with each of the instances
  ec2_eip:
    device_id: "{{ item }}"
  loop: "{{ ec2.instance_ids }}"

- name: allocate a new elastic IP inside a VPC in us-west-2
  ec2_eip:
    name: myeip-finance
    region: us-west-2
  register: eip

- name: Allocate an elastic ip for future use with an EC2-Classic instance
  ec2_eip:
    name: myeip-finance
    ec2_classic: yes
  register: eip

- name: output the IP
  debug:
    msg: "Allocated IP inside a VPC is {{ eip.public_ip }}"
'''

RETURN = '''
allocation_id:
  description: allocation_id of the elastic ip
  returned: on success
  type: str
  sample: eipalloc-51aa3a6c
name:
  description: name of the elastic ip
  returned: on success
  type: str
  sample: myElasticIp-29
public_ip:
  description: an elastic ip address
  returned: on success
  type: str
  sample: 52.88.159.209
tags:
  description: tags associated with the elastic ip
  returned: on success
  type: dict
  sample:
    key: value
    key2: value2
'''

try:
    import botocore.exceptions
except ImportError:
    pass  # Taken care of by ec2.HAS_BOTO3

from ansible.module_utils.ec2 import (ec2_argument_spec, compare_aws_tags,
                                      boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_tag_list)

from ansible.module_utils.aws.core import AnsibleAWSModule


class EIPException(Exception):
    pass


def is_instance(device_id):
    if device_id.startswith("i-"):
        return True
    else:
        return False


def associate_ip_and_device(ec2, address, private_ip_address, device_id, allow_reassociation, check_mode):
    if address_is_associated_with_device(ec2, address, device_id):
        return False

    # If we're in check mode, nothing else to do
    if not check_mode:
        if is_instance(device_id):
            if address["Domain"] == "vpc":
                res = ec2.associate_address(InstanceId=device_id,
                                            AllocationId=address["AllocationId"],
                                            PrivateIpAddress=private_ip_address,
                                            AllowReassociation=allow_reassociation)
            else:
                res = ec2.associate_address(InstanceId=device_id,
                                            PublicIp=address["PublicIp"],
                                            PrivateIpAddress=private_ip_address,
                                            AllowReassociation=allow_reassociation)
        else:
            res = ec2.associate_address(NetworkInterfaceId=device_id,
                                        AllocationId=address["AllocationId"],
                                        PrivateIpAddress=private_ip_address,
                                        AllowReassociation=allow_reassociation)

        if not res:
            raise EIPException('Association of eip {0} to {1} failed'.format(address["PublicIp"], device_id))

    return True


def disassociate_ip_and_device(ec2, address, device_id, check_mode):
    if not address_is_associated_with_device(ec2, address, device_id):
        return False

    # If we're in check mode, nothing else to do
    if not check_mode:
        if address["Domain"] == 'vpc':
            res = ec2.disassociate_address(AssociationId=address["AssociationId"])
        else:
            res = ec2.disassociate_address(PublicIp=address["PublicIp"])

        if not res:
            raise EIPException('Disassociation of eip {0} from {1} failed'.format(address["PublicIp"], device_id))

    return True


def find_address(ec2, name, public_ip, device_id):
    """ Find an existing Elastic IP address """
    args = {}
    filters = []
    if name:
        filters.append({"Name": 'tag:Name', "Values": [name]})

    if public_ip:
        args["PublicIps"] = [public_ip]
    elif device_id:
        if is_instance(device_id):
            filters.append({"Name": 'instance-id', "Values": [device_id]})
        else:
            filters.append({'Name': 'network-interface-id', "Values": [device_id]})

    if len(filters) > 0:
        args["Filters"] = filters
    elif len(filters) == 0 and public_ip is None:
        return None

    try:
        addresses = ec2.describe_addresses(**args)["Addresses"]
        if len(addresses) == 1:
            return addresses[0]
        elif len(addresses) > 1:
            msg = "Found more than one address using args {0}".format(args)
            msg += "Addresses found: {0}".format(addresses)
            raise EIPException(msg)
    except botocore.exceptions.ClientError as ce:
        # search finds nothing is handled as an error (400)
        if ce.response.get("Error", {}).get("Code", "") == "InvalidAddress.NotFound":
            return None
        else:
            raise


def address_is_associated_with_device(ec2, address, device_id):
    """ Check if the elastic IP is currently associated with the device """
    address = find_address(ec2, None, address["PublicIp"], None)
    if address:
        if is_instance(device_id):
            if "InstanceId" in address and address["InstanceId"] == device_id:
                return address
        else:
            if "NetworkInterfaceId" in address and address["NetworkInterfaceId"] == device_id:
                return address
    return False


def allocate_address(ec2, domain, reuse_existing_ip_allowed):
    """ Allocate a new elastic IP address (when needed) and return it """
    changed = False
    address = None
    if reuse_existing_ip_allowed:
        all_addresses = ec2.describe_addresses(Filters=[{'Name': 'domain', "Values": [domain]}])["Addresses"]

        if domain == 'vpc':
            unassociated_addresses = [a for a in all_addresses
                                      if not a["AssociationId"]]
        else:
            unassociated_addresses = [a for a in all_addresses
                                      if not a["InstanceId"]]
        if unassociated_addresses:
            address = unassociated_addresses[0]

    if not address:
        changed = True
        address = ec2.allocate_address(Domain=domain)
        # you can ask for a standard (ec2_classic) domain eip and get a vpc one back
        if address["Domain"] != domain:
            release_address(ec2, address, address["Domain"], False)
            raise EIPException('Attempt to allocate ' +
                               ("vpc (new style)" if domain == "vpc" else "ec2_classic") +
                               ' address failed.  Does your account allow this type?')

    return address, changed


def release_address(ec2, address, domain, check_mode):
    """ Release a previously allocated elastic IP address """

    # If we're in check mode, nothing else to do
    if not check_mode:
        if domain == "vpc":
            args = {"AllocationId": address["AllocationId"]}
        else:
            args = {"PublicIp": address["PublicIp"]}

        if not ec2.release_address(**args):
            raise EIPException('Release of address {0} failed'.format(address["PublicIp"]))

    return True


def determine_domain(ec2, device_id, ec2_classic):
    """ Determine device type and return the domain of the device (standard, vpc) """
    domain = "vpc"
    if device_id:
        if is_instance(device_id):
            # The device is an instance
            try:
                paginator = ec2.get_paginator('describe_instances')
                reservations = list(paginator.paginate(InstanceIds=[device_id]).search('Reservations[]'))
            except botocore.exceptions.ClientError as e:
                msg = "Failed to find instance with device_id {0}".format(device_id)
                msg += "Took error from AWS: {0}".format(str(e))
                raise EIPException(msg)

            if len(reservations) == 1:
                instances = reservations[0]["Instances"]
                if len(instances) == 1:
                    if "VpcId" not in instances[0]:
                        domain = "standard"
    else:
        if ec2_classic:
            domain = "standard"

    if ec2_classic and domain == "vpc":
        msg = "{0} is in the VPC domain, but you specified an EC2-Classic EIP.".format(device_id)
        msg += "Remove the ec2_classic parameter or specify an EC2-Classic device"
        raise EIPException(msg)
    else:
        return domain


def manage_tags(resource, resource_id, new_tags, purge_tags, connection, check_mode):
    """
        Align the tags on the resource to the desired tags specified in new_tags.  This method will add or optionally
        delete tags to bring the resources tags into compliance with new_tags.  This method supports check_mode.

        Note: Currently supports tags kept in the resource as "Tags" or "TagSet" - since AWS seems vary where it stores
        tags by resource type.

        :param resource: The boto3 resource as returned by calls like describe_instances
        :param resource_id: The resource id of the resource we are checking the tags on.  Example: vpc-3897234
        :param new_tags: ansible_dict of desired tags for the resource.  Example: { "key": "value", "key2": "value2" }
        :param connection: The ec2 connection
        :param purge_tags: Bool that indicates if we should delete existing tags that are not included in new_tags
        :param check_mode: Bool indicating if we are checking if something has changed, or if we should actually make
                           the change
        :return: bool: True if we changed any tags, False if no changes were made
        """
    changed = False

    if "Tags" in resource:
        old_tags = boto3_tag_list_to_ansible_dict(resource['Tags'])
    elif "TagSet" in resource:
        old_tags = boto3_tag_list_to_ansible_dict(resource['TagSet'])
    elif new_tags:
        old_tags = {}
    else:
        # No new tags and nothing in Tags
        return False

    tags_to_set, tags_to_delete = compare_aws_tags(
        old_tags, new_tags,
        purge_tags=purge_tags,
    )
    if tags_to_set:
        if not check_mode:
            connection.create_tags(
                Resources=[resource_id],
                Tags=ansible_dict_to_boto3_tag_list(tags_to_set)
            )
        changed |= True
    if tags_to_delete:
        if not check_mode:
            delete_with_current_values = dict((k, old_tags.get(k)) for k in tags_to_delete)
            connection.delete_tags(
                Resources=[resource_id],
                Tags=ansible_dict_to_boto3_tag_list(delete_with_current_values)
            )
        changed |= True
    return changed


def ensure_present(ec2, domain, address, private_ip_address, device_id, reuse_existing_ip_allowed,
                   allow_reassociation, check_mode, name, tags, purge_tags):
    changed_alloc = False
    changed_assoc = False
    changed_tags = False
    result = {}
    if not address:
        # Allocate an IP for instance since no public_ip was provided
        if check_mode:
            return {'changed': True}

        address, changed_alloc = allocate_address(ec2, domain, reuse_existing_ip_allowed)

    if device_id and address:
        # Associate address object (provided or allocated) with instance or network interface
        changed_assoc = associate_ip_and_device(
            ec2, address, private_ip_address, device_id, allow_reassociation, check_mode
        )

    if "AllocationId" in address:
        # Modify the tags, if needed
        changed_tags = manage_tags(address, address["AllocationId"], tags, purge_tags, ec2, check_mode)
        result["allocation_id"] = address["AllocationId"]

    if changed_alloc or changed_assoc or changed_tags:
        result["changed"] = True
        # Update the address object to get more complete info
        address = find_address(ec2, name, address["PublicIp"], device_id)
    else:
        result["changed"] = False

    if "AllocationId" in address:
        result["allocation_id"] = address["AllocationId"]

    if "Domain" in address and address["Domain"] == "standard":
        result["ec2_classic"] = True

    if "PublicIp" in address:
        result["public_ip"] = address["PublicIp"]

    if "Tags" in address:
        tags = boto3_tag_list_to_ansible_dict(address["Tags"])
        result["tags"] = tags
        if "Name" in tags:
            result["name"] = tags["Name"]

    return result


def ensure_absent(ec2, domain, address, device_id, release_on_disassociation, check_mode):
    if not address:
        return {'changed': False}

    changed_dis = False
    changed_rel = False
    if device_id:
        # disassociating address from instance
        changed_dis = disassociate_ip_and_device(ec2, address, device_id, check_mode)

    if release_on_disassociation or not device_id:
        # releasing address
        changed_rel = release_address(ec2, address, domain, check_mode)

    if changed_dis or changed_rel:
        result = {"changed": True}
    else:
        result = {"changed": False}

    result["disassociated"] = changed_dis
    result["released"] = changed_rel

    return result


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        device_id=dict(required=False, default=None, aliases=['instance_id']),
        public_ip=dict(required=False, aliases=['ip']),
        state=dict(required=False, default='present',
                   choices=['present', 'absent']),
        ec2_classic=dict(required=False, type='bool', default=False, aliases=['in_vpc']),
        reuse_existing_ip_allowed=dict(required=False, type='bool',
                                       default=False),
        release_on_disassociation=dict(required=False, type='bool', default=False),
        allow_reassociation=dict(type='bool', default=False),
        wait_timeout=dict(default=300, type='int'),
        private_ip_address=dict(required=False, default=None, type='str'),
        name=dict(required=False, default=None, type='str'),
        purge_tags=dict(required=False, default=False, type='bool'),
        tags=dict(required=False, default={}, type='dict')
    ))

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_by={
            'private_ip_address': ['device_id'],
        },
    )

    warnings = []

    ec2 = module.client('ec2')

    device_id = module.params.get('device_id')
    instance_id = module.params.get('instance_id')
    public_ip = module.params.get('public_ip')
    private_ip_address = module.params.get('private_ip_address')
    state = module.params.get('state')
    ec2_classic = module.params.get('ec2_classic')
    reuse_existing_ip_allowed = module.params.get('reuse_existing_ip_allowed')
    release_on_disassociation = module.params.get('release_on_disassociation')
    allow_reassociation = module.params.get('allow_reassociation')
    invpc = module.params.get('in_vpc')
    name = module.params.get('name')
    tags = module.params.get('tags')
    purge_tags = module.params.get('purge_tags')

    if name:
        tags["Name"] = name

    if invpc:
        warnings.append("Option in_vpc is no longer used.  Please use ec2_classic.")
        ec2_classic = not invpc

    if instance_id:
        warnings.append("Option instance_id is no longer used.  Please use device_id going forward")
        device_id = instance_id

    try:
        domain = determine_domain(ec2, device_id, ec2_classic)
        address = find_address(ec2, name, public_ip, device_id)

        if device_id and address and address["Domain"] != domain:
            msg = "Failed to associate address {0} with {1} ".format(address["PublicIp"], device_id)
            msg += "Cannot associate an address of domain {0} ".format(address["Domain"])
            msg += "with a device of domain {0}".format(domain)
            module.fail_json_aws(msg)

        if state == 'present':
            result = ensure_present(ec2, domain, address, private_ip_address, device_id, reuse_existing_ip_allowed,
                                    allow_reassociation, module.check_mode, name, tags, purge_tags)
        else:
            result = ensure_absent(ec2, domain, address, device_id, release_on_disassociation, module.check_mode)

    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(str(e))
    except EIPException as f:
        module.fail_json_aws(str(f))

    if instance_id:
        result['warnings'] = warnings
    module.exit_json(**result)


if __name__ == '__main__':
    main()
