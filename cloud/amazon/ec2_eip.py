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
module: ec2_eip
short_description: associate an EC2 elastic IP with an instance.
description:
    - This module associates AWS EC2 elastic IP addresses with instances
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
      - The elastic IP address to associate with the instance.
      - If absent, allocate a new address
    required: false
  state:
    description:
      - If present, associate the IP with the instance.
      - If absent, disassociate the IP with the instance.
    required: false
    choices: ['present', 'absent']
    default: present
  in_vpc:
    description:
      - allocate an EIP inside a VPC or not
    required: false
    default: false
    version_added: "1.4"
  reuse_existing_ip_allowed:
    description:
      - Reuse an EIP that is not associated to an instance (when available), instead of allocating a new one.
    required: false
    default: false
    version_added: "1.6"
  release_on_disassociation:
    description:
      - whether or not to automatically release the EIP when it is disassociated
    required: false
    default: false
    version_added: "2.0"
extends_documentation_fragment:
    - aws
    - ec2
author: "Rick Mendes (@rickmendes) <rmendes@illumina.com>"
notes:
   - This module will return C(public_ip) on success, which will contain the
     public IP address associated with the instance.
   - There may be a delay between the time the Elastic IP is assigned and when
     the cloud instance is reachable via the new address. Use wait_for and
     pause to delay further playbook execution until the instance is reachable,
     if necessary.
   - This module returns multiple changed statuses on disassociation or release.
     It returns an overall status based on any changes occuring. It also returns
     individual changed statuses for disassociation and release.
'''

EXAMPLES = '''
- name: associate an elastic IP with an instance
  ec2_eip: device_id=i-1212f003 ip=93.184.216.119
- name: associate an elastic IP with a device
  ec2_eip: device_id=eni-c8ad70f3 ip=93.184.216.119
- name: disassociate an elastic IP from an instance
  ec2_eip: device_id=i-1212f003 ip=93.184.216.119 state=absent
- name: disassociate an elastic IP with a device
  ec2_eip: device_id=eni-c8ad70f3 ip=93.184.216.119 state=absent
- name: allocate a new elastic IP and associate it with an instance
  ec2_eip: device_id=i-1212f003
- name: allocate a new elastic IP without associating it to anything
  action: ec2_eip
  register: eip
- name: output the IP
  debug: msg="Allocated IP is {{ eip.public_ip }}"
- name: another way of allocating an elastic IP without associating it to anything
  ec2_eip: state='present'
- name: provision new instances with ec2
  ec2: keypair=mykey instance_type=c1.medium image=emi-40603AD1 wait=yes'''
''' group=webserver count=3
  register: ec2
- name: associate new elastic IPs with each of the instances
  ec2_eip: "device_id={{ item }}"
  with_items: ec2.instance_ids
- name: allocate a new elastic IP inside a VPC in us-west-2
  ec2_eip: region=us-west-2 in_vpc=yes
  register: eip
- name: output the IP
  debug: msg="Allocated IP inside a VPC is {{ eip.public_ip }}"
