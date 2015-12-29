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
module: ec2_vpc_peer
short_description: create, delete, accept, and reject VPC peering connections between two VPCs.
description:
  - Read the AWS documentation for VPC Peering Connections
    U(http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/vpc-peering.html)
version_added: "2.1"    
options:
  vpc_id:
    description:
      - VPC id of the requesting VPC.
    required: false
  peer_vpc_id:
    description:
      - VPC id of the accepting VPC.
    required: false
  peer_owner_id:
    description:
      - The AWS account number for cross account peering.
    required: false
  state:
    description:
      - Create, delete, accept, reject a peering connection.
    required: false
    default: present
    choices: ['present', 'absent', 'accept', 'reject']
  region:
    description:
      - The AWS region to use.  Must be specified if ec2_url is not used. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: false
    default: null
    aliases: ['aws_region', 'ec2_region']
  profile:
    description:
      - boto3 profile name.
    required: false
    default: None
  aws_secret_key:
    description:
      - AWS secret key. If not set then the value of the AWS_SECRET_KEY environment variable is used.
    required: false
    default: None
    aliases: ['ec2_secret_key', 'secret_key']
  aws_access_key:
    description:
      - AWS access key. If not set then the value of the AWS_ACCESS_KEY environment variable is used.
    required: false
    default: None
    aliases: ['ec2_access_key', 'access_key']
author: Mike Mochan(@mmochan)
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Complete example to create and accept a local peering connection.
- name: Create local account VPC peering Connection
  ec2_vpc_peer:
    region: ap-southeast-2
    vpc_id: vpc-12345678
    peer_vpc_id: vpc-87654321
    state: present
  register: vpc_peer

- name: Accept local VPC peering request
  ec2_vpc_peer:
    region: ap-southeast-2
    peering_id: "{{ vpc_peer.peering_id }}"
    state: accept
  register: action_peer

# Complete example to delete a local peering connection.
- name: Create local account VPC peering Connection
  ec2_vpc_peer:
    region: ap-southeast-2
    vpc_id: vpc-12345678
    peer_vpc_id: vpc-87654321
    state: present
  register: vpc_peer

- name: delete a local VPC peering Connection
  ec2_vpc_peer:
    region: ap-southeast-2
    peering_id: "{{ vpc_peer.peering_id }}"
    state: absent
  register: vpc_peer

  # Complete example to create and accept a cross account peering connection.
- name: Create cross account VPC peering Connection
  ec2_vpc_peer:
    region: ap-southeast-2
    vpc_id: vpc-12345678
    peer_vpc_id: vpc-87654321
    peer_vpc_id: vpc-ce26b7ab
    peer_owner_id: 123456789102
    state: present
  register: vpc_peer

- name: Accept peering connection from remote account
  ec2_vpc_peer:
    region: ap-southeast-2
    peering_id: "{{ vpc_peer.peering_id }}"
    profile: bot03_profile_for_cross_account
    state: accept
  register: vpc_peer

# Complete example to create and reject a local peering connection.
- name: Create local account VPC peering Connection
  ec2_vpc_peer:
    region: ap-southeast-2
    vpc_id: vpc-12345678
    peer_vpc_id: vpc-87654321
    state: present
  register: vpc_peer

- name: Reject a local VPC peering Connection
  ec2_vpc_peer:
    region: ap-southeast-2
    peering_id: "{{ vpc_peer.peering_id }}"
    state: reject

# Complete example to create and accept a cross account peering connection.
- name: Create cross account VPC peering Connection
  ec2_vpc_peer:
    region: ap-southeast-2
    vpc_id: vpc-12345678
    peer_vpc_id: vpc-87654321
    peer_vpc_id: vpc-ce26b7ab
    peer_owner_id: 123456789102
    state: present
  register: vpc_peer

- name: Accept a cross account VPC peering connection request
  ec2_vpc_peer:
    region: ap-southeast-2
    peering_id: "{{ vpc_peer.peering_id }}"
    profile: bot03_profile_for_cross_account
    state: accept


# Complete example to create and reject a cross account peering connection.
- name: Create cross account VPC peering Connection
  ec2_vpc_peer:
    region: ap-southeast-2
    vpc_id: vpc-12345678
    peer_vpc_id: vpc-87654321
    peer_vpc_id: vpc-ce26b7ab
    peer_owner_id: 123456789102
    state: present
  register: vpc_peer

