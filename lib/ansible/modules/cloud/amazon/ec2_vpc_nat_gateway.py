#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_vpc_nat_gateway
short_description: Manage AWS VPC NAT Gateways.
description:
  - Ensure the state of AWS VPC NAT Gateways based on their id, allocation and subnet ids.
version_added: "2.2"
requirements: [boto3, botocore]
options:
  state:
    description:
      - Ensure NAT Gateway is present or absent.
    default: "present"
    choices: ["present", "absent"]
  nat_gateway_id:
    description:
      - The id AWS dynamically allocates to the NAT Gateway on creation.
        This is required when the absent option is present.
  subnet_id:
    description:
      - The id of the subnet to create the NAT Gateway in. This is required
        with the present option.
  allocation_id:
    description:
      - The id of the elastic IP allocation. If this is not passed and the
        eip_address is not passed. An EIP is generated for this NAT Gateway.
  eip_address:
    description:
      - The elastic IP address of the EIP you want attached to this NAT Gateway.
        If this is not passed and the allocation_id is not passed,
        an EIP is generated for this NAT Gateway.
  if_exist_do_not_create:
    description:
      - if a NAT Gateway exists already in the subnet_id, then do not create a new one.
    required: false
    default: false
  release_eip:
    description:
      - Deallocate the EIP from the VPC.
      - Option is only valid with the absent state.
      - You should use this with the wait option. Since you can not release an address while a delete operation is happening.
    default: 'yes'
  wait:
    description:
      - Wait for operation to complete before returning.
    default: 'no'
  wait_timeout:
    description:
      - How many seconds to wait for an operation to complete before timing out.
    default: 300
  client_token:
    description:
      - Optional unique token to be used during create to ensure idempotency.
        When specifying this option, ensure you specify the eip_address parameter
        as well otherwise any subsequent runs will fail.
author:
  - "Allen Sanabria (@linuxdynasty)"
  - "Jon Hadfield (@jonhadfield)"
  - "Karen Cheng(@Etherdaemon)"
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create new nat gateway with client token.
  ec2_vpc_nat_gateway:
    state: present
    subnet_id: subnet-12345678
    eip_address: 52.1.1.1
    region: ap-southeast-2
    client_token: abcd-12345678
  register: new_nat_gateway

- name: Create new nat gateway using an allocation-id.
  ec2_vpc_nat_gateway:
    state: present
    subnet_id: subnet-12345678
    allocation_id: eipalloc-12345678
    region: ap-southeast-2
  register: new_nat_gateway

- name: Create new nat gateway, using an EIP address  and wait for available status.
  ec2_vpc_nat_gateway:
    state: present
    subnet_id: subnet-12345678
    eip_address: 52.1.1.1
    wait: yes
    region: ap-southeast-2
  register: new_nat_gateway

- name: Create new nat gateway and allocate new EIP.
  ec2_vpc_nat_gateway:
    state: present
    subnet_id: subnet-12345678
    wait: yes
    region: ap-southeast-2
  register: new_nat_gateway

- name: Create new nat gateway and allocate new EIP if a nat gateway does not yet exist in the subnet.
  ec2_vpc_nat_gateway:
    state: present
    subnet_id: subnet-12345678
    wait: yes
    region: ap-southeast-2
    if_exist_do_not_create: true
  register: new_nat_gateway

- name: Delete nat gateway using discovered nat gateways from facts module.
  ec2_vpc_nat_gateway:
    state: absent
    region: ap-southeast-2
    wait: yes
    nat_gateway_id: "{{ item.NatGatewayId }}"
    release_eip: yes
  register: delete_nat_gateway_result
  with_items: "{{ gateways_to_remove.result }}"

- name: Delete nat gateway and wait for deleted status.
  ec2_vpc_nat_gateway:
    state: absent
    nat_gateway_id: nat-12345678
    wait: yes
    wait_timeout: 500
    region: ap-southeast-2

- name: Delete nat gateway and release EIP.
  ec2_vpc_nat_gateway:
    state: absent
    nat_gateway_id: nat-12345678
    release_eip: yes
    wait: yes
    wait_timeout: 300
    region: ap-southeast-2
