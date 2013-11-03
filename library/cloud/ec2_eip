#!/usr/bin/python
DOCUMENTATION = '''
---
module: ec2_eip
short_description: associate an EC2 elastic IP with an instance.
description:
    - This module associates AWS EC2 elastic IP addresses with instances
version_added: 1.4
options:
  instance_id:
    description:
      - The EC2 instance id
    required: false
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
  ec2_url:
    description:
      - URL to use to connect to EC2-compatible cloud (by default the module will use EC2 endpoints)
    required: false
    default: null
    aliases: [ EC2_URL ]
  ec2_access_key:
    description:
      - EC2 access key. If not specified then the EC2_ACCESS_KEY environment variable is used.
    required: false
    default: null
    aliases: [ EC2_ACCESS_KEY ]
  ec2_secret_key:
    description:
      - EC2 secret key. If not specified then the EC2_SECRET_KEY environment variable is used.
    required: false
    default: null
    aliases: [ EC2_SECRET_KEY ]
  region:
    description:
      - the EC2 region to use
    required: false
    default: null
    aliases: [ ec2_region ]
  in_vpc:
    description:
      - allocate an EIP inside a VPC or not
    required: false
    default: false
    version_added: "1.4"
requirements: [ "boto" ]
author: Lorin Hochstein <lorin@nimbisservices.com>
notes:
   - This module will return C(public_ip) on success, which will contain the
     public IP address associated with the instance.
   - There may be a delay between the time the Elastic IP is assigned and when
     the cloud instance is reachable via the new address. Use wait_for and pause
     to delay further playbook execution until the instance is reachable, if
     necessary.
'''

EXAMPLES = '''
- name: associate an elastic IP with an instance
  ec2_eip: instance_id=i-1212f003 ip=93.184.216.119

- name: disassociate an elastic IP from an instance
  ec2_eip: instance_id=i-1212f003 ip=93.184.216.119 state=absent

- name: allocate a new elastic IP and associate it with an instance
  ec2_eip: instance_id=i-1212f003

- name: allocate a new elastic IP without associating it to anything
  ec2_eip:
  register: eip
- name: output the IP
  debug: msg="Allocated IP is {{ eip.public_ip }}"

- name: provision new instances with ec2
  ec2: keypair=mykey instance_type=c1.medium image=emi-40603AD1 wait=yes group=webserver count=3
  register: ec2
- name: associate new elastic IPs with each of the instances
  ec2_eip: "instance_id={{ item }}"
  with_items: ec2.instance_ids

- name: allocate a new elastic IP inside a VPC in us-west-2
  ec2_eip: region=us-west-2 in_vpc=yes
  register: eip
- name: output the IP
  debug: msg="Allocated IP inside a VPC is {{ eip.public_ip }}"
'''

try:
    import boto.ec2
except ImportError:
    boto_found = False
else:
    boto_found = True


def connect(ec2_url, ec2_access_key, ec2_secret_key, region, module):

    """ Return an ec2 connection"""
    # allow environment variables to be used if ansible vars aren't set
    if not ec2_url and 'EC2_URL' in os.environ:
        ec2_url = os.environ['EC2_URL']
    if not ec2_secret_key and 'EC2_SECRET_KEY' in os.environ:
        ec2_secret_key = os.environ['EC2_SECRET_KEY']
    if not ec2_access_key and 'EC2_ACCESS_KEY' in os.environ:
        ec2_access_key = os.environ['EC2_ACCESS_KEY']

    # If we have a region specified, connect to its endpoint.
    if region:
        try:
            ec2 = boto.ec2.connect_to_region(region,
                                        aws_access_key_id=ec2_access_key,
                                        aws_secret_access_key=ec2_secret_key)
        except boto.exception.NoAuthHandlerFound, e:
            module.fail_json(msg = str(" %s %s %s " % (region, ec2_access_key,
                                                       ec2_secret_key)))
    # Otherwise, no region so we fallback to the old connection method
    else:
        try:
            if ec2_url: # if we have an URL set, connect to the specified endpoint
                ec2 = boto.connect_ec2_endpoint(ec2_url, ec2_access_key, ec2_secret_key)
            else: # otherwise it's Amazon.
                ec2 = boto.connect_ec2(ec2_access_key, ec2_secret_key)
        except boto.exception.NoAuthHandlerFound, e:
            module.fail_json(msg = str(e))
    return ec2


