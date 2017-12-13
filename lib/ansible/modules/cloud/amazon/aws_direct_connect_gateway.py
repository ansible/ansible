#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: aws_direct_connect_gateway
short_description: Manage AWS Direct Connect Gateway.
description:
  - Creates AWS Direct Connect Gateway
  - Deletes AWS Direct Connect Gateway
  - Attaches Virtual Gateways to Direct Connect Gateway
  - Detaches Virtual Gateways to Direct Connect Gateway
requirements: [ boto3 ]
options:
  state:
    description:
        - present to ensure resource is created.
        - absent to remove resource
    required: false
    default: present
    choices: [ "present", "absent"]
  name:
    description:
        - name of the dxgw to be created or deleted
    required: false
  amazon_asn:
    description:
        - amazon side asn
    required: true
  direct_connect_gateway_id:
    description:
        - id of an existing direct connect gateway
    required: false
  virtual_gateway_id:
    description:
        - vpn gateway id of an existing virtual gateway
    required: false
author: Gobin Sougrakpam (gobins@github)
'''

EXAMPLES = '''
- name: Create a new direct connect gateway attached to virtual private gateway
  dxgw:
    state: present
    name: my-dx-gateway
    amazon_asn: 7224
    virtual_gateway_id: vpg-12345
  register: created_dxgw

- name: Create a new unattached dxgw
  dxgw:
    state: present
    name: my-dx-gateway
    amazon_asn: 7224
  register: created_dxgw

'''

RETURN = '''
result:
  description:
    - The attributes of the Direct Connect Gateway
  type: dict
  returned: I(state=present)
  contains:
    {
        "amazon_side_asn": 64512, 
        "changed": false, 
        "direct_connect_gateway_id": "38c2ebfa-76eb-4dcb-bd5e-123456ds", 
        "direct_connect_gateway_name": "my-direct-connect-gateway", 
        "direct_connect_gateway_state": "available", 
        "failed": false, 
        "owner_account": "0123456789"
    }
