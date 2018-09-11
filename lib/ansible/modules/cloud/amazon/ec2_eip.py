#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}


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
    version_added: "1.4"
  reuse_existing_ip_allowed:
    description:
      - Reuse an EIP that is not associated to a device (when available), instead of allocating a new one.
    default: 'no'
    version_added: "1.6"
  release_on_disassociation:
    description:
      - whether or not to automatically release the EIP when it is disassociated
    default: 'no'
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
    version_added: "2.5"
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
requirements:
  - botocore
  - boto3
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
  with_items: "{{ ec2.instance_ids }}"

- name: allocate a new elastic IP inside a VPC in us-west-2
  ec2_eip:
    region: us-west-2
    in_vpc: yes
  register: eip

- name: output the IP
  debug:
    msg: "Allocated IP inside a VPC is {{ eip.public_ip }}"
'''

RETURN = '''
allocation_id:
  description: allocation_id of the elastic ip
  returned: on success
  type: string
  sample: eipalloc-51aa3a6c
public_ip:
  description: an elastic ip address
  returned: on success
  type: string
  sample: 52.88.159.209
'''

try:
    import botocore
except ImportError:
    pass # Handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (
    AWSRetry,
    boto3_conn,
    ec2_argument_spec,
    get_aws_connection_info,
    camel_dict_to_snake_dict,
    boto3_tag_list_to_ansible_dict,
    ansible_dict_to_boto3_filter_list,
    ansible_dict_to_boto3_tag_list,
    compare_aws_tags
)
from ansible.module_utils._text import to_native

DEVICE_TYPE_ENI = 'eni'
DEVICE_TYPE_INSTANCE = 'instance'


class EIPException(Exception):
    pass


class AnsibleEc2Eip(object):

    def __init__(self, module=None, results=None):
        self._module = module
        self._results = results
        self._connection = self._module.client('ec2')
        self._check_mode = self._module.check_mode
        self.warnings = []

        self.public_ip = self._module.params.get('public_ip')

        self.in_vpc = self._module.params.get('in_vpc')
        self.domain = 'vpc' if self.in_vpc else None
        self.device_type = DEVICE_TYPE_ENI
        self.device_id = self._module.params.get('device_id')
        instance_id = self._module.params.get('instance_id')
        if instance_id:
            self.warnings.append("instance_id is no longer used, please use device_id going forward")
            self.device_type = DEVICE_TYPE_INSTANCE
            self.device_id = instance_id
        else:
            if self.device_id and self.device_id.startswith('i-'):
                self.device_type = DEVICE_TYPE_INSTANCE
            elif self.device_id:
                if self.device_id.startswith('eni-') and not self.in_vpc:
                    self._module.fail_json(msg="If you are specifying an ENI, in_vpc must be true")

        self.eip = self._get_eip()

    def _get_eip(self, allocation_id=None):
        """ Find an existing Elastic IP address """
        self._module.debug('Searching Address {}'.format({
            'allocation_id': allocation_id,
            'public_ip': self.public_ip,
            'device_id': self.device_id,
            'device_type': self.device_type
        }))
        find_params = dict()
        if allocation_id:
            find_params['AllocationIds'] = [allocation_id]
        elif self.public_ip:
            find_params['PublicIps'] = [self.public_ip]
        elif self.device_id and self.device_type == DEVICE_TYPE_INSTANCE:
            find_params['Filters'] = ansible_dict_to_boto3_filter_list({'instance-id': self.device_id})
        elif self.device_id and self.device_type == DEVICE_TYPE_ENI:
            find_params['Filters'] = ansible_dict_to_boto3_filter_list({
                'network-interface-id': self.device_id
            })

        eips = []
        try:
            eip_response = self._connection.describe_addresses(**find_params)
            eips = eip_response.get('Addresses', [])
        except botocore.exceptions.ClientError as e:
            self._module.fail_json_aws(e)

        eip = None
        if len(eips) > 1:
            self._module.fail_json(
                msg='More than one Elastic IP Address was returned with filters {0}, aborting'.format(find_params))
        elif eips:
            eip = camel_dict_to_snake_dict(eips[0])
        return eip

    def _get_device(self):
        devices = []
        try:
            if self.device_type == DEVICE_TYPE_INSTANCE:
                devices_response = self._connection.describe_instances(InstanceIds=[self.device_id])
                for reservation in devices_response['Reservations']:
                    devices = devices + reservation['Instances']
            elif self.device_type == DEVICE_TYPE_ENI:
                devices_response = self._connection.describe_network_interfaces(NetworkInterfaceIds=[self.device_id])
                devices = devices_response['NetworkInterfaces']
        except botocore.exceptions.ClientError as e:
            self._module.fail_json_aws(e)

        device = None
        if len(devices) > 1:
            self._module.fail_json_aws(
                None,
                msg='More than one device was returned with id, aborting'.format(self.device_id))
        elif devices:
            device = camel_dict_to_snake_dict(devices[0])
        return device

    def _eip_is_associated_with_device(self):
        result = False

        if self.eip:
            if self.device_type == DEVICE_TYPE_INSTANCE:
                result = self.eip.get('instance_id', None) == self.device_id
            else:
                result = self.eip.get('network_interface_id', None) == self.device_id

        return result

    def _associate_eip_and_device(self):
        if self._eip_is_associated_with_device():
            return self.eip['association_id']

        # Default value for check mode
        association_id = '#new_association'
        device = self._get_device()

        if self.device_type == DEVICE_TYPE_INSTANCE and self._module.params.get('reuse_existing_ip_allowed'):
            if device['vpc_id'] and not self.in_vpc:
                self._module.fail_json(
                    msg="You must set 'in_vpc' to true to associate an instance with an existing ip in a vpc")

        self._results['changed'] = True

        # If we're in check mode, nothing else to do
        if not self._check_mode:
            try:
                common_association_params = dict(
                    AllowReassociation=self._module.params.get('allow_reassociation'),
                )
                association_response = None
                if self._module.params.get('private_ip_address'):
                    common_association_params['PrivateIpAddress'] = self._module.params.get('private_ip_address')
                if self.device_type == DEVICE_TYPE_INSTANCE:
                    if self.eip['domain'] == "vpc":
                        association_response = self._connection.associate_address(
                            InstanceId=self.device_id,
                            AllocationId=self.eip['allocation_id'],
                            **common_association_params
                        )
                    else:
                        association_response = self._connection.associate_address(
                            InstanceId=self.device_id,
                            PublicIp=self.public_ip,
                            **common_association_params
                        )
                    self.eip['domain'] = "vpc"
                else:
                    association_response = self._connection.associate_address(
                        NetworkInterfaceId=self.device_id,
                        AllocationId=self.eip['allocation_id'],
                        **common_association_params
                    )
                association_id = association_response.get('AssociationId')
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self._module.fail_json_aws(e, msg='Error while associating Elastic IP')

        return association_id

    def _get_available_eip(self):
        eip = None
        if self.public_ip:
            # Should already be found
            return None

        domain = 'vpc' if self.in_vpc else 'standard'
        find_params = {'domain': domain}
        try:
            eips_response = self._connection.describe_addresses(
                Filters=ansible_dict_to_boto3_filter_list(find_params),
            )
            for candidate in eips_response.get('Addresses', []):
                if self.in_vpc:
                    if not candidate.get('AssociationId', None):
                        eip = camel_dict_to_snake_dict(candidate)
                        break
                else:
                    if not candidate.get('InstanceId', None):
                        eip = camel_dict_to_snake_dict(candidate)
                        break
        except botocore.exceptions.ClientError as e:
            self._module.fail_json_aws(e, 'Error while searching for available address')

        if eip:
            self._module.debug('Found candidate Address : {}'.format(eip['allocation_id']))
        else:
            self._module.debug('No candidate Address found')

        return eip

    def _disassociate_eip_and_device(self):
        if not self._eip_is_associated_with_device():
            return

        self._results['changed'] = True

        if not self._check_mode:
            try:
                if self.eip['domain'] == "vpc":
                    self._connection.disassociate_address(
                        AllocationId=self.eip['allocation_id'],
                    )
                else:
                    self._connection.disassociate_address(
                        PublicIp=self.public_ip,
                    )
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self._module.fail_json_aws(e, msg='Error while disassociating Elastic IP')

    def _create_eip(self):
        eip = None

        domain = 'standard'
        if self.in_vpc:
            domain = 'vpc'
        try:
            eip_response = self._connection.allocate_address(Domain=domain)
            eip = self._get_eip(allocation_id=eip_response['AllocationId'])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self._module.fail_json_aws(e, msg='Error while allocating Elastic IP')

        return eip

    def _release_eip(self):
        if not self._module.params.get('release_on_disassociation'):
            return
        if not self.eip:
            return

        self._results['changed'] = True

        if not self._check_mode:
            try:
                if self.eip['domain'] == "vpc":
                    self._connection.release_address(
                        AllocationId=self.eip['allocation_id'],
                    )
                else:
                    self._connection.release_address(
                        PublicIp=self.public_ip,
                    )
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self._module.fail_json_aws(e, msg='Error while releasing Elastic IP')

    def ensure_present(self):
        # Return the EIP object since we've been given a public IP
        if not self.eip:
            if self._check_mode:
                return
            lonely_eip = self._get_available_eip()
            if lonely_eip:
                self._module.debug('Using found address {}'.format(lonely_eip.get('allocation_id', None)))
                self.eip = lonely_eip
            else:
                self._module.debug('Create address')
                self.eip = self._create_eip()
        self._associate_eip_and_device()
        self._results['allocation_id'] = self.eip.get('allocation_id', None)
        self._results['public_ip'] = self.eip['public_ip']

    def ensure_absent(self):
        if not self.eip:
            return

        self._disassociate_eip_and_device()

        self._release_eip()

    def process(self):
        private_ip_address = self._module.params.get('private_ip_address')
        state = self._module.params.get('state', 'present')

        # Parameter checks
        if private_ip_address is not None and self.device_id is None:
            self._module.fail_json(msg="parameters are required together: ('device_id', 'private_ip_address')")

        if state == 'present':
            self.ensure_present()
        else:
            self.ensure_absent()

        if self.warnings:
            self._results['warnings'] = self.warnings


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
        wait_timeout=dict(default=300),
        private_ip_address=dict(required=False, default=None, type='str')
    ))

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    results = dict(
        changed=False
    )

    eip_manager = AnsibleEc2Eip(module=module, results=results)
    eip_manager.process()

    module.exit_json(**results)


if __name__ == '__main__':
    main()
