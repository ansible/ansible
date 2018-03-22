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
      - An AWS supported vpc endpoint service. Use the ec2_vpc_endpoint_facts
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
    choices: ["yes", "no"]
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
      - One or more vpc endpoint ids to remove from the AWS account with C(state=absent)
        or as of Ansible 2.6 to update if used with C(state=present).
    required: false
  purge_route_tables:
    description:
      - May be used in combination with state=present and vpc_endpoint_id to update
        an endpoint.
    default: False
    type: bool
    version_added: "2.6"
  client_token:
    description:
      - Optional client token to ensure idempotency
    required: false
author: Karen Cheng(@Etherdaemon)
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

- name: Update routes and policy from the task above
  # Also update the policy
  ec2_vpc_endpoint:
    state: present
    vpc_endpoint_id: "{{ new_vpc_endpoint.result.vpc_endpoint_id }}"
    route_table_ids:
      - rtb-11111111
      - rtb-22222222
    purge_route_tables: True  # removes route tables rtb-12345678 and rtb-87654321
    policy_file: "{{ role_path }}/files/new_endpoint_policy.json"

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
    from botocore.exceptions import BotoCoreError, ClientError, WaiterError
except ImportError:
    pass  # will be picked up by imported HAS_BOTO3

from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.aws.waiters import get_waiter
from ansible.module_utils.ec2 import (
    get_aws_connection_info, boto3_conn, ec2_argument_spec,
    camel_dict_to_snake_dict, compare_policies, AWSRetry
)


def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