'''

RETURN = '''
create_time:
  description: The ISO 8601 date time formatin UTC.
  returned: In all cases.
  type: string
  sample: "2016-03-05T05:19:20.282000+00:00'"
nat_gateway_id:
  description: id of the VPC NAT Gateway
  returned: In all cases.
  type: string
  sample: "nat-0d1e3a878585988f8"
subnet_id:
  description: id of the Subnet
  returned: In all cases.
  type: string
  sample: "subnet-12345"
state:
  description: The current state of the NAT Gateway.
  returned: In all cases.
  type: string
  sample: "available"
vpc_id:
  description: id of the VPC.
  returned: In all cases.
  type: string
  sample: "vpc-12345"
nat_gateway_addresses:
  description: List of dictionairies containing the public_ip, network_interface_id, private_ip, and allocation_id.
  returned: In all cases.
  type: string
  sample: [
      {
          'public_ip': '52.52.52.52',
          'network_interface_id': 'eni-12345',
          'private_ip': '10.0.0.100',
          'allocation_id': 'eipalloc-12345'
      }
  ]
'''

import datetime
import random
import time

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (ec2_argument_spec, get_aws_connection_info, boto3_conn,
                                      camel_dict_to_snake_dict, HAS_BOTO3)


DRY_RUN_GATEWAYS = [
    {
        "nat_gateway_id": "nat-123456789",
        "subnet_id": "subnet-123456789",
        "nat_gateway_addresses": [
            {
                "public_ip": "55.55.55.55",
                "network_interface_id": "eni-1234567",
                "private_ip": "10.0.0.102",
                "allocation_id": "eipalloc-1234567"
            }
        ],
        "state": "available",
        "create_time": "2016-03-05T05:19:20.282000+00:00",
        "vpc_id": "vpc-12345678"
    }
]

DRY_RUN_ALLOCATION_UNCONVERTED = {
    'Addresses': [
        {
            'PublicIp': '55.55.55.55',
            'Domain': 'vpc',
            'AllocationId': 'eipalloc-1234567'
        }
    ]
}

DRY_RUN_MSGS = 'DryRun Mode:'


def get_nat_gateways(client, subnet_id=None, nat_gateway_id=None,
                     states=None, check_mode=False):
    """Retrieve a list of NAT Gateways
    Args:
        client (botocore.client.EC2): Boto3 client

    Kwargs:
        subnet_id (str): The subnet_id the nat resides in.
        nat_gateway_id (str): The Amazon nat id.
        states (list): States available (pending, failed, available, deleting, and deleted)
            default=None

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> subnet_id = 'subnet-12345678'
        >>> get_nat_gateways(client, subnet_id)
        [
            true,
            "",
            {
                "nat_gateway_id": "nat-123456789",
                "subnet_id": "subnet-123456789",
                "nat_gateway_addresses": [
                    {
                        "public_ip": "55.55.55.55",
                        "network_interface_id": "eni-1234567",
                        "private_ip": "10.0.0.102",
                        "allocation_id": "eipalloc-1234567"
                    }
                ],
                "state": "deleted",
                "create_time": "2016-03-05T00:33:21.209000+00:00",
                "delete_time": "2016-03-05T00:36:37.329000+00:00",
                "vpc_id": "vpc-12345678"
            }

    Returns:
        Tuple (bool, str, list)
    """
    params = dict()
    err_msg = ""
    gateways_retrieved = False
    existing_gateways = list()
    if not states:
        states = ['available', 'pending']
    if nat_gateway_id:
        params['NatGatewayIds'] = [nat_gateway_id]
    else:
        params['Filter'] = [
            {
                'Name': 'subnet-id',
                'Values': [subnet_id]
            },
            {
                'Name': 'state',
                'Values': states
            }
        ]

    try:
        if not check_mode:
            gateways = client.describe_nat_gateways(**params)['NatGateways']
            if gateways:
                for gw in gateways:
                    existing_gateways.append(camel_dict_to_snake_dict(gw))
            gateways_retrieved = True
        else:
            gateways_retrieved = True
            if nat_gateway_id:
                if DRY_RUN_GATEWAYS[0]['nat_gateway_id'] == nat_gateway_id:
                    existing_gateways = DRY_RUN_GATEWAYS
            elif subnet_id:
                if DRY_RUN_GATEWAYS[0]['subnet_id'] == subnet_id:
                    existing_gateways = DRY_RUN_GATEWAYS
            err_msg = '{0} Retrieving gateways'.format(DRY_RUN_MSGS)

    except botocore.exceptions.ClientError as e:
        err_msg = str(e)

    return gateways_retrieved, err_msg, existing_gateways


def wait_for_status(client, wait_timeout, nat_gateway_id, status,
                    check_mode=False):
    """Wait for the NAT Gateway to reach a status
    Args:
        client (botocore.client.EC2): Boto3 client
        wait_timeout (int): Number of seconds to wait, until this timeout is reached.
        nat_gateway_id (str): The Amazon nat id.
        status (str): The status to wait for.
            examples. status=available, status=deleted

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> subnet_id = 'subnet-12345678'
        >>> allocation_id = 'eipalloc-12345678'
        >>> wait_for_status(client, subnet_id, allocation_id)
        [
            true,
            "",
            {
                "nat_gateway_id": "nat-123456789",
                "subnet_id": "subnet-1234567",
                "nat_gateway_addresses": [
                    {
                        "public_ip": "55.55.55.55",
                        "network_interface_id": "eni-1234567",
                        "private_ip": "10.0.0.102",
                        "allocation_id": "eipalloc-12345678"
                    }
                ],
                "state": "deleted",
                "create_time": "2016-03-05T00:33:21.209000+00:00",
                "delete_time": "2016-03-05T00:36:37.329000+00:00",
                "vpc_id": "vpc-12345677"
            }
        ]

    Returns:
        Tuple (bool, str, dict)
    """
    polling_increment_secs = 5
    wait_timeout = time.time() + wait_timeout
    status_achieved = False
    nat_gateway = dict()
    states = ['pending', 'failed', 'available', 'deleting', 'deleted']
    err_msg = ""

    while wait_timeout > time.time():
        try:
            gws_retrieved, err_msg, nat_gateways = (
                get_nat_gateways(
                    client, nat_gateway_id=nat_gateway_id,
                    states=states, check_mode=check_mode
                )
            )
            if gws_retrieved and nat_gateways:
                nat_gateway = nat_gateways[0]
                if check_mode:
                    nat_gateway['state'] = status

                if nat_gateway.get('state') == status:
                    status_achieved = True
                    break

                elif nat_gateway.get('state') == 'failed':
                    err_msg = nat_gateway.get('failure_message')
                    break

                elif nat_gateway.get('state') == 'pending':
                    if 'failure_message' in nat_gateway:
                        err_msg = nat_gateway.get('failure_message')
                        status_achieved = False
                        break

            else:
                time.sleep(polling_increment_secs)

        except botocore.exceptions.ClientError as e:
            err_msg = str(e)

    if not status_achieved:
        err_msg = "Wait time out reached, while waiting for results"

    return status_achieved, err_msg, nat_gateway


def gateway_in_subnet_exists(client, subnet_id, allocation_id=None,
                             check_mode=False):
    """Retrieve all NAT Gateways for a subnet.
    Args:
        subnet_id (str): The subnet_id the nat resides in.

    Kwargs:
        allocation_id (str): The EIP Amazon identifier.
            default = None

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> subnet_id = 'subnet-1234567'
        >>> allocation_id = 'eipalloc-1234567'
        >>> gateway_in_subnet_exists(client, subnet_id, allocation_id)
        (
            [
                {
                    "nat_gateway_id": "nat-123456789",
                    "subnet_id": "subnet-123456789",
                    "nat_gateway_addresses": [
                        {
                            "public_ip": "55.55.55.55",
                            "network_interface_id": "eni-1234567",
                            "private_ip": "10.0.0.102",
                            "allocation_id": "eipalloc-1234567"
                        }
                    ],
                    "state": "deleted",
                    "create_time": "2016-03-05T00:33:21.209000+00:00",
                    "delete_time": "2016-03-05T00:36:37.329000+00:00",
                    "vpc_id": "vpc-1234567"
                }
            ],
            False
        )

    Returns:
        Tuple (list, bool)
    """
    allocation_id_exists = False
    gateways = []
    states = ['available', 'pending']
    gws_retrieved, _, gws = (
        get_nat_gateways(
            client, subnet_id, states=states, check_mode=check_mode
        )
    )
    if not gws_retrieved:
        return gateways, allocation_id_exists
    for gw in gws:
        for address in gw['nat_gateway_addresses']:
            if allocation_id:
                if address.get('allocation_id') == allocation_id:
                    allocation_id_exists = True
                    gateways.append(gw)
            else:
                gateways.append(gw)

    return gateways, allocation_id_exists


def get_eip_allocation_id_by_address(client, eip_address, check_mode=False):
    """Release an EIP from your EIP Pool
    Args:
        client (botocore.client.EC2): Boto3 client
        eip_address (str): The Elastic IP Address of the EIP.

    Kwargs:
        check_mode (bool): if set to true, do not run anything and
            falsify the results.

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> eip_address = '52.87.29.36'
        >>> get_eip_allocation_id_by_address(client, eip_address)
        'eipalloc-36014da3'

    Returns:
        Tuple (str, str)
    """
    params = {
        'PublicIps': [eip_address],
    }
    allocation_id = None
    err_msg = ""
    try:
        if not check_mode:
            allocations = client.describe_addresses(**params)['Addresses']
            if len(allocations) == 1:
                allocation = allocations[0]
            else:
                allocation = None
        else:
            dry_run_eip = (
                DRY_RUN_ALLOCATION_UNCONVERTED['Addresses'][0]['PublicIp']
            )
            if dry_run_eip == eip_address:
                allocation = DRY_RUN_ALLOCATION_UNCONVERTED['Addresses'][0]
            else:
                allocation = None
        if allocation:
            if allocation.get('Domain') != 'vpc':
                err_msg = (
                    "EIP {0} is a non-VPC EIP, please allocate a VPC scoped EIP"
                    .format(eip_address)
                )
            else:
                allocation_id = allocation.get('AllocationId')
        else:
            err_msg = (
                "EIP {0} does not exist".format(eip_address)
            )

    except botocore.exceptions.ClientError as e:
        err_msg = str(e)

    return allocation_id, err_msg


def allocate_eip_address(client, check_mode=False):
    """Release an EIP from your EIP Pool
    Args:
        client (botocore.client.EC2): Boto3 client

    Kwargs:
        check_mode (bool): if set to true, do not run anything and
            falsify the results.

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> allocate_eip_address(client)
        True

    Returns:
        Tuple (bool, str)
    """
    ip_allocated = False
    new_eip = None
    err_msg = ''
    params = {
        'Domain': 'vpc',
    }
    try:
        if check_mode:
            ip_allocated = True
            random_numbers = (
                ''.join(str(x) for x in random.sample(range(0, 9), 7))
            )
            new_eip = 'eipalloc-{0}'.format(random_numbers)
        else:
            new_eip = client.allocate_address(**params)['AllocationId']
            ip_allocated = True
        err_msg = 'eipalloc id {0} created'.format(new_eip)

    except botocore.exceptions.ClientError as e:
        err_msg = str(e)

    return ip_allocated, err_msg, new_eip


def release_address(client, allocation_id, check_mode=False):
    """Release an EIP from your EIP Pool
    Args:
        client (botocore.client.EC2): Boto3 client
        allocation_id (str): The eip Amazon identifier.

    Kwargs:
        check_mode (bool): if set to true, do not run anything and
            falsify the results.

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> allocation_id = "eipalloc-123456"
        >>> release_address(client, allocation_id)
        True

    Returns:
        Boolean, string
    """
    err_msg = ''
    if check_mode:
        return True, ''

    ip_released = False
    try:
        client.describe_addresses(AllocationIds=[allocation_id])
    except botocore.exceptions.ClientError as e:
        # IP address likely already released
        # Happens with gateway in 'deleted' state that
        # still lists associations
        return True, str(e)
    try:
        client.release_address(AllocationId=allocation_id)
        ip_released = True
    except botocore.exceptions.ClientError as e:
        err_msg = str(e)

    return ip_released, err_msg


def create(client, subnet_id, allocation_id, client_token=None,
           wait=False, wait_timeout=0, if_exist_do_not_create=False,
           check_mode=False):
    """Create an Amazon NAT Gateway.
    Args:
        client (botocore.client.EC2): Boto3 client
        subnet_id (str): The subnet_id the nat resides in.
        allocation_id (str): The eip Amazon identifier.

    Kwargs:
        if_exist_do_not_create (bool): if a nat gateway already exists in this
            subnet, than do not create another one.
            default = False
        wait (bool): Wait for the nat to be in the deleted state before returning.
            default = False
        wait_timeout (int): Number of seconds to wait, until this timeout is reached.
            default = 0
        client_token (str):
            default = None

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> subnet_id = 'subnet-1234567'
        >>> allocation_id = 'eipalloc-1234567'
        >>> create(client, subnet_id, allocation_id, if_exist_do_not_create=True, wait=True, wait_timeout=500)
        [
            true,
            "",
            {
                "nat_gateway_id": "nat-123456789",
                "subnet_id": "subnet-1234567",
                "nat_gateway_addresses": [
                    {
                        "public_ip": "55.55.55.55",
                        "network_interface_id": "eni-1234567",
                        "private_ip": "10.0.0.102",
                        "allocation_id": "eipalloc-1234567"
                    }
                ],
                "state": "deleted",
                "create_time": "2016-03-05T00:33:21.209000+00:00",
                "delete_time": "2016-03-05T00:36:37.329000+00:00",
                "vpc_id": "vpc-1234567"
            }
        ]

    Returns:
        Tuple (bool, str, list)
    """
    params = {
        'SubnetId': subnet_id,
        'AllocationId': allocation_id
    }
    request_time = datetime.datetime.utcnow()
    changed = False
    success = False
    token_provided = False
    err_msg = ""

    if client_token:
        token_provided = True
        params['ClientToken'] = client_token

    try:
        if not check_mode:
            result = camel_dict_to_snake_dict(client.create_nat_gateway(**params)["NatGateway"])
        else:
            result = DRY_RUN_GATEWAYS[0]
            result['create_time'] = datetime.datetime.utcnow()
            result['nat_gateway_addresses'][0]['allocation_id'] = allocation_id
            result['subnet_id'] = subnet_id

        success = True
        changed = True
        create_time = result['create_time'].replace(tzinfo=None)
        if token_provided and (request_time > create_time):
            changed = False
        elif wait:
            success, err_msg, result = (
                wait_for_status(
                    client, wait_timeout, result['nat_gateway_id'], 'available',
                    check_mode=check_mode
                )
            )
            if success:
                err_msg = (
                    'NAT gateway {0} created'.format(result['nat_gateway_id'])
                )

    except botocore.exceptions.ClientError as e:
        if "IdempotentParameterMismatch" in e.message:
            err_msg = (
                'NAT Gateway does not support update and token has already been provided: ' + str(e)
            )
        else:
            err_msg = str(e)
        success = False
        changed = False
        result = None

    return success, changed, err_msg, result


def pre_create(client, subnet_id, allocation_id=None, eip_address=None,
               if_exist_do_not_create=False, wait=False, wait_timeout=0,
               client_token=None, check_mode=False):
    """Create an Amazon NAT Gateway.
    Args:
        client (botocore.client.EC2): Boto3 client
        subnet_id (str): The subnet_id the nat resides in.

    Kwargs:
        allocation_id (str): The EIP Amazon identifier.
            default = None
        eip_address (str): The Elastic IP Address of the EIP.
            default = None
        if_exist_do_not_create (bool): if a nat gateway already exists in this
            subnet, than do not create another one.
            default = False
        wait (bool): Wait for the nat to be in the deleted state before returning.
            default = False
        wait_timeout (int): Number of seconds to wait, until this timeout is reached.
            default = 0
        client_token (str):
            default = None

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> subnet_id = 'subnet-w4t12897'
        >>> allocation_id = 'eipalloc-36014da3'
        >>> pre_create(client, subnet_id, allocation_id, if_exist_do_not_create=True, wait=True, wait_timeout=500)
        [
            true,
            "",
            {
                "nat_gateway_id": "nat-03835afb6e31df79b",
                "subnet_id": "subnet-w4t12897",
                "nat_gateway_addresses": [
                    {
                        "public_ip": "52.87.29.36",
                        "network_interface_id": "eni-5579742d",
                        "private_ip": "10.0.0.102",
                        "allocation_id": "eipalloc-36014da3"
                    }
                ],
                "state": "deleted",
                "create_time": "2016-03-05T00:33:21.209000+00:00",
                "delete_time": "2016-03-05T00:36:37.329000+00:00",
                "vpc_id": "vpc-w68571b5"
            }
        ]

    Returns:
        Tuple (bool, bool, str, list)
    """
    success = False
    changed = False
    err_msg = ""
    results = list()

    if not allocation_id and not eip_address:
        existing_gateways, allocation_id_exists = (
            gateway_in_subnet_exists(client, subnet_id, check_mode=check_mode)
        )

        if len(existing_gateways) > 0 and if_exist_do_not_create:
            success = True
            changed = False
            results = existing_gateways[0]
            err_msg = (
                'NAT Gateway {0} already exists in subnet_id {1}'
                .format(
                    existing_gateways[0]['nat_gateway_id'], subnet_id
                )
            )
            return success, changed, err_msg, results
        else:
            success, err_msg, allocation_id = (
                allocate_eip_address(client, check_mode=check_mode)
            )
            if not success:
                return success, 'False', err_msg, dict()

    elif eip_address or allocation_id:
        if eip_address and not allocation_id:
            allocation_id, err_msg = (
                get_eip_allocation_id_by_address(
                    client, eip_address, check_mode=check_mode
                )
            )
            if not allocation_id:
                success = False
                changed = False
                return success, changed, err_msg, dict()

        existing_gateways, allocation_id_exists = (
            gateway_in_subnet_exists(
                client, subnet_id, allocation_id, check_mode=check_mode
            )
        )
        if len(existing_gateways) > 0 and (allocation_id_exists or if_exist_do_not_create):
            success = True
            changed = False
            results = existing_gateways[0]
            err_msg = (
                'NAT Gateway {0} already exists in subnet_id {1}'
                .format(
                    existing_gateways[0]['nat_gateway_id'], subnet_id
                )
            )
            return success, changed, err_msg, results

    success, changed, err_msg, results = create(
        client, subnet_id, allocation_id, client_token,
        wait, wait_timeout, if_exist_do_not_create, check_mode=check_mode
    )

    return success, changed, err_msg, results


def remove(client, nat_gateway_id, wait=False, wait_timeout=0,
           release_eip=False, check_mode=False):
    """Delete an Amazon NAT Gateway.
    Args:
        client (botocore.client.EC2): Boto3 client
        nat_gateway_id (str): The Amazon nat id.

    Kwargs:
        wait (bool): Wait for the nat to be in the deleted state before returning.
        wait_timeout (int): Number of seconds to wait, until this timeout is reached.
        release_eip (bool): Once the nat has been deleted, you can deallocate the eip from the vpc.

    Basic Usage:
        >>> client = boto3.client('ec2')
        >>> nat_gw_id = 'nat-03835afb6e31df79b'
        >>> remove(client, nat_gw_id, wait=True, wait_timeout=500, release_eip=True)
        [
            true,
            "",
            {
                "nat_gateway_id": "nat-03835afb6e31df79b",
                "subnet_id": "subnet-w4t12897",
                "nat_gateway_addresses": [
                    {
                        "public_ip": "52.87.29.36",
                        "network_interface_id": "eni-5579742d",
                        "private_ip": "10.0.0.102",
                        "allocation_id": "eipalloc-36014da3"
                    }
                ],
                "state": "deleted",
                "create_time": "2016-03-05T00:33:21.209000+00:00",
                "delete_time": "2016-03-05T00:36:37.329000+00:00",
                "vpc_id": "vpc-w68571b5"
            }
        ]

    Returns:
        Tuple (bool, str, list)
    """
    params = {
        'NatGatewayId': nat_gateway_id
    }
    success = False
    changed = False
    err_msg = ""
    results = list()
    states = ['pending', 'available']
    try:
        exist, _, gw = (
            get_nat_gateways(
                client, nat_gateway_id=nat_gateway_id,
                states=states, check_mode=check_mode
            )
        )
        if exist and len(gw) == 1:
            results = gw[0]
            if not check_mode:
                client.delete_nat_gateway(**params)

            allocation_id = (
                results['nat_gateway_addresses'][0]['allocation_id']
            )
            changed = True
            success = True
            err_msg = (
                'NAT gateway {0} is in a deleting state. Delete was successful'
                .format(nat_gateway_id)
            )

            if wait:
                status_achieved, err_msg, results = (
                    wait_for_status(
                        client, wait_timeout, nat_gateway_id, 'deleted',
                        check_mode=check_mode
                    )
                )
                if status_achieved:
                    err_msg = (
                        'NAT gateway {0} was deleted successfully'
                        .format(nat_gateway_id)
                    )

    except botocore.exceptions.ClientError as e:
        err_msg = str(e)

    if release_eip:
        eip_released, eip_err = (
            release_address(client, allocation_id, check_mode)
        )
        if not eip_released:
            err_msg = (
                "{0}: Failed to release EIP {1}: {2}"
                .format(err_msg, allocation_id, eip_err)
            )
            success = False

    return success, changed, err_msg, results


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            subnet_id=dict(type='str'),
            eip_address=dict(type='str'),
            allocation_id=dict(type='str'),
            if_exist_do_not_create=dict(type='bool', default=False),
            state=dict(default='present', choices=['present', 'absent']),
            wait=dict(type='bool', default=False),
            wait_timeout=dict(type='int', default=320, required=False),
            release_eip=dict(type='bool', default=False),
            nat_gateway_id=dict(type='str'),
            client_token=dict(type='str'),
        )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['allocation_id', 'eip_address']
        ],
        required_if=[['state', 'absent', ['nat_gateway_id']],
                     ['state', 'present', ['subnet_id']]]
    )

    # Validate Requirements
    if not HAS_BOTO3:
        module.fail_json(msg='botocore/boto3 is required.')

    state = module.params.get('state').lower()
    check_mode = module.check_mode
    subnet_id = module.params.get('subnet_id')
    allocation_id = module.params.get('allocation_id')
    eip_address = module.params.get('eip_address')
    nat_gateway_id = module.params.get('nat_gateway_id')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')
    release_eip = module.params.get('release_eip')
    client_token = module.params.get('client_token')
    if_exist_do_not_create = module.params.get('if_exist_do_not_create')

    try:
        region, ec2_url, aws_connect_kwargs = (
            get_aws_connection_info(module, boto3=True)
        )
        client = (
            boto3_conn(
                module, conn_type='client', resource='ec2',
                region=region, endpoint=ec2_url, **aws_connect_kwargs
            )
        )
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Boto3 Client Error - " + str(e.msg))

    changed = False
    err_msg = ''

    if state == 'present':
        success, changed, err_msg, results = (
            pre_create(
                client, subnet_id, allocation_id, eip_address,
                if_exist_do_not_create, wait, wait_timeout,
                client_token, check_mode=check_mode
            )
        )
    else:
        success, changed, err_msg, results = (
            remove(
                client, nat_gateway_id, wait, wait_timeout, release_eip,
                check_mode=check_mode
            )
        )

    if not success:
        module.fail_json(
            msg=err_msg, success=success, changed=changed
        )
    else:
        module.exit_json(
            msg=err_msg, success=success, changed=changed, **results
        )


if __name__ == '__main__':
    main()
