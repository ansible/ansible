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
version_added: "2.2"
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
  tags:
    description:
      - Dictionary of tags to look for and apply when creating a Peering Connection.
    required: false    
  state:
    description:
      - Create, delete, accept, reject a peering connection.
    required: false
    default: present
    choices: ['present', 'absent', 'accept', 'reject']
author: Mike Mochan(@mmochan)
extends_documentation_fragment: aws
requirements: [ botocore, boto3, json ]
'''

EXAMPLES = '''
# Complete example to create and accept a local peering connection.
- name: Create local account VPC peering Connection
  ec2_vpc_peer:
    region: ap-southeast-2
    vpc_id: vpc-12345678
    peer_vpc_id: vpc-87654321
    state: present
    tags:
      Name: Peering conenction for VPC 21 to VPC 22
      CostCode: CC1234
      Project: phoenix       
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
    tags:
      Name: Peering conenction for VPC 21 to VPC 22
      CostCode: CC1234
      Project: phoenix           
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
    peer_vpc_id: vpc-12345678
    peer_owner_id: 123456789102
    state: present
    tags:
      Name: Peering conenction for VPC 21 to VPC 22
      CostCode: CC1234
      Project: phoenix         
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
    tags:
      Name: Peering conenction for VPC 21 to VPC 22
      CostCode: CC1234
      Project: phoenix          
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
    peer_vpc_id: vpc-12345678
    peer_owner_id: 123456789102
    state: present
    tags:
      Name: Peering conenction for VPC 21 to VPC 22
      CostCode: CC1234
      Project: phoenix        
  register: vpc_peer

- name: Accept a cross account VPC peering connection request
  ec2_vpc_peer:
    region: ap-southeast-2
    peering_id: "{{ vpc_peer.peering_id }}"
    profile: bot03_profile_for_cross_account
    state: accept
    tags:
      Name: Peering conenction for VPC 21 to VPC 22
      CostCode: CC1234
      Project: phoenix

# Complete example to create and reject a cross account peering connection.
- name: Create cross account VPC peering Connection
  ec2_vpc_peer:
    region: ap-southeast-2
    vpc_id: vpc-12345678
    peer_vpc_id: vpc-12345678
    peer_owner_id: 123456789102
    state: present
    tags:
      Name: Peering conenction for VPC 21 to VPC 22
      CostCode: CC1234
      Project: phoenix         
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
  description: The result of the create, accept, reject or delete action.
  returned: success
  type: dictionary
'''

try:
    import json
    import botocore
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def tags_changed(pcx_id, client, module):
    changed = False
    tags = dict()
    if module.params.get('tags'):
        tags = module.params.get('tags')
    pcx = find_pcx_by_id(pcx_id, client, module)
    if pcx['VpcPeeringConnections']:
        pcx_values = [t.values() for t in pcx['VpcPeeringConnections'][0]['Tags']]
        pcx_tags = [item for sublist in pcx_values for item in sublist]
        tag_values = [[key, str(value)] for key, value in tags.iteritems()]
        tags = [item for sublist in tag_values for item in sublist]
        if sorted(pcx_tags) == sorted(tags):
            changed = False
            return changed
        else:
            delete_tags(pcx_id, client, module)
            create_tags(pcx_id, client, module)
            changed = True
            return changed
    return changed


def describe_peering_connections(params, client):
    result = client.describe_vpc_peering_connections(Filters=[
        {'Name': 'requester-vpc-info.vpc-id', 'Values': [params['VpcId']]},
        {'Name': 'accepter-vpc-info.vpc-id', 'Values': [params['PeerVpcId']]}
        ])
    if result['VpcPeeringConnections'] == []:
        result = client.describe_vpc_peering_connections(Filters=[
            {'Name': 'requester-vpc-info.vpc-id', 'Values': [params['PeerVpcId']]},
            {'Name': 'accepter-vpc-info.vpc-id', 'Values': [params['VpcId']]}
            ])
    return result


def is_active(peering_conn):
    return peering_conn['Status']['Code'] == 'active'


def is_pending(peering_conn):
    return peering_conn['Status']['Code'] == 'pending-acceptance'


def create_peer_connection(client, module):
    changed = False
    params = dict()
    params['VpcId'] = module.params.get('vpc_id')
    params['PeerVpcId'] = module.params.get('peer_vpc_id')
    if module.params.get('peer_owner_id'):
        params['PeerOwnerId'] = str(module.params.get('peer_owner_id'))
    params['DryRun'] = module.check_mode
    peering_conns = describe_peering_connections(params, client)
    for peering_conn in peering_conns['VpcPeeringConnections']:
        pcx_id = peering_conn['VpcPeeringConnectionId']
        if tags_changed(pcx_id, client, module):
            changed = True
        if is_active(peering_conn):
            return (changed, peering_conn['VpcPeeringConnectionId'])
        if is_pending(peering_conn):
            return (changed, peering_conn['VpcPeeringConnectionId'])
    try:
        peering_conn = client.create_vpc_peering_connection(**params)
        pcx_id = peering_conn['VpcPeeringConnection']['VpcPeeringConnectionId']
        if module.params.get('tags'):
            create_tags(pcx_id, client, module)
        changed = True
        return (changed, peering_conn['VpcPeeringConnection']['VpcPeeringConnectionId'])
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))                   


def peer_status(client, module):
    params = dict()
    params['VpcPeeringConnectionIds'] = [module.params.get('peering_id')]
    vpc_peering_connection = client.describe_vpc_peering_connections(**params)
    return vpc_peering_connection['VpcPeeringConnections'][0]['Status']['Code']


def accept_reject_delete(state, client, module):
    changed = False
    params = dict()
    params['VpcPeeringConnectionId'] = module.params.get('peering_id')
    params['DryRun'] = module.check_mode
    invocations = {
        'accept': client.accept_vpc_peering_connection,
        'reject': client.reject_vpc_peering_connection,
        'absent': client.delete_vpc_peering_connection
    }
    if state == 'absent' or peer_status(client, module) != 'active':
        try:
            invocations[state](**params)
            if module.params.get('tags'):
                create_tags(params['VpcPeeringConnectionId'], client, module)
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e))
    if tags_changed(params['VpcPeeringConnectionId'], client, module):
        changed = True
    return changed, params['VpcPeeringConnectionId']


def load_tags(module):
    tags = []
    if module.params.get('tags'):
        for name, value in module.params.get('tags').iteritems():
            tags.append({'Key': name, 'Value': str(value)})
    return tags


def create_tags(pcx_id, client, module):
    try:
        delete_tags(pcx_id, client, module)
        client.create_tags(Resources=[pcx_id], Tags=load_tags(module))
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))


def delete_tags(pcx_id, client, module):
    try:
        client.delete_tags(Resources=[pcx_id])
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))


def find_pcx_by_id(pcx_id, client, module):
    try:
        return client.describe_vpc_peering_connections(VpcPeeringConnectionIds=[pcx_id])
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        vpc_id=dict(),
        peer_vpc_id=dict(),
        peering_id=dict(),
        peer_owner_id=dict(),
        tags=dict(required=False, type='dict'),
        profile=dict(),
        state=dict(default='present', choices=['present', 'absent', 'accept', 'reject'])
        )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='json, botocore and boto3 are required.')
    state = module.params.get('state').lower()
    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        client = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg="Can't authorize connection - "+str(e))

    if state == 'present':
        (changed, results) = create_peer_connection(client, module)
        module.exit_json(changed=changed, peering_id=results)
    else:
        (changed, results) = accept_reject_delete(state, client, module)
        module.exit_json(changed=changed, peering_id=results)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
