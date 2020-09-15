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
  in_vpc:
    description:
      - Allocate an EIP inside a VPC or not. Required if specifying an ENI.
    default: 'no'
    type: bool
    version_added: "1.4"
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
  tag_name:
    description:
      - When reuse_existing_ip_allowed is true, supplement with this option to only reuse
        an Elastic IP if it is tagged with tag_name.
    default: 'no'
    version_added: "2.9"
  tag_value:
    description:
      - Supplements tag_name but also checks that the value of the tag provided in tag_name matches tag_value.
        matches the tag_value
    default: 'no'
    version_added: "2.9"
  public_ipv4_pool:
    description:
      - Allocates the new Elastic IP from the provided public IPv4 pool (BYOIP)
        only applies to newly allocated Elastic IPs, isn't validated when reuse_existing_ip_allowed is true.
    default: 'no'
    version_added: "2.9"
extends_documentation_fragment:
    - aws
    - ec2
author: "Rick Mendes (@rickmendes) <rmendes@illumina.com>"
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
    device_id: i-1212f003
    ip: 93.184.216.119

- name: associate an elastic IP with a device
  ec2_eip:
    device_id: eni-c8ad70f3
    ip: 93.184.216.119

- name: associate an elastic IP with a device and allow reassociation
  ec2_eip:
    device_id: eni-c8ad70f3
    public_ip: 93.184.216.119
    allow_reassociation: yes

- name: disassociate an elastic IP from an instance
  ec2_eip:
    device_id: i-1212f003
    ip: 93.184.216.119
    state: absent

- name: disassociate an elastic IP with a device
  ec2_eip:
    device_id: eni-c8ad70f3
    ip: 93.184.216.119
    state: absent

- name: allocate a new elastic IP and associate it with an instance
  ec2_eip:
    device_id: i-1212f003

- name: allocate a new elastic IP without associating it to anything
  ec2_eip:
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
    region: us-west-2
    in_vpc: yes
  register: eip

- name: output the IP
  debug:
    msg: "Allocated IP inside a VPC is {{ eip.public_ip }}"

- name: allocate eip - reuse unallocated ips (if found) with FREE tag
  ec2_eip:
    region: us-east-1
    in_vpc: yes
    reuse_existing_ip_allowed: yes
    tag_name: FREE

- name: allocate eip - reuse unallocted ips if tag reserved is nope
  ec2_eip:
    region: us-east-1
    in_vpc: yes
    reuse_existing_ip_allowed: yes
    tag_name: reserved
    tag_value: nope

- name: allocate new eip - from servers given ipv4 pool
  ec2_eip:
    region: us-east-1
    in_vpc: yes
    public_ipv4_pool: ipv4pool-ec2-0588c9b75a25d1a02

- name: allocate eip - from a given pool (if no free addresses where dev-servers tag is dynamic)
  ec2_eip:
    region: us-east-1
    in_vpc: yes
    reuse_existing_ip_allowed: yes
    tag_name: dev-servers
    public_ipv4_pool: ipv4pool-ec2-0588c9b75a25d1a02

- name: allocate eip from pool - check if tag reserved_for exists and value is our hostname
  ec2_eip:
    region: us-east-1
    in_vpc: yes
    reuse_existing_ip_allowed: yes
    tag_name: reserved_for
    tag_value: "{{ inventory_hostname }}"
    public_ipv4_pool: ipv4pool-ec2-0588c9b75a25d1a02
'''

RETURN = '''
allocation_id:
  description: allocation_id of the elastic ip
  returned: on success
  type: str
  sample: eipalloc-51aa3a6c
public_ip:
  description: an elastic ip address
  returned: on success
  type: str
  sample: 52.88.159.209