'''

import time
import traceback

try:
    import botocore
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (camel_dict_to_snake_dict, ec2_argument_spec, HAS_BOTO3,
                                      get_aws_connection_info, boto3_conn, AWSRetry)
from ansible.module_utils.aws.direct_connect import DirectConnectError

from ansible.module_utils._text import to_native


def dx_gateway_info(client, gateway_id):
    resp = client.describe_direct_connect_gateways(
        directConnectGatewayId=gateway_id)
    if resp is not []:
        return resp['directConnectGateways'][0]
    else:
        None

def wait_for_status(client, module, gateway_id, virtual_gateway_id, status):
    polling_increment_secs = 15
    max_retries = 3
    status_achieved = False

    for x in range(0, max_retries):
        try:
            response = check_dxgw_association(
                client, 
                module, 
                gateway_id=gateway_id,
                virtual_gateway_id=virtual_gateway_id)
            if len(response['directConnectGatewayAssociations']) > 0:
                if response['directConnectGatewayAssociations'][0]['associationState'] == status:
                    status_achieved = True
                    break
                else:
                    time.sleep(polling_increment_secs)
            else:
                status_achieved = True
                break
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    result = response
    return status_achieved, result


def associate_direct_connect_gateway(client, module, gateway_id):
    params = dict()
    params['virtual_gateway_id'] = module.params.get('virtual_gateway_id')
    try:
        response = client.create_direct_connect_gateway_association(
            directConnectGatewayId=gateway_id,
            virtualGatewayId=params['virtual_gateway_id'])
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    status_achieved, dxgw = wait_for_status(client, module, gateway_id, params['virtual_gateway_id'], 'associating')
    if not status_achieved:
        module.fail_json(msg='Error waiting for dxgw to attach to vpg - please check the AWS console')

    result = response
    return result


def delete_association(client, module, gateway_id, virtual_gateway_id):
    try:
        response = client.delete_direct_connect_gateway_association(
            directConnectGatewayId=gateway_id,
            virtualGatewayId=virtual_gateway_id)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    status_achieved, dxgw = wait_for_status(client, module, gateway_id, virtual_gateway_id, 'disassociating')
    if not status_achieved:
        module.fail_json(msg='Error waiting for  dxgw to detach from vpg - please check the AWS console')

    result = response
    return result

def create_dx_gateway(client, module):
    params = dict()
    params['name'] = module.params.get('name')
    params['amazon_asn'] = module.params.get('amazon_asn')
    try:
        response = client.create_direct_connect_gateway(
            directConnectGatewayName=params['name'],
            amazonSideAsn=int(params['amazon_asn'])
            )
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    result = response
    return result


def find_dx_gateway(client, module, gateway_id=None):
    params = dict()
    gateways = list()
    if gateway_id is not None:
        params['directConnectGatewayId'] = gateway_id
    while True:
        resp = client.describe_direct_connect_gateways(**params)
        gateways.extend(resp['directConnectGateways'])
        if 'nextToken' in resp:
            params['NextToken'] = resp['NextToken']
        else:
            break
    if gateways != []:
        count = 0
        
        for gateway in gateways:
            if module.params.get('name') == gateway['directConnectGatewayName']:
                count += 1
                return gateway
    return None


def check_dxgw_association(client, module, gateway_id, virtual_gateway_id=None):
    try:
        if virtual_gateway_id is None:
            resp = client.describe_direct_connect_gateway_associations(
                directConnectGatewayId=gateway_id
            )
        else:
            resp = client.describe_direct_connect_gateway_associations(
                directConnectGatewayId=gateway_id,
                virtualGatewayId=virtual_gateway_id,
            )
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    return resp


def ensure_present(client, module):
    # If an existing direct connect gateway matches our args
    # then a match is considered to have been found and we will not create another dxgw.

    changed = False
    params = dict()
    result = dict()
    params['name'] = module.params.get('name')
    params['amazon_asn'] = module.params.get('amazon_asn')
    params['virtual_gateway_id'] = module.params.get('virtual_gateway_id')

    # Check that a name argument has been supplied.
    if not module.params.get('name'):
        module.fail_json(msg='A name is required when a status of \'present\' is suppled')
    # Check that a amazon_asn argument has been supplied.
    if not module.params.get('amazon_asn'):
        module.fail_json(msg='An amazon_asn is required when a status of \'present\' is suppled')

    # check if a gateway matching our module args already exists
    existing_dxgw = find_dx_gateway(client, module)

    if existing_dxgw != None and existing_dxgw['directConnectGatewayState'] != 'deleted':
        gateway_id = existing_dxgw['directConnectGatewayId']
        # if a gateway_id was provided, check if it is attach to the DXGW
        if params['virtual_gateway_id']:
            resp = check_dxgw_association(
                client,
                module,
                gateway_id=gateway_id,
                virtual_gateway_id=params['virtual_gateway_id']
                )
            if not bool(resp["directConnectGatewayAssociations"]):
                # attach the dxgw to the supplied virtual_gateway_id
                associate_direct_connect_gateway(client, module, gateway_id)
                changed = True
        # if params['virtual_gateway_id'] is not provided, check the dxgw is attached to a VPG. If so, detach it.
        else:
            existing_dxgw = find_dx_gateway(client, module)

            resp = check_dxgw_association(
                client,
                module,
                gateway_id=gateway_id
                )
            if bool(resp["directConnectGatewayAssociations"]):
                for association in resp['directConnectGatewayAssociations']:
                    if association['associationState'] not in ['disassociating','disassociated']:
                        delete_association(
                            client,
                            module,
                            gateway_id=gateway_id,
                            virtual_gateway_id=association['virtualGatewayId'])
    else:
        # create a new dxgw
        new_dxgw = create_dx_gateway(client, module)
        changed = True
        gateway_id = new_dxgw['directConnectGateway']['directConnectGatewayId']

        # if a vpc-id was supplied, attempt to attach it to the dxgw
        if params['virtual_gateway_id']:
            associate_direct_connect_gateway(client, module, gateway_id)
            resp = check_dxgw_association(
                client,
                module,
                gateway_id=gateway_id
                )
            if bool(resp["directConnectGatewayAssociations"]):
                changed = True

    result = dx_gateway_info(client, gateway_id)
    return changed, result

def ensure_absent(client, module):
    # If an existing direct connect gateway matches our args
    # then a match is considered to have been found and we will not create another dxgw.
    if not module.params.get('direct_connect_gateway_id'):
        module.fail_json(msg='A direct_connect_gateway_id is required when a status of \'absent\' is suppled')
 
    changed = False
    result = dict()
    dx_gateway_id = module.params.get('direct_connect_gateway_id')
    existing_dxgw = find_dx_gateway(client, module, dx_gateway_id)
    
    if existing_dxgw != None:
        resp = check_dxgw_association(
            client,
            module,
            gateway_id=dx_gateway_id
            )
        if bool(resp["directConnectGatewayAssociations"]):
            for association in resp['directConnectGatewayAssociations']:
                if association['associationState'] not in ['disassociating','disassociated']:
                    delete_association(
                        client,
                        module,
                        gateway_id=dx_gateway_id,
                        virtual_gateway_id=association['virtualGatewayId'])
        # wait for deleting association
        timeout = time.time() + 60*10
        while time.time() < timeout: 
            resp = check_dxgw_association(
                client,
                module,
                gateway_id=dx_gateway_id
                )
            if resp["directConnectGatewayAssociations"] != []:
                time.sleep(15)                
            else:
                break

        resp = client.delete_direct_connect_gateway(
            directConnectGatewayId=dx_gateway_id
        )
        result = resp['directConnectGateway']
    return changed, result


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(default='present', choices=['present', 'absent']),
        name=dict(),
        amazon_asn=dict(),
        virtual_gateway_id=dict(),
        direct_connect_gateway_id=dict(),
        wait_timeout=dict(type='int', default=320),
        )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required for this module')

    state = module.params.get('state').lower()

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        if not region:
            module.fail_json(msg="Either region or AWS_REGION or EC2_REGION environment variable or boto config aws_region or ec2_region must be set.")

        client = boto3_conn(module, conn_type='client', resource='directconnect', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg="Can't authorize connection - %s" % to_native(e), exception=traceback.format_exc())

    try:
        if state == 'present':
            (changed, results) = ensure_present(client, module)
        elif state == 'absent':
            changed = ensure_absent(client, module)
            results = {}
    except DirectConnectError as e:
        if e.response:
            module.fail_json(msg=e.msg, exception=e.last_traceback, **e.response)
        elif e.last_traceback:
            module.fail_json(msg=e.msg, exception=e.last_traceback)
        else:
            module.fail_json(msg=e.msg)

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(results))

if __name__ == '__main__':
    main()
