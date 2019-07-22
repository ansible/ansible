#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: ec2_vpc_endpoint
short_description: Create and delete AWS VPC Endpoints.
description:
  - Creates AWS VPC endpoints.
  - Deletes AWS VPC endpoints.
  - This module support check mode.
version_added: "2.4"
requirements: [ boto3 ]
options:
  vpc_id:
    description:
      - Required when creating a VPC endpoint.
    required: false
  service:
    description:
      - An AWS supported vpc endpoint service. Use the M(ec2_vpc_endpoint_info)
        module to describe the supported endpoint services.
      - Required when creating an endpoint.
    required: false
  policy:
    description:
      - A properly formatted json policy as string, see
        U(https://github.com/ansible/ansible/issues/7005#issuecomment-42894813).
        Cannot be used with I(policy_file).
      - Option when creating an endpoint. If not provided AWS will
        utilise a default policy which provides full access to the service.
    required: false
  policy_file:
    description:
      - The path to the properly json formatted policy file, see
        U(https://github.com/ansible/ansible/issues/7005#issuecomment-42894813)
        on how to use it properly. Cannot be used with I(policy).
      - Option when creating an endpoint. If not provided AWS will
        utilise a default policy which provides full access to the service.
    required: false
    aliases: [ "policy_path" ]
  state:
    description:
        - present to ensure resource is created.
        - absent to remove resource
    required: false
    default: present
    choices: [ "present", "absent"]
  wait:
    description:
      - When specified, will wait for either available status for state present.
        Unfortunately this is ignored for delete actions due to a difference in
        behaviour from AWS.
    required: false
    default: no
    type: bool
  wait_timeout:
    description:
      - Used in conjunction with wait. Number of seconds to wait for status.
        Unfortunately this is ignored for delete actions due to a difference in
        behaviour from AWS.
    required: false
    default: 320
  route_table_ids:
    description:
      - List of one or more route table ids to attach to the endpoint. A route
        is added to the route table with the destination of the endpoint if
        provided.
    required: false
  vpc_endpoint_id:
    description:
      - One or more vpc endpoint ids to remove from the AWS account
    required: false
  client_token:
    description:
      - Optional client token to ensure idempotency
    required: false
author: Karen Cheng (@Etherdaemon)
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create new vpc endpoint with a json template for policy
  ec2_vpc_endpoint:
    state: present
    region: ap-southeast-2
    vpc_id: vpc-12345678
    service: com.amazonaws.ap-southeast-2.s3
    policy: " {{ lookup( 'template', 'endpoint_policy.json.j2') }} "
    route_table_ids:
      - rtb-12345678
      - rtb-87654321
  register: new_vpc_endpoint

- name: Create new vpc endpoint the default policy
  ec2_vpc_endpoint:
    state: present
    region: ap-southeast-2
    vpc_id: vpc-12345678
    service: com.amazonaws.ap-southeast-2.s3
    route_table_ids:
      - rtb-12345678
      - rtb-87654321
  register: new_vpc_endpoint

- name: Create new vpc endpoint with json file
  ec2_vpc_endpoint:
    state: present
    region: ap-southeast-2
    vpc_id: vpc-12345678
    service: com.amazonaws.ap-southeast-2.s3
    policy_file: "{{ role_path }}/files/endpoint_policy.json"
    route_table_ids:
      - rtb-12345678
      - rtb-87654321
  register: new_vpc_endpoint

- name: Delete newly created vpc endpoint
  ec2_vpc_endpoint:
    state: absent
    nat_gateway_id: "{{ new_vpc_endpoint.result['VpcEndpointId'] }}"
    region: ap-southeast-2
'''

RETURN = '''
endpoints:
  description: The resulting endpoints from the module call
  returned: success
  type: list
  sample: [
      {
        "creation_timestamp": "2017-02-20T05:04:15+00:00",
        "policy_document": {
          "Id": "Policy1450910922815",
          "Statement": [
            {
              "Action": "s3:*",
              "Effect": "Allow",
              "Principal": "*",
              "Resource": [
                "arn:aws:s3:::*/*",
                "arn:aws:s3:::*"
              ],
              "Sid": "Stmt1450910920641"
            }
          ],
          "Version": "2012-10-17"
        },
        "route_table_ids": [
          "rtb-abcd1234"
        ],
        "service_name": "com.amazonaws.ap-southeast-2.s3",
        "vpc_endpoint_id": "vpce-a1b2c3d4",
        "vpc_id": "vpc-abbad0d0"
      }
    ]
'''

import datetime
import json
import time
import traceback

try:
    import botocore
except ImportError:
    pass  # will be picked up by imported HAS_BOTO3

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (get_aws_connection_info, boto3_conn, ec2_argument_spec, HAS_BOTO3,
                                      camel_dict_to_snake_dict)
from ansible.module_utils.six import string_types


def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


def wait_for_status(client, module, resource_id, status):
    polling_increment_secs = 15
    max_retries = (module.params.get('wait_timeout') // polling_increment_secs)
    status_achieved = False

    for x in range(0, max_retries):
        try:
            resource = get_endpoints(client, module, resource_id)['VpcEndpoints'][0]
            if resource['State'] == status:
                status_achieved = True
                break
            else:
                time.sleep(polling_increment_secs)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e), exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))

    return status_achieved, resource


def get_endpoints(client, module, resource_id=None):
    params = dict()
    if resource_id:
        params['VpcEndpointIds'] = [resource_id]

    result = json.loads(json.dumps(client.describe_vpc_endpoints(**params), default=date_handler))
    return result


def setup_creation(client, module):
    vpc_id = module.params.get('vpc_id')
    service_name = module.params.get('service')

    if module.params.get('route_table_ids'):
        route_table_ids = module.params.get('route_table_ids')
        existing_endpoints = get_endpoints(client, module)
        for endpoint in existing_endpoints['VpcEndpoints']:
            if endpoint['VpcId'] == vpc_id and endpoint['ServiceName'] == service_name:
                sorted_endpoint_rt_ids = sorted(endpoint['RouteTableIds'])
                sorted_route_table_ids = sorted(route_table_ids)
                if sorted_endpoint_rt_ids == sorted_route_table_ids:
                    return False, camel_dict_to_snake_dict(endpoint)

    changed, result = create_vpc_endpoint(client, module)

    return changed, json.loads(json.dumps(result, default=date_handler))


def create_vpc_endpoint(client, module):
    params = dict()
    changed = False
    token_provided = False
    params['VpcId'] = module.params.get('vpc_id')
    params['ServiceName'] = module.params.get('service')
    params['DryRun'] = module.check_mode

    if module.params.get('route_table_ids'):
        params['RouteTableIds'] = module.params.get('route_table_ids')

    if module.params.get('client_token'):
        token_provided = True
        request_time = datetime.datetime.utcnow()
        params['ClientToken'] = module.params.get('client_token')

    policy = None
    if module.params.get('policy'):
        try:
            policy = json.loads(module.params.get('policy'))
        except ValueError as e:
            module.fail_json(msg=str(e), exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))

    elif module.params.get('policy_file'):
        try:
            with open(module.params.get('policy_file'), 'r') as json_data:
                policy = json.load(json_data)
        except Exception as e:
            module.fail_json(msg=str(e), exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))

    if policy:
        params['PolicyDocument'] = json.dumps(policy)

    try:
        changed = True
        result = camel_dict_to_snake_dict(client.create_vpc_endpoint(**params)['VpcEndpoint'])
        if token_provided and (request_time > result['creation_timestamp'].replace(tzinfo=None)):
            changed = False
        elif module.params.get('wait') and not module.check_mode:
            status_achieved, result = wait_for_status(client, module, result['vpc_endpoint_id'], 'available')
            if not status_achieved:
                module.fail_json(msg='Error waiting for vpc endpoint to become available - please check the AWS console')
    except botocore.exceptions.ClientError as e:
        if "DryRunOperation" in e.message:
            changed = True
            result = 'Would have created VPC Endpoint if not in check mode'
        elif "IdempotentParameterMismatch" in e.message:
            module.fail_json(msg="IdempotentParameterMismatch - updates of endpoints are not allowed by the API")
        elif "RouteAlreadyExists" in e.message:
            module.fail_json(msg="RouteAlreadyExists for one of the route tables - update is not allowed by the API")
        else:
            module.fail_json(msg=str(e), exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))

    return changed, result


def setup_removal(client, module):
    params = dict()
    changed = False
    params['DryRun'] = module.check_mode
    if isinstance(module.params.get('vpc_endpoint_id'), string_types):
        params['VpcEndpointIds'] = [module.params.get('vpc_endpoint_id')]
    else:
        params['VpcEndpointIds'] = module.params.get('vpc_endpoint_id')
    try:
        result = client.delete_vpc_endpoints(**params)['Unsuccessful']
        if not module.check_mode and (result != []):
            module.fail_json(msg=result)
    except botocore.exceptions.ClientError as e:
        if "DryRunOperation" in e.message:
            changed = True
            result = 'Would have deleted VPC Endpoint if not in check mode'
        else:
            module.fail_json(msg=str(e), exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    return changed, result


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            vpc_id=dict(),
            service=dict(),
            policy=dict(type='json'),
            policy_file=dict(type='path', aliases=['policy_path']),
            state=dict(default='present', choices=['present', 'absent']),
            wait=dict(type='bool', default=False),
            wait_timeout=dict(type='int', default=320, required=False),
            route_table_ids=dict(type='list'),
            vpc_endpoint_id=dict(),
            client_token=dict(),
        )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[['policy', 'policy_file']],
        required_if=[
            ['state', 'present', ['vpc_id', 'service']],
            ['state', 'absent', ['vpc_endpoint_id']],
        ]
    )

    # Validate Requirements
    if not HAS_BOTO3:
        module.fail_json(msg='botocore and boto3 are required for this module')

    state = module.params.get('state')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    except NameError as e:
        # Getting around the get_aws_connection_info boto reliance for region
        if "global name 'boto' is not defined" in e.message:
            module.params['region'] = botocore.session.get_session().get_config_variable('region')
            if not module.params['region']:
                module.fail_json(msg="Error - no region provided")
        else:
            module.fail_json(msg="Can't retrieve connection information - " + str(e),
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        ec2 = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg="Failed to connect to AWS due to wrong or missing credentials: %s" % str(e),
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))

    # Ensure resource is present
    if state == 'present':
        (changed, results) = setup_creation(ec2, module)
    else:
        (changed, results) = setup_removal(ec2, module)

    module.exit_json(changed=changed, result=results)


if __name__ == '__main__':
    main()