def associate_ip_and_instance(ec2, address, instance_id, module):
    if ip_is_associated_with_instance(ec2, address.public_ip, instance_id, module):
        module.exit_json(changed=False, public_ip=address.public_ip)

    # If we're in check mode, nothing else to do
    if module.check_mode:
        module.exit_json(changed=True)

    try:
        if address.domain == "vpc":
            res = ec2.associate_address(instance_id, allocation_id=address.allocation_id)
        else:
            res = ec2.associate_address(instance_id, public_ip=address.public_ip)
    except boto.exception.EC2ResponseError, e:
        module.fail_json(msg=str(e))
    
    if res:
        module.exit_json(changed=True, public_ip=address.public_ip)
    else:
        module.fail_json(msg="association failed")


def disassociate_ip_and_instance(ec2, address, instance_id, module):
    if not ip_is_associated_with_instance(ec2, address.public_ip, instance_id, module):
        module.exit_json(changed=False, public_ip=address.public_ip)

    # If we're in check mode, nothing else to do
    if module.check_mode:
        module.exit_json(changed=True)

    try:
        if address.domain == "vpc":
            res = ec2.disassociate_address(association_id=address.association_id)
        else:
            res = ec2.disassociate_address(public_ip=address.public_ip)
    except boto.exception.EC2ResponseError, e:
        module.fail_json(msg=str(e))

    if res:
        module.exit_json(changed=True)
    else:
        module.fail_json(msg="disassociation failed")


def find_address(ec2, public_ip, module):
    """ Find an existing Elastic IP address """
    
    try:
        addresses = ec2.get_all_addresses([public_ip])
    except boto.exception.EC2ResponseError, e:
        module.fail_json(msg=str(e.message))
        
    return addresses[0]


def ip_is_associated_with_instance(ec2, public_ip, instance_id, module):
    """ Check if the elastic IP is currently associated with the instance """
    address = find_address(ec2, public_ip, module)
    if address:
        return address.instance_id == instance_id
    else:
        return False


def allocate_address(ec2, domain, module):
    """ Allocate a new elastic IP address and return it """
    # If we're in check mode, nothing else to do
    if module.check_mode:
        module.exit_json(change=True)

    address = ec2.allocate_address(domain=domain)
    return address


def release_address(ec2, public_ip, module):
    """ Release a previously allocated elastic IP address """
    
    address = find_address(ec2, public_ip, module)
    
    # If we're in check mode, nothing else to do
    if module.check_mode:
        module.exit_json(change=True)
    
    res = address.release()    
    if res:
        module.exit_json(changed=True)
    else:
        module.fail_json(msg="release failed")


def find_instance(ec2, instance_id, module):
    """ Attempt to find the EC2 instance and return it """
    
    try:
        reservations = ec2.get_all_reservations(instance_ids=[instance_id])
    except boto.exception.EC2ResponseError, e:
        module.fail_json(msg=str(e))
    
    if len(reservations) == 1:
        instances = reservations[0].instances
        if len(instances) == 1:
            return instances[0]
    
    module.fail_json(msg="could not find instance" + instance_id)
    

def main():
    module = AnsibleModule(
        argument_spec = dict(
            instance_id = dict(required=False),
            public_ip = dict(required=False, aliases= ['ip']),
            state = dict(required=False, default='present',
                         choices=['present', 'absent']),
            ec2_url = dict(required=False, aliases=['EC2_URL']),
            ec2_secret_key = dict(required=False, aliases=['EC2_SECRET_KEY'], no_log=True),
            ec2_access_key = dict(required=False, aliases=['EC2_ACCESS_KEY']),
            region = dict(required=False, aliases=['ec2_region']),
            in_vpc = dict(required=False, choices=BOOLEANS, default=False),
        ),
        supports_check_mode=True
    )

    if not boto_found:
        module.fail_json(msg="boto is required")

    ec2_url, ec2_access_key, ec2_secret_key, region = get_ec2_creds(module)

    ec2 = connect(ec2_url,
                  ec2_access_key,
                  ec2_secret_key,
                  region,
                  module)

    instance_id = module.params.get('instance_id')
    public_ip = module.params.get('public_ip')
    state = module.params.get('state')
    in_vpc = module.params.get('in_vpc')
    domain  = "vpc" if in_vpc else None

    if state == 'present':
        if public_ip is None:
            if instance_id is None:
                address = allocate_address(ec2, domain, module)
                module.exit_json(changed=True, public_ip=address.public_ip)
            else:
                # Determine if the instance is inside a VPC or not
                instance = find_instance(ec2, instance_id, module)
                if instance.vpc_id != None:
                    domain = "vpc"
                address = allocate_address(ec2, domain, module)
        else:
            address = find_address(ec2, public_ip, module)
        associate_ip_and_instance(ec2, address, instance_id, module)
    else:
        if instance_id is None:
            release_address(ec2, public_ip, module)
        else:
            address = find_address(ec2, public_ip, module)
            disassociate_ip_and_instance(ec2, address, instance_id, module)



# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