def wait_for_status(client, module, resource_id, status):
    polling_increment_secs = 15
    max_retries = (module.params.get('wait_timeout') // polling_increment_secs)
    status_achieved = False

    for x in range(0, max_retries):
        resource = get_endpoints(client, module)['VpcEndpoints']
        if resource:
            if resource[0]['State'] == status:
                status_achieved = True
                break
        elif resource == [] and status == 'deleted':
            status_achieved = True
            break
        time.sleep(polling_increment_secs)

    if resource:
        resource = camel_dict_to_snake_dict(resource[0])
    return status_achieved, resource


def endpoint_filters(module):
    params = {'Filters': []}
    if module.params.get('vpc_endpoint_id'):
        params['VpcEndpointIds'] = [module.params['vpc_endpoint_id']]
    if module.params.get('vpc_id'):
        params['Filters'].append({'Name': 'vpc-id', 'Values': [module.params['vpc_id']]})
    if module.params.get('service'):
        params['Filters'].append({'Name': 'service-name', 'Values': [module.params['service']]})
    return params


@AWSRetry.exponential_backoff()
def get_endpoints(client, module):
    params = endpoint_filters(module)
    try:
        return json.loads(json.dumps(client.describe_vpc_endpoints(**params), default=date_handler))
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidVpcEndpointId.NotFound':
            return {'VpcEndpoints': []}
        else:
            module.fail_json_aws(e, msg="Unable to describe endpoints")
    except BotoCoreError as e:
        module.fail_json_aws(e, msg="Unable to describe endpoints")


def setup_creation(client, module):
    vpc_id = module.params.get('vpc_id')
    service_name = module.params.get('service')

    if module.params.get('route_table_ids') is not None:
        route_table_ids = module.params.get('route_table_ids')
        existing_endpoints = get_endpoints(client, module)['VpcEndpoints']
        if len(existing_endpoints) > 1:
            module.fail_json("More than one endpoint matches your criteria: {0}".format(existing_endpoints))

        for endpoint in existing_endpoints:
            new_endpoint_rt_ids = set(route_table_ids) - set(endpoint['RouteTableIds'])
            obsolete_endpoint_rt_ids = set(endpoint['RouteTableIds']) - set(route_table_ids)
            current_policy = json.loads(to_native(endpoint['PolicyDocument']))
            new_policy = get_policy(client, module)

            # if/elif for backwards compatibility with Ansible < 2.5
            if not module.params.get('vpc_endpoint_id') and not any([new_endpoint_rt_ids, obsolete_endpoint_rt_ids]):
                return False, camel_dict_to_snake_dict(endpoint)
            elif module.params.get('vpc_endpoint_id'):
                return modify_endpoint(client, module, endpoint, new_policy, current_policy,
                                       new_endpoint_rt_ids, obsolete_endpoint_rt_ids)

    changed, result = create_vpc_endpoint(client, module)

    return changed, json.loads(json.dumps(result, default=date_handler))


def modify_endpoint(client, module, endpoint, new_policy, current_policy, new_endpoint_rt_ids, obsolete_endpoint_rt_ids):
    changed = False
    modification_params = {'VpcEndpointId': module.params['vpc_endpoint_id']}
    if new_policy is not None and compare_policies(current_policy, new_policy):
        changed = True
        modification_params['PolicyDocument'] = json.dumps(new_policy)
    if new_endpoint_rt_ids:
        changed = True
        modification_params['AddRouteTableIds'] = list(new_endpoint_rt_ids)
    if obsolete_endpoint_rt_ids and module.params.get('purge_route_tables'):
        changed = True
        modification_params['RemoveRouteTableIds'] = list(obsolete_endpoint_rt_ids)
    if changed and not module.check_mode:
        try:
            client.modify_vpc_endpoint(**modification_params)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Unable to modify endpoint {0}".format(module.params['vpc_endpoint_id']))
        else:
            endpoint = get_endpoints(client, module)['VpcEndpoints'][0]
    return changed, camel_dict_to_snake_dict(endpoint)


def get_policy(client, module):
    policy = None
    if module.params.get('policy'):
        try:
            policy = json.loads(module.params.get('policy'))
        except ValueError as e:
            module.fail_json(msg=str(e), exception=traceback.format_exc())

    elif module.params.get('policy_file'):
        try:
            with open(module.params.get('policy_file'), 'r') as json_data:
                policy = json.load(json_data)
        except Exception as e:
            module.fail_json(msg=str(e), exception=traceback.format_exc())

    return policy


def create_vpc_endpoint(client, module):
    if module.check_mode:
        return True, 'Would have created VPC Endpoint if not in check mode'

    params = dict()
    token_provided = False
    params['VpcId'] = module.params.get('vpc_id')
    params['ServiceName'] = module.params.get('service')

    if module.params.get('route_table_ids'):
        params['RouteTableIds'] = module.params.get('route_table_ids')

    if module.params.get('client_token'):
        token_provided = True
        request_time = datetime.datetime.utcnow()
        params['ClientToken'] = module.params.get('client_token')

    policy = get_policy(client, module)
    if policy:
        params['PolicyDocument'] = policy

    try:
        changed = True
        result = camel_dict_to_snake_dict(client.create_vpc_endpoint(**params)['VpcEndpoint'])
        if token_provided and (request_time > result['creation_timestamp'].replace(tzinfo=None)):
            changed = False
        elif module.params.get('wait'):
            get_waiter(
                client, 'vpc_endpoint_exists'
            ).wait(
                VpcEndpointIds=[result['vpc_endpoint_id']]
            )
            result = get_endpoints(client, module)['VpcEndpoints'][0]
    except WaiterError as e:
        module.fail_json_aws(e, msg="Error waiting for vpc endpoint to become available - please check the AWS console")
    except ClientError as e:
        if e.response['Error']['Code'] in ["IdempotentParameterMismatch", "RouteAlreadyExists"]:
            module.fail_json_aws(e, msg="To update an endpoint, provide the vpc_endpoint_id to the task")
        else:
            module.fail_json_aws(e, msg="Failed to create endpoint")
    except BotoCoreError as e:
        module.fail_json_aws(e, msg="Failed to create endpoint.")

    return changed, camel_dict_to_snake_dict(result)


def setup_removal(client, module):
    existing_endpoints = get_endpoints(client, module)['VpcEndpoints']
    if not existing_endpoints:
        return False, []
    else:
        changed = True

    if module.check_mode:
        return changed, 'Would have deleted VPC Endpoint if not in check mode'
    try:
        result = client.delete_vpc_endpoints(VpcEndpointIds=[module.params['vpc_endpoint_id']])['Unsuccessful']
        if module.params.get('wait'):
            get_waiter(
                client, 'vpc_endpoint_deleted'
            ).wait(
                **endpoint_filters(module)
            )
    except WaiterError as e:
        module.fail_json_aws(e, msg="Took too long to wait for endpoint {0} to be deleted".format(module.params['vpc_endpoint_id']))
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to delete endpoint {0}".format(module.params['vpc_endpoint_id']))
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
            purge_route_tables=dict(type='bool', default=False),
            client_token=dict(),
        )
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[['policy', 'policy_file']],
        required_together=[['vpc_id', 'service']],
        required_if=[['state', 'absent', ['vpc_endpoint_id']]]
    )
    if module.params.get('state') == 'present' and not module.params.get('vpc_id') and not module.params.get('vpc_endpoint_id'):
        module.fail_json(msg="state is present but all of the following are missing: [vpc_id, service] or [vpc_endpoint_id]")

    state = module.params.get('state')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    ec2 = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    # Ensure resource is present
    if state == 'present':
        (changed, results) = setup_creation(ec2, module)
    else:
        (changed, results) = setup_removal(ec2, module)

    module.exit_json(changed=changed, result=results)


if __name__ == '__main__':
    main()