'''

try:
    import boto.exception
    from boto.ec2.address import Address
except ImportError:
    pass  # Taken care of by ec2.HAS_BOTO

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import HAS_BOTO, ec2_argument_spec, ec2_connect


class EIPException(Exception):
    pass


def associate_ip_and_device(ec2, address, private_ip_address, device_id, allow_reassociation, check_mode, is_instance=True):
    if address_is_associated_with_device(ec2, address, device_id, is_instance):
        return {'changed': False}

    # If we're in check mode, nothing else to do
    if not check_mode:
        if is_instance:
            if address.domain == "vpc":
                res = ec2.associate_address(device_id,
                                            allocation_id=address.allocation_id,
                                            private_ip_address=private_ip_address,
                                            allow_reassociation=allow_reassociation)
            else:
                res = ec2.associate_address(device_id,
                                            public_ip=address.public_ip,
                                            private_ip_address=private_ip_address,
                                            allow_reassociation=allow_reassociation)
        else:
            res = ec2.associate_address(network_interface_id=device_id,
                                        allocation_id=address.allocation_id,
                                        private_ip_address=private_ip_address,
                                        allow_reassociation=allow_reassociation)
        if not res:
            raise EIPException('association failed')

    return {'changed': True}


def disassociate_ip_and_device(ec2, address, device_id, check_mode, is_instance=True):
    if not address_is_associated_with_device(ec2, address, device_id, is_instance):
        return {'changed': False}

    # If we're in check mode, nothing else to do
    if not check_mode:
        if address.domain == 'vpc':
            res = ec2.disassociate_address(
                association_id=address.association_id)
        else:
            res = ec2.disassociate_address(public_ip=address.public_ip)

        if not res:
            raise EIPException('disassociation failed')

    return {'changed': True}


def _find_address_by_ip(ec2, public_ip):
    try:
        return ec2.get_all_addresses([public_ip])[0]
    except boto.exception.EC2ResponseError as e:
        if "Address '{0}' not found.".format(public_ip) not in e.message:
            raise


def _find_address_by_device_id(ec2, device_id, is_instance=True):
    if is_instance:
        addresses = ec2.get_all_addresses(None, {'instance-id': device_id})
    else:
        addresses = ec2.get_all_addresses(None, {'network-interface-id': device_id})
    if addresses:
        return addresses[0]


def find_address(ec2, public_ip, device_id, is_instance=True):
    """ Find an existing Elastic IP address """
    if public_ip:
        return _find_address_by_ip(ec2, public_ip)
    elif device_id and is_instance:
        return _find_address_by_device_id(ec2, device_id)
    elif device_id:
        return _find_address_by_device_id(ec2, device_id, is_instance=False)


def address_is_associated_with_device(ec2, address, device_id, is_instance=True):
    """ Check if the elastic IP is currently associated with the device """
    address = ec2.get_all_addresses(address.public_ip)
    if address:
        if is_instance:
            return address and address[0].instance_id == device_id
        else:
            return address and address[0].network_interface_id == device_id
    return False


def allocate_address(ec2, domain, reuse_existing_ip_allowed, check_mode, tag_dict=None, public_ipv4_pool=None):
    """ Allocate a new elastic IP address (when needed) and return it """
    if reuse_existing_ip_allowed:
        domain_filter = {'domain': domain or 'standard'}

        if tag_dict is not None:
            domain_filter.update(tag_dict)

        all_addresses = ec2.get_all_addresses(filters=domain_filter)

        if domain == 'vpc':
            unassociated_addresses = [a for a in all_addresses
                                      if not a.association_id]
        else:
            unassociated_addresses = [a for a in all_addresses
                                      if not a.instance_id]
        if unassociated_addresses:
            return unassociated_addresses[0], False

    if public_ipv4_pool:
        return allocate_address_from_pool(ec2, domain, check_mode, public_ipv4_pool), True

    return ec2.allocate_address(domain=domain), True


def release_address(ec2, address, check_mode):
    """ Release a previously allocated elastic IP address """

    # If we're in check mode, nothing else to do
    if not check_mode:
        if not address.release():
            raise EIPException('release failed')

    return {'changed': True}


def find_device(ec2, module, device_id, is_instance=True):
    """ Attempt to find the EC2 instance and return it """

    if is_instance:
        try:
            reservations = ec2.get_all_reservations(instance_ids=[device_id])
        except boto.exception.EC2ResponseError as e:
            module.fail_json(msg=str(e))

        if len(reservations) == 1:
            instances = reservations[0].instances
            if len(instances) == 1:
                return instances[0]
    else:
        try:
            interfaces = ec2.get_all_network_interfaces(network_interface_ids=[device_id])
        except boto.exception.EC2ResponseError as e:
            module.fail_json(msg=str(e))

        if len(interfaces) == 1:
            return interfaces[0]

    raise EIPException("could not find instance" + device_id)


def ensure_present(ec2, module, domain, address, private_ip_address, device_id,
                   reuse_existing_ip_allowed, allow_reassociation, check_mode, is_instance=True):
    changed = False

    # Return the EIP object since we've been given a public IP
    if not address:
        if check_mode:
            return {'changed': True}

        address, changed = allocate_address(ec2, domain, reuse_existing_ip_allowed, check_mode)

    if device_id:
        # Allocate an IP for instance since no public_ip was provided
        if is_instance:
            instance = find_device(ec2, module, device_id)
            if reuse_existing_ip_allowed:
                if instance.vpc_id and len(instance.vpc_id) > 0 and domain is None:
                    raise EIPException("You must set 'in_vpc' to true to associate an instance with an existing ip in a vpc")
            # Associate address object (provided or allocated) with instance
            assoc_result = associate_ip_and_device(ec2, address, private_ip_address, device_id, allow_reassociation,
                                                   check_mode)
        else:
            instance = find_device(ec2, module, device_id, is_instance=False)
            # Associate address object (provided or allocated) with instance
            assoc_result = associate_ip_and_device(ec2, address, private_ip_address, device_id, allow_reassociation,
                                                   check_mode, is_instance=False)

        if instance.vpc_id:
            domain = 'vpc'

        changed = changed or assoc_result['changed']

    return {'changed': changed, 'public_ip': address.public_ip, 'allocation_id': address.allocation_id}


def ensure_absent(ec2, address, device_id, check_mode, is_instance=True):
    if not address:
        return {'changed': False}

    # disassociating address from instance
    if device_id:
        if is_instance:
            return disassociate_ip_and_device(ec2, address, device_id,
                                              check_mode)
        else:
            return disassociate_ip_and_device(ec2, address, device_id,
                                              check_mode, is_instance=False)
    # releasing address
    else:
        return release_address(ec2, address, check_mode)


def allocate_address_from_pool(ec2, domain, check_mode, public_ipv4_pool):
    # type: (EC2Connection, str, bool, str) -> Address
    """ Overrides boto's allocate_address function to support BYOIP """
    params = {}

    if domain is not None:
        params['Domain'] = domain

    if public_ipv4_pool is not None:
        ec2.APIVersion = "2016-11-15"  # Workaround to force amazon to accept this attribute
        params['PublicIpv4Pool'] = public_ipv4_pool

    if check_mode:
        params['DryRun'] = 'true'

    return ec2.get_object('AllocateAddress', params, Address, verb='POST')


def generate_tag_dict(module, tag_name, tag_value):
    # type: (AnsibleModule, str, str) -> Optional[Dict]
    """ Generates a dictionary to be passed as a filter to Amazon """
    if tag_name and not tag_value:
        if tag_name.startswith('tag:'):
            tag_name = tag_name.strip('tag:')
        return {'tag-key': tag_name}

    elif tag_name and tag_value:
        if not tag_name.startswith('tag:'):
            tag_name = 'tag:' + tag_name
        return {tag_name: tag_value}

    elif tag_value and not tag_name:
        module.fail_json(msg="parameters are required together: ('tag_name', 'tag_value')")


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        device_id=dict(required=False, aliases=['instance_id']),
        public_ip=dict(required=False, aliases=['ip']),
        state=dict(required=False, default='present',
                   choices=['present', 'absent']),
        in_vpc=dict(required=False, type='bool', default=False),
        reuse_existing_ip_allowed=dict(required=False, type='bool',
                                       default=False),
        release_on_disassociation=dict(required=False, type='bool', default=False),
        allow_reassociation=dict(type='bool', default=False),
        wait_timeout=dict(default=300, type='int'),
        private_ip_address=dict(),
        tag_name=dict(),
        tag_value=dict(),
        public_ipv4_pool=dict()
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_by={
            'private_ip_address': ['device_id'],
        },
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    ec2 = ec2_connect(module)

    device_id = module.params.get('device_id')
    instance_id = module.params.get('instance_id')
    public_ip = module.params.get('public_ip')
    private_ip_address = module.params.get('private_ip_address')
    state = module.params.get('state')
    in_vpc = module.params.get('in_vpc')
    domain = 'vpc' if in_vpc else None
    reuse_existing_ip_allowed = module.params.get('reuse_existing_ip_allowed')
    release_on_disassociation = module.params.get('release_on_disassociation')
    allow_reassociation = module.params.get('allow_reassociation')
    tag_name = module.params.get('tag_name')
    tag_value = module.params.get('tag_value')
    public_ipv4_pool = module.params.get('public_ipv4_pool')

    if instance_id:
        warnings = ["instance_id is no longer used, please use device_id going forward"]
        is_instance = True
        device_id = instance_id
    else:
        if device_id and device_id.startswith('i-'):
            is_instance = True
        elif device_id:
            if device_id.startswith('eni-') and not in_vpc:
                module.fail_json(msg="If you are specifying an ENI, in_vpc must be true")
            is_instance = False

    tag_dict = generate_tag_dict(module, tag_name, tag_value)

    try:
        if device_id:
            address = find_address(ec2, public_ip, device_id, is_instance=is_instance)
        else:
            address = find_address(ec2, public_ip, None)

        if state == 'present':
            if device_id:
                result = ensure_present(ec2, module, domain, address, private_ip_address, device_id,
                                        reuse_existing_ip_allowed, allow_reassociation,
                                        module.check_mode, is_instance=is_instance)
            else:
                if address:
                    changed = False
                else:
                    address, changed = allocate_address(ec2, domain, reuse_existing_ip_allowed, module.check_mode, tag_dict, public_ipv4_pool)
                result = {'changed': changed, 'public_ip': address.public_ip, 'allocation_id': address.allocation_id}
        else:
            if device_id:
                disassociated = ensure_absent(ec2, address, device_id, module.check_mode, is_instance=is_instance)

                if release_on_disassociation and disassociated['changed']:
                    released = release_address(ec2, address, module.check_mode)
                    result = {'changed': True, 'disassociated': disassociated, 'released': released}
                else:
                    result = {'changed': disassociated['changed'], 'disassociated': disassociated, 'released': {'changed': False}}
            else:
                released = release_address(ec2, address, module.check_mode)
                result = {'changed': released['changed'], 'disassociated': {'changed': False}, 'released': released}

    except (boto.exception.EC2ResponseError, EIPException) as e:
        module.fail_json(msg=str(e))

    if instance_id:
        result['warnings'] = warnings
    module.exit_json(**result)


if __name__ == '__main__':
    main()