- name: Reject a cross account VPC peering Connection
  ec2_vpc_peer:
    region: ap-southeast-2
    peering_id: "{{ vpc_peer.peering_id }}"
    profile: bot03_profile_for_cross_account
    state: reject

'''
RETURN = '''
task:
  description: details about the tast that was started
  type: complex
  sample: "TODO: include sample"
'''

try:
    import json
    import datetime
    import boto
    import botocore
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

import q


def describe_peering_connections(vpc_id, peer_vpc_id, client):
    result = client.describe_vpc_peering_connections(Filters=[
        {'Name': 'requester-vpc-info.vpc-id', 'Values': [vpc_id]},
        {'Name': 'accepter-vpc-info.vpc-id', 'Values': [peer_vpc_id]}
        ])
    if result['VpcPeeringConnections'] == []:
        result = client.describe_vpc_peering_connections(Filters=[
            {'Name': 'requester-vpc-info.vpc-id', 'Values': [peer_vpc_id]},
            {'Name': 'accepter-vpc-info.vpc-id', 'Values': [vpc_id]}
            ])
    return result


def is_active(peering_conn):
    return peering_conn['Status']['Code'] == 'active'


def is_pending(peering_conn):
    return peering_conn['Status']['Code'] == 'pending-acceptance'


def peer_status(resource, module):
    peer_id = module.params.get('peering_id')
    vpc_peering_connection = resource.VpcPeeringConnection(peer_id)
    return vpc_peering_connection.status['Message']


def create_peer_connection(client, module):
    changed = False
    vpc_id = module.params.get('vpc_id')
    peer_vpc_id = module.params.get('peer_vpc_id')
    peer_owner_id = module.params.get('peer_owner_id', False)
    peering_conns = describe_peering_connections(vpc_id, peer_vpc_id, client)
    for peering_conn in peering_conns['VpcPeeringConnections']:
        if is_active(peering_conn):
            return (False, peering_conn['VpcPeeringConnectionId'])
        if is_pending(peering_conn):
            return (False, peering_conn['VpcPeeringConnectionId'])
    if not peer_owner_id:
        try:
            peering_conn = client.create_vpc_peering_connection(VpcId=vpc_id, PeerVpcId=peer_vpc_id)
            return (True, peering_conn['VpcPeeringConnection']['VpcPeeringConnectionId'])
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e))            
    else:
        try:
            peering_conn = client.create_vpc_peering_connection(VpcId=vpc_id, PeerVpcId=peer_vpc_id, PeerOwnerId=str(peer_owner_id))
            return (True, peering_conn['VpcPeeringConnection']['VpcPeeringConnectionId'])
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e))            


def accept_reject_delete(state, client, resource, module):
    changed = False
    peer_id = module.params.get('peering_id')
    if state == "accept":
        if peer_status(resource, module) == "Active":
            return (False, peer_id)
        try:
            client.accept_vpc_peering_connection(VpcPeeringConnectionId=peer_id)
            return (True, peer_id)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e))            
    if state == "reject":
        if peer_status(resource, module) != "Active":
            try:
                client.reject_vpc_peering_connection(VpcPeeringConnectionId=peer_id)
                return (True, peer_id)
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg=str(e))
        else:
            return (False, peer_id)                   
    if state == "absent":
        try:
            client.delete_vpc_peering_connection(VpcPeeringConnectionId=peer_id)
            return (True, peer_id)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e))            
    return (changed, "")


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        region=dict(),
        vpc_id=dict(),
        peer_vpc_id=dict(),
        peer_owner_id=dict(),
        peering_id=dict(),
        profile=dict(),
        state=dict(default='present', choices=['present', 'absent', 'accept', 'reject'])
        )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if not (HAS_BOTO or HAS_BOTO3):
        module.fail_json(msg='json and boto/boto3 is required.')
    state = module.params.get('state').lower()
    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        client = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
        resource = boto3_conn(module, conn_type='resource', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError, e:
        module.fail_json(msg="Can't authorize connection - "+str(e))

    if state == 'present':
        (changed, results) = create_peer_connection(client, module)
        module.exit_json(changed=changed, peering_id=results)
    else:
        (changed, results) = accept_reject_delete(state, client, resource, module)
        module.exit_json(changed=changed, peering_id=results)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
