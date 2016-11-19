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
module: elb_target_group
short_description: Manage a target group for an Application load balancer
description:
    - Manage an AWS Application Elastic Load Balancer target group. See U(http://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html) for details.
version_added: "2.3"
author: "Rob White (@wimnat)"
options:
  name:
    description:
      - The name of the target group.
    required: true
  protocol:
    description:
      - The protocol to use for routing traffic to the targets. Required if state=present.
    required: false
    choices: [ 'http', 'https' ]
  port:
    description:
      - The port on which the targets receive traffic. This port is used unless you specify a port override when registering the target. Required if state=present.
    required: false
  vpc_id:
    description:
      - The identifier of the virtual private cloud (VPC). Required if state=present.
    required: false
  health_check_protocol:
    description:
      - The protocol the load balancer uses when performing health checks on targets.
    required: false
    choices: [ 'http', 'https' ]
  health_check_port:
    description:
      - The port the load balancer uses when performing health checks on targets.
    required: false
    default: "The port on which each target receives traffic from the load balancer."
  health_check_path:
    description:
      - The ping path that is the destination on the targets for health checks. The path must be defined in order to set a health check.
    required: false
  health_check_interval:
    description:
      - The approximate amount of time, in seconds, between health checks of an individual target.
    required: false
    default: 30
  health_check_timeout:
    description:
      - The amount of time, in seconds, during which no response from a target means a failed health check.
    required: false
    default: 5
  healthy_threshold_count:
    description:
      - The number of consecutive health checks successes required before considering an unhealthy target healthy.
    required: false
    default: 5
  unhealthy_threshold_count:
    description:
      - The number of consecutive health check failures required before considering a target unhealthy.
    required: false
    default: 2
  successful_response_codes:
    description:
      - The HTTP codes to use when checking for a successful response from a target.
    required: false
    default: 200
  state:
    description:
      - Create or destroy the target group.
    required: true
    choices: [ 'present', 'absent' ]
extends_documentation_fragment:
    - aws
    - ec2
notes:
  - Once a target group has been created, only its health check can then be modified using subsequent calls
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a target group with a default health check
- elb_target_group:
    name: mytargetgroup
    protocol: HTTP
    port: 80
    vpc_id: vpc-01234567
    state: present

# Modify the target group with a custom health check
- elb_target_group:
    name: mytargetgroup
    protocol: HTTP
    port: 80
    vpc_id: vpc-01234567
    health_check_path: /
    successful_response_codes: "200, 250-260"
    state: present

# Delete a target group
- elb_target_group:
    name: mytargetgroup
    state: absent

# Create a target group with targets
- elb_target_group:
  name: mytargetgroup
  protocol: http
  port: 81
  vpc_id: vpc-01234567
  health_check_path: /
  successful_response_codes: "200,250-260"
  targets: 
   - Id: i-01234567
     Port: 80
   - Id: i-98765432
     Port: 80
  state: present
  wait_timeout: 200
  wait: True
'''

RETURN = '''
target_group_arn:
    description: The Amazon Resource Name (ARN) of the target group.
    type: string
    sample: "arn:aws:elasticloadbalancing:ap-southeast-2:01234567890:targetgroup/mytargetgroup/aabbccddee0044332211"
target_group_name:
    description: The name of the target group.
    type: string
    sample: mytargetgroup
protocol:
    description: The protocol to use for routing traffic to the targets.
    type: string
    sample: HTTP
port:
    description: The port on which the targets are listening.
    type: int
    sample: 80
vpc_id:
    description: The ID of the VPC for the targets.
    type: string
    sample: vpc-0123456
health_check_protocol:
    description: The protocol to use to connect with the target.
    type: string
    sample: HTTP
health_check_port:
    description: The port to use to connect with the target.
    type: string
    sample: traffic-port
health_check_interval_seconds:
    description: The approximate amount of time, in seconds, between health checks of an individual target.
    type: int
    sample: 30
health_check_timeout_seconds:
    description: The amount of time, in seconds, during which no response means a failed health check.
    type: int
    sample: 5
healthy_threshold_count:
    description: The number of consecutive health checks successes required before considering an unhealthy target healthy.
    type: int
    sample: 5
unhealthy_threshold_count:
    description: The number of consecutive health check failures required before considering the target unhealthy.
    type: int
    sample: 2
health_check_path:
    description: The destination for the health check request.
    type: string
    sample: /index.html
matcher:
    description: The HTTP codes to use when checking for a successful response from a target.
    type: dict
    sample: {
        "http_code": "200"
    }
load_balancer_arns:
    description: The Amazon Resource Names (ARN) of the load balancers that route traffic to this target group.
    type: list
    sample: []
'''

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def get_target_group(connection, module):

    try:
        return connection.describe_target_groups(Names=[module.params.get("name")])['TargetGroups'][0]
    except (ClientError, NoCredentialsError) as e:
        if e.response['Error']['Code'] == 'TargetGroupNotFound':
            return None
        else:
            module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))


def diff_list(a, b):
    """Find the entries in list a that are not in list b"""
    b = set(b)
    return [aa for aa in a if aa not in b]


def wait_for_status(connection, module, target_group_arn, targets, status):
    polling_increment_secs = 5
    max_retries = (module.params.get('wait_timeout') / polling_increment_secs)
    status_achieved = False

    for x in range(0, max_retries):
        try:
            response = connection.describe_target_health(TargetGroupArn=target_group_arn, Targets=targets)
            if response['TargetHealthDescriptions'][0]['TargetHealth']['State'] == status:
                status_achieved = True
                break
            else:
                time.sleep(polling_increment_secs)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

    result = response
    return status_achieved, result


def create_or_update_target_group(connection, module):

    changed = False
    params = dict()
    params['Name'] = module.params.get("name")
    params['Protocol'] = module.params.get("protocol").upper()
    params['Port'] = module.params.get("port")
    params['VpcId'] = module.params.get("vpc_id")

    # If health check path not None, set health check attributes
    if module.params.get("health_check_path") is not None:
        params['HealthCheckPath'] = module.params.get("health_check_path")

        if module.params.get("health_check_protocol") is not None:
            params['HealthCheckProtocol'] = module.params.get("health_check_protocol").upper()

        if module.params.get("health_check_port") is not None:
            params['HealthCheckPort'] = str(module.params.get("health_check_port"))

        if module.params.get("health_check_interval") is not None:
            params['HealthCheckIntervalSeconds'] = module.params.get("health_check_interval")

        if module.params.get("health_check_timeout") is not None:
            params['HealthCheckTimeoutSeconds'] = module.params.get("health_check_timeout")

        if module.params.get("healthy_threshold_count") is not None:
            params['HealthyThresholdCount'] = module.params.get("healthy_threshold_count")

        if module.params.get("unhealthy_threshold_count") is not None:
            params['UnhealthyThresholdCount'] = module.params.get("unhealthy_threshold_count")

        if module.params.get("successful_response_codes") is not None:
            params['Matcher'] = {}
            params['Matcher']['HttpCode'] = module.params.get("successful_response_codes")

    # Does the target group currently exist?
    tg = get_target_group(connection, module)

    if tg:
        # Target group exists so check health check parameters match what has been passed

        # If we have no health check path then we have nothing to modify
        hc_params = dict()
        if module.params.get("health_check_path") is not None:
            # Health check protocol
            if 'HealthCheckProtocol' in params and tg['HealthCheckProtocol'] != params['HealthCheckProtocol']:
                hc_params['HealthCheckProtocol'] = params['HealthCheckProtocol']

            # Health check port
            if 'HealthCheckPort' in params and tg['HealthCheckPort'] != params['HealthCheckPort']:
                hc_params['HealthCheckPort'] = params['HealthCheckPort']

            # Health check path
            if 'HealthCheckPath'in params and tg['HealthCheckPath'] != params['HealthCheckPath']:
                hc_params['HealthCheckPath'] = params['HealthCheckPath']

            # Health check interval
            if 'HealthCheckIntervalSeconds' in params and tg['HealthCheckIntervalSeconds'] != params['HealthCheckIntervalSeconds']:
                hc_params['HealthCheckIntervalSeconds'] = params['HealthCheckIntervalSeconds']

            # Health check timeout
            if 'HealthCheckTimeoutSeconds' in params and tg['HealthCheckTimeoutSeconds'] != params['HealthCheckTimeoutSeconds']:
                hc_params['HealthCheckTimeoutSeconds'] = params['HealthCheckTimeoutSeconds']

            # Healthy threshold
            if 'HealthyThresholdCount' in params and tg['HealthyThresholdCount'] != params['HealthyThresholdCount']:
                hc_params['HealthyThresholdCount'] = params['HealthyThresholdCount']

            # Unhealthy threshold
            if 'UnhealthyThresholdCount' in params and tg['UnhealthyThresholdCount'] != params['UnhealthyThresholdCount']:
                hc_params['UnhealthyThresholdCount'] = params['UnhealthyThresholdCount']

            # Matcher (successful response codes)
            current_matcher_list = tg['Matcher']['HttpCode'].split(',')
            requested_matcher_list = params['Matcher']['HttpCode'].split(',')
            if set(current_matcher_list) != set(requested_matcher_list):
                hc_params['Matcher'] = {}
                hc_params['Matcher']['HttpCode'] = ','.join(requested_matcher_list)

            try:
                if hc_params:
                    connection.modify_target_group(TargetGroupArn=tg['TargetGroupArn'], **hc_params)
                    changed = True
            except (ClientError, NoCredentialsError) as e:
                module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

        if module.params.get("targets"):
            params['Targets'] = module.params.get("targets")

            # get list of current target instances. I can't see anything like a describe targets in the doco so
            # describe_target_health seems to be the only way to get them

            try:
                current_targets = connection.describe_target_health(TargetGroupArn=tg['TargetGroupArn'])
            except (ClientError, NoCredentialsError) as e:
                module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

            current_instances = current_targets['TargetHealthDescriptions']
            current_instance_ids = []

            for instance in current_targets['TargetHealthDescriptions']:
                current_instance_ids.append(instance['Target']['Id'])

            new_instance_ids = []
            for instance in params['Targets']:
                new_instance_ids.append(instance['Id'])

            add_instances = diff_list(new_instance_ids, current_instance_ids)

            if add_instances:
                instances_to_add = []
                for target in params['Targets']:
                    if target['Id'] in add_instances:
                        instances_to_add.append(target)

                changed = True
                try:
                    connection.register_targets(TargetGroupArn=tg['TargetGroupArn'], Targets=instances_to_add)
                except (ClientError, NoCredentialsError) as e:
                    module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

                if module.params.get("wait"):
                    status_achieved, registered_instances = wait_for_status(connection, module, tg['TargetGroupArn'], instances_to_add, 'healthy')
                    if not status_achieved:
                        module.fail_json(msg='Error waiting for target registration - please check the AWS console')


            remove_instances = diff_list(current_instance_ids, new_instance_ids)

            if remove_instances:
                instances_to_remove = []
                for target in current_targets['TargetHealthDescriptions']:
                    if target['Target']['Id'] in remove_instances:
                        instances_to_remove.append({'Id': target['Target']['Id'], 'Port': target['Target']['Port'] })

                changed = True
                try:
                    connection.deregister_targets(TargetGroupArn=tg['TargetGroupArn'], Targets=instances_to_remove)
                except (ClientError, NoCredentialsError) as e:
                    module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

                if module.params.get("wait"):
                    status_achieved, registered_instances = wait_for_status(connection, module, tg['TargetGroupArn'], instances_to_remove, 'unused')
                    if not status_achieved:
                        module.fail_json(msg='Error waiting for target deregistration - please check the AWS console')

        else:  
            try:
                current_targets = connection.describe_target_health(TargetGroupArn=tg['TargetGroupArn'])
            except (ClientError, NoCredentialsError) as e:
                module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

            current_instances = current_targets['TargetHealthDescriptions']

            if current_instances:
                instances_to_remove = []
                for target in current_targets['TargetHealthDescriptions']:
                    instances_to_remove.append({'Id': target['Target']['Id'], 'Port': target['Target']['Port'] })

                changed = True
                try:
                    connection.deregister_targets(TargetGroupArn=tg['TargetGroupArn'], Targets=instances_to_remove)
                except (ClientError, NoCredentialsError) as e:
                    module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

                if module.params.get("wait"):
                    status_achieved, registered_instances = wait_for_status(connection, module, tg['TargetGroupArn'], instances_to_remove, 'unused')
                    if not status_achieved:
                        module.fail_json(msg='Error waiting for target deregistration - please check the AWS console')

    else:
        try:
            connection.create_target_group(**params)
            changed = True
        except (ClientError, NoCredentialsError) as e:
            module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

        tg = get_target_group(connection, module)

        if module.params.get("targets"):
            params['Targets'] = module.params.get("targets")
            try:
                connection.register_targets(TargetGroupArn=tg['TargetGroupArn'], Targets=params['Targets'])
            except (ClientError, NoCredentialsError) as e:
                module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

            if module.params.get("wait"):
                status_achieved, registered_instances = wait_for_status(connection, module, tg['TargetGroupArn'], params['Targets'], 'healthy')
                if not status_achieved:
                    module.fail_json(msg='Error waiting for target registration - please check the AWS console')

    # Get the target group again
    tg = get_target_group(connection, module)

    module.exit_json(changed=changed, target_group=camel_dict_to_snake_dict(tg))


def delete_target_group(connection, module):

    changed = False
    tg = get_target_group(connection, module)

    if tg:
        try:
            connection.delete_target_group(TargetGroupArn=tg['TargetGroupArn'])
            changed = True
        except (ClientError, NoCredentialsError) as e:
            module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

    module.exit_json(changed=changed)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True, type='str'),
            protocol=dict(required=False, choices=['http', 'https'], type='str'),
            port=dict(required=False, type='int'),
            vpc_id=dict(required=False, type='str'),
            health_check_protocol=dict(required=False, choices=['http', 'https'], type='str'),
            health_check_port=dict(required=False, type='int'),
            health_check_path=dict(required=False, default=None, type='str'),
            health_check_interval=dict(required=False, default=30, type='int'),
            health_check_timeout=dict(required=False, default=5, type='int'),
            healthy_threshold_count=dict(required=False, default=5, type='int'),
            unhealthy_threshold_count=dict(required=False, default=2, type='int'),
            state=dict(required=True, choices=['present', 'absent'], type='str'),
            successful_response_codes=dict(required=False, default='200', type='str'),
            targets=dict(required=False, type='list'),
            wait_timeout=dict(required=False, type='int'),
            wait=dict(required=False, type='bool')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=[
                               ('state', 'present', ['protocol', 'port', 'vpc_id'])
                           ]
                           )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        connection = boto3_conn(module, conn_type='client', resource='elbv2', region=region, endpoint=ec2_url, **aws_connect_params)
    else:
        module.fail_json(msg="region must be specified")

    state = module.params.get("state")

    if state == 'present':
        create_or_update_target_group(connection, module)
    else:
        delete_target_group(connection, module)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