'''

try:
    import boto.ec2
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


class EIPException(Exception):
    pass


def associate_ip_and_device(ec2, address, device_id, check_mode, isinstance=True):
    if address_is_associated_with_device(ec2, address, device_id, isinstance):
        return {'changed': False}

    # If we're in check mode, nothing else to do
    if not check_mode:
        if isinstance:
            if address.domain == "vpc":
                res = ec2.associate_address(device_id, allocation_id=address.allocation_id)
            else:
                res = ec2.associate_address(device_id, public_ip=address.public_ip)
        else:
            res = ec2.associate_address(network_interface_id=device_id, allocation_id=address.allocation_id)
        if not res:
            raise EIPException('association failed')

    return {'changed': True}


def disassociate_ip_and_device(ec2, address, device_id, check_mode, isinstance=True):
    if not address_is_associated_with_device(ec2, address, device_id, isinstance):
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
        if "Address '{}' not found.".format(public_ip) not in e.message:
            raise


def _find_address_by_device_id(ec2, device_id, isinstance=True):
    if isinstance:
        addresses = ec2.get_all_addresses(None, {'instance-id': device_id})
    else:
        addresses = ec2.get_all_addresses(None, {'network-interface-id': device_id})
    if addresses:
        return addresses[0]


def find_address(ec2, public_ip, device_id, isinstance=True):
    """ Find an existing Elastic IP address """
    if public_ip:
        return _find_address_by_ip(ec2, public_ip)
    elif device_id and isinstance:
        return _find_address_by_device_id(ec2, device_id)
    elif device_id:
        return _find_address_by_device_id(ec2, device_id, isinstance=False)


def address_is_associated_with_device(ec2, address, device_id, isinstance=True):
    """ Check if the elastic IP is currently associated with the device """
    address = ec2.get_all_addresses(address.public_ip)
    if address:
        if isinstance:
            return address and address[0].instance_id == device_id
        else:
            return address and address[0].network_interface_id == device_id
    return False


def allocate_address(ec2, domain, reuse_existing_ip_allowed):
    """ Allocate a new elastic IP address (when needed) and return it """
    if reuse_existing_ip_allowed:
        domain_filter = {'domain': domain or 'standard'}
        all_addresses = ec2.get_all_addresses(filters=domain_filter)

        if domain == 'vpc':
            unassociated_addresses = [a for a in all_addresses
                                      if not a.association_id]
        else:
            unassociated_addresses = [a for a in all_addresses
                                      if not a.instance_id]
        if unassociated_addresses:
            return unassociated_addresses[0]

    return ec2.allocate_address(domain=domain)


def release_address(ec2, address, check_mode):
    """ Release a previously allocated elastic IP address """

    # If we're in check mode, nothing else to do
    if not check_mode:
        if not address.release():
            EIPException('release failed')

    return {'changed': True}


def find_device(ec2, device_id, isinstance=True):
    """ Attempt to find the EC2 instance and return it """

    if isinstance:
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


def ensure_present(ec2, domain, address, device_id,
                   reuse_existing_ip_allowed, check_mode, isinstance=True):
    changed = False

    # Return the EIP object since we've been given a public IP
    if not address:
        if check_mode:
            return {'changed': True}

        address = allocate_address(ec2, domain, reuse_existing_ip_allowed)
        changed = True

    if device_id:
        # Allocate an IP for instance since no public_ip was provided
        if isinstance:
            instance = find_device(ec2, device_id)
            if reuse_existing_ip_allowed:
                if len(instance.vpc_id) > 0 and domain is None:
                    raise EIPException("You must set 'in_vpc' to true to associate an instance with an existing ip in a vpc")
            # Associate address object (provided or allocated) with instance
            assoc_result = associate_ip_and_device(ec2, address, device_id,
                                                 check_mode)
        else:
            instance = find_device(ec2, device_id, isinstance=False)
            # Associate address object (provided or allocated) with instance
            assoc_result = associate_ip_and_device(ec2, address, device_id,
                                                 check_mode, isinstance=False)

        if instance.vpc_id:
            domain = 'vpc'

        changed = changed or assoc_result['changed']

    return {'changed': changed, 'public_ip': address.public_ip, 'allocation_id': address.allocation_id}


def ensure_absent(ec2, domain, address, device_id, check_mode, isinstance=True):
    if not address:
        return {'changed': False}

    # disassociating address from instance
    if device_id:
        if isinstance:
            return disassociate_ip_and_device(ec2, address, device_id,
                                                check_mode)
        else:
            return disassociate_ip_and_device(ec2, address, device_id,
                                                check_mode, isinstance=False)
    # releasing address
    else:
        return release_address(ec2, address, check_mode)


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
        wait_timeout=dict(default=300),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    ec2 = ec2_connect(module)

    device_id = module.params.get('device_id')
    instance_id = module.params.get('instance_id')
    public_ip = module.params.get('public_ip')
    state = module.params.get('state')
    in_vpc = module.params.get('in_vpc')
    domain = 'vpc' if in_vpc else None
    reuse_existing_ip_allowed = module.params.get('reuse_existing_ip_allowed')
    release_on_disassociation = module.params.get('release_on_disassociation')

    if instance_id:
        warnings = ["instance_id is no longer used, please use device_id going forward"]
        is_instance = True
        device_id = instance_id
    else:
        if device_id and device_id.startswith('i-'):
            is_instance = True
        elif device_id:
            is_instance = False

    try:
        if device_id:
            address = find_address(ec2, public_ip, device_id, isinstance=is_instance)
        else:
            address = False

        if state == 'present':
            if device_id:
                result = ensure_present(ec2, domain, address, device_id,
                                    reuse_existing_ip_allowed,
                                    module.check_mode, isinstance=is_instance)
            else:
                address = allocate_address(ec2, domain, reuse_existing_ip_allowed)
                result = {'changed': True, 'public_ip': address.public_ip, 'allocation_id': address.allocation_id}
        else:
            if device_id:
                disassociated = ensure_absent(ec2, domain, address, device_id, module.check_mode, isinstance=is_instance)

                if release_on_disassociation and disassociated['changed']:
                    released = release_address(ec2, address, module.check_mode)
                    result = {'changed': True, 'disassociated': disassociated, 'released': released}
                else:
                    result = {'changed': disassociated['changed'], 'disassociated': disassociated, 'released': {'changed': False}}
            else:
                address = find_address(ec2, public_ip, None)
                released = release_address(ec2, address, module.check_mode)
                result = {'changed': released['changed'], 'disassociated': {'changed': False}, 'released': released}

    except (boto.exception.EC2ResponseError, EIPException) as e:
        module.fail_json(msg=str(e))

    if instance_id:
        result['warnings'] = warnings
    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *  # noqa
from ansible.module_utils.ec2 import *  # noqa

if __name__ == '__main__':
    main()
