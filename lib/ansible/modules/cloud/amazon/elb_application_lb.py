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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: elb_application_lb
short_description: Manage an Application load balancer
description:
    - Manage an AWS Application Elastic Load Balancer. See U(https://aws.amazon.com/blogs/aws/new-aws-application-load-balancer/) for details.
version_added: "2.4"
author: "Rob White (@wimnat)"
options:
  access_logs_enabled:
    description:
      - "Whether or not to enable access logs. When true, I(access_logs_s3_bucket) must be set."
    required: false
    choices: [ 'yes', 'no' ]
  access_logs_s3_bucket:
    description:
      - The name of the S3 bucket for the access logs. This attribute is required if access logs in Amazon S3 are enabled. The bucket must exist in the same 
        region as the load balancer and have a bucket policy that grants Elastic Load Balancing permission to write to the bucket.
    required: false
  access_logs_s3_prefix:
    description:
      - The prefix for the location in the S3 bucket. If you don't specify a prefix, the access logs are stored in the root of the bucket.
    required: false
  deletion_protection:
    description:
      - Indicates whether deletion protection for the ELB is enabled.
    required: false
    default: no
    choices: [ 'yes', 'no' ]
  idle_timeout:
    description:
      - The number of seconds to wait before an idle connection is closed.
    required: false
    default: 60
  listeners:
    description:
      - A list of dicts containing listeners to attach to the ELB. See examples for detail of the dict required. Note that listener keys
        are CamelCased.
    required: false
  name:
    description:
      - The name of the load balancer. This name must be unique within your AWS account, can have a maximum of 32 characters, must contain only alphanumeric 
        characters or hyphens, and must not begin or end with a hyphen.
    required: true
  purge_tags:
    description:
      - If yes, existing tags will be purged from the resource to match exactly what is defined by tags parameter. If the tag parameter is not set then tags 
        will not be modified.
    required: false
    default: yes
    choices: [ 'yes', 'no' ]
  subnets:
    description:
      - A list of the IDs of the subnets to attach to the load balancer. You can specify only one subnet per Availability Zone. You must specify subnets from 
        at least two Availability Zones. Required if state=present.
    required: false
  security_groups:
    description:
      - A list of the names or IDs of the security groups to assign to the load balancer. Required if state=present.
    required: false
    default: []
  scheme:
    description:
      - Internet-facing or internal load balancer. An ELB scheme can not be modified after creation.
    required: false
    default: internet-facing
    choices: [ 'internet-facing', 'internal' ]
  state:
    description:
      - Create or destroy the load balancer.
    required: true
    choices: [ 'present', 'absent' ]
  tags:
    description:
      - A dictionary of one or more tags to assign to the load balancer.
    required: false
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create an ELB and attach a listener
- elb_application_lb:
    name: myelb
    security_groups:
      - sg-12345678
      - my-sec-group
    subnets:
      - subnet-012345678
      - subnet-abcdef000
    listeners:
      - Protocol: HTTP # Required. The protocol for connections from clients to the load balancer (HTTP or HTTPS) (case-sensitive).
        Port: 80 # Required. The port on which the load balancer is listening.
        # The security policy that defines which ciphers and protocols are supported. The default is the current predefined security policy.
        SslPolicy: ELBSecurityPolicy-2015-05
        Certificates: # The ARN of the certificate (only one certficate ARN should be provided)
          - CertificateArn: arn:aws:iam::12345678987:server-certificate/test.domain.com
        DefaultActions:
          - Type: forward # Required. Only 'forward' is accepted at this time
            TargetGroupName: # Required. The name of the target group
    state: present

# Create an ELB and attach a listener with logging enabled
- elb_application_lb:
    access_logs_enabled: yes
    access_logs_s3_bucket: mybucket
    access_logs_s3_prefix: "/logs"
    name: myelb
    security_groups:
      - sg-12345678
      - my-sec-group
    subnets:
      - subnet-012345678
      - subnet-abcdef000
    listeners:
      - Protocol: HTTP # Required. The protocol for connections from clients to the load balancer (HTTP or HTTPS) (case-sensitive).
        Port: 80 # Required. The port on which the load balancer is listening.
        # The security policy that defines which ciphers and protocols are supported. The default is the current predefined security policy.
        SslPolicy: ELBSecurityPolicy-2015-05
        Certificates: # The ARN of the certificate (only one certficate ARN should be provided)
          - CertificateArn: arn:aws:iam::12345678987:server-certificate/test.domain.com
        DefaultActions:
          - Type: forward # Required. Only 'forward' is accepted at this time
            TargetGroupName: # Required. The name of the target group
    state: present

# Create an ALB with listeners and rules
- elb_application_lb:
    name: test-alb
    subnets:
      - subnet-12345678
      - subnet-87654321
    security_groups:
     - sg-12345678
    scheme: internal
    listeners:
      - Protocol: HTTPS
        Port: 443
        DefaultActions:
          - Type: forward
            TargetGroupName: test-target-group
        Certificates:
          - CertificateArn: arn:aws:iam::12345678987:server-certificate/test.domain.com
        SslPolicy: ELBSecurityPolicy-2015-05
        Rules:
          - Conditions:
            - Field: path-pattern
              Values:
                - '/test'
            Priority: '1'
            Actions:
              - TargetGroupName: test-target-group
                Type: forward
    state: present

# Remove an ELB
- elb_application_lb:
    name: myelb
    state: absent

'''

RETURN = '''
access_logs_s3_bucket:
    description: The name of the S3 bucket for the access logs.
    returned: when state is present
    type: string
    sample: mys3bucket
access_logs_s3_enabled:
    description: Indicates whether access logs stored in Amazon S3 are enabled.
    returned: when state is present
    type: string
    sample: true
access_logs_s3_prefix:
    description: The prefix for the location in the S3 bucket.
    returned: when state is present
    type: string
    sample: /my/logs
availability_zones:
    description: The Availability Zones for the load balancer.
    returned: when state is present
    type: list
    sample: "[{'subnet_id': 'subnet-aabbccddff', 'zone_name': 'ap-southeast-2a'}]"
canonical_hosted_zone_id:
    description: The ID of the Amazon Route 53 hosted zone associated with the load balancer.
    returned: when state is present
    type: string
    sample: ABCDEF12345678
created_time:
    description: The date and time the load balancer was created.
    returned: when state is present
    type: string
    sample: "2015-02-12T02:14:02+00:00"
deletion_protection_enabled:
    description: Indicates whether deletion protection is enabled.
    returned: when state is present
    type: string
    sample: true
dns_name:
    description: The public DNS name of the load balancer.
    returned: when state is present
    type: string
    sample: internal-my-elb-123456789.ap-southeast-2.elb.amazonaws.com
idle_timeout_timeout_seconds:
    description: The idle timeout value, in seconds.
    returned: when state is present
    type: string
    sample: 60
ip_address_type:
    description:  The type of IP addresses used by the subnets for the load balancer.
    returned: when state is present
    type: string
    sample: ipv4
listeners:
    description: Information about the listeners.
    returned: when state is present
    type: complex
    contains:
        listener_arn:
            description: The Amazon Resource Name (ARN) of the listener.
            returned: when state is present
            type: string
            sample: ""
        load_balancer_arn:
            description: The Amazon Resource Name (ARN) of the load balancer.
            returned: when state is present
            type: string
            sample: ""
        port:
            description: The port on which the load balancer is listening.
            returned: when state is present
            type: int
            sample: 80
        protocol:
            description: The protocol for connections from clients to the load balancer.
            returned: when state is present
            type: string
            sample: HTTPS
        certificates:
            description: The SSL server certificate.
            returned: when state is present
            type: complex
            contains:
                certificate_arn:
                    description: The Amazon Resource Name (ARN) of the certificate.
                    returned: when state is present
                    type: string
                    sample: ""
        ssl_policy:
            description: The security policy that defines which ciphers and protocols are supported.
            returned: when state is present
            type: string
            sample: ""
        default_actions:
            description: The default actions for the listener.
            returned: when state is present
            type: string
            contains:
                type:
                    description: The type of action.
                    returned: when state is present
                    type: string
                    sample: ""
                target_group_arn:
                    description: The Amazon Resource Name (ARN) of the target group.
                    returned: when state is present
                    type: string
                    sample: ""
load_balancer_arn:
    description: The Amazon Resource Name (ARN) of the load balancer.
    returned: when state is present
    type: string
    sample: arn:aws:elasticloadbalancing:ap-southeast-2:0123456789:loadbalancer/app/my-elb/001122334455
load_balancer_name:
    description: The name of the load balancer.
    returned: when state is present
    type: string
    sample: my-elb
scheme:
    description: Internet-facing or internal load balancer.
    returned: when state is present
    type: string
    sample: internal
security_groups:
    description: The IDs of the security groups for the load balancer.
    returned: when state is present
    type: list
    sample: ['sg-0011223344']
state:
    description: The state of the load balancer.
    returned: when state is present
    type: dict
    sample: "{'code': 'active'}"
tags:
    description: The tags attached to the load balancer.
    returned: when state is present
    type: dict
    sample: "{
        'Tag': 'Example'
    }"
type:
    description: The type of load balancer.
    returned: when state is present
    type: string
    sample: application
vpc_id:
    description: The ID of the VPC for the load balancer.
    returned: when state is present
    type: string
    sample: vpc-0011223344
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, camel_dict_to_snake_dict, ec2_argument_spec, get_ec2_security_group_ids_from_names, \
    ansible_dict_to_boto3_tag_list, boto3_tag_list_to_ansible_dict, compare_aws_tags, HAS_BOTO3
import collections
from copy import deepcopy
import traceback

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    HAS_BOTO3 = False


def convert(data):
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.items()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data


def convert_tg_name_arn(connection, module, tg_name):

    try:
        response = connection.describe_target_groups(Names=[tg_name])
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    tg_arn = response['TargetGroups'][0]['TargetGroupArn']

    return tg_arn


def convert_tg_arn_name(connection, module, tg_arn):

    try:
        response = connection.describe_target_groups(TargetGroupArns=[tg_arn])
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    tg_name = response['TargetGroups'][0]['TargetGroupName']

    return tg_name


def wait_for_status(connection, module, elb_arn, status):
    polling_increment_secs = 15
    max_retries = (module.params.get('wait_timeout') / polling_increment_secs)
    status_achieved = False

    for x in range(0, max_retries):
        try:
            response = connection.describe_load_balancers(LoadBalancerArns=[elb_arn])
            if response['LoadBalancers'][0]['State']['Code'] == status:
                status_achieved = True
                break
            else:
                time.sleep(polling_increment_secs)
        except ClientError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    result = response
    return status_achieved, result


def _get_subnet_ids_from_subnet_list(subnet_list):

    subnet_id_list = []
    for subnet in subnet_list:
        subnet_id_list.append(subnet['SubnetId'])

    return subnet_id_list


def get_elb_listeners(connection, module, elb_arn):

    try:
        return connection.describe_listeners(LoadBalancerArn=elb_arn)['Listeners']
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def get_elb_attributes(connection, module, elb_arn):

    try:
        elb_attributes = boto3_tag_list_to_ansible_dict(connection.describe_load_balancer_attributes(LoadBalancerArn=elb_arn)['Attributes'])
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    # Replace '.' with '_' in attribute key names to make it more Ansibley
    for k, v in elb_attributes.items():
        elb_attributes[k.replace('.', '_')] = v
        del elb_attributes[k]

    return elb_attributes


def get_elb(connection, module):
    """
    Get an application load balancer based on name. If not found, return None
    :param connection: ELBv2 boto3 connection
    :param module: Ansible module object
    :return: Dict of load balancer attributes or None if not found
    """

    try:
        load_balancer_paginator = connection.get_paginator('describe_load_balancers')
        return (load_balancer_paginator.paginate(Names=[module.params.get("name")]).build_full_result())['LoadBalancers'][0]
    except ClientError as e:
        if e.response['Error']['Code'] == 'LoadBalancerNotFound':
            return None
        else:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def create_or_update_elb_listeners(connection, module, elb):
    """Create or update ELB listeners. Return true if changed, else false"""

    listener_changed = False
    listeners = module.params.get("listeners")

    # create a copy of original list as we remove list elements for initial comparisons
    listeners_rules = deepcopy(listeners)
    listener_matches = False

    if listeners is not None:
        current_listeners = get_elb_listeners(connection, module, elb['LoadBalancerArn'])
        # If there are no current listeners we can just create the new ones
        current_listeners_array = []

        if current_listeners:
            # the describe_listeners action returns keys as unicode so I've converted them to string for easier comparison
            for current_listener in current_listeners:
                del current_listener['ListenerArn']
                del current_listener['LoadBalancerArn']
                current_listeners_s = convert(current_listener)
                current_listeners_array.append(current_listeners_s)

            for curr_listener in current_listeners_array:
                for default_action in curr_listener['DefaultActions']:
                    default_action['TargetGroupName'] = convert_tg_arn_name(connection, module, default_action['TargetGroupArn'])
                    del default_action['TargetGroupArn']

            listeners_to_add = []

            # remove rules from the comparison. We will handle them separately.
            for listener in listeners:
                if 'Rules' in listener.keys():
                    del listener['Rules']

            for listener in listeners:
                if listener not in current_listeners_array:
                    listeners_to_add.append(listener)

            listeners_to_remove = []
            for current_listener in current_listeners_array:
                if current_listener not in listeners:
                    listeners_to_remove.append(current_listener)

            # for listeners to remove, we need to lookup the arns using unique listener attributes. Port must be unique for
            # all listeners so I've retrieved the ARN based on Port.
            if listeners_to_remove:
                arns_to_remove = []
                current_listeners = connection.describe_listeners(LoadBalancerArn=elb['LoadBalancerArn'])['Listeners']
                listener_changed = True
                for listener in listeners_to_remove:
                    for current_listener in current_listeners:
                        if current_listener['Port'] == listener['Port']:
                            arns_to_remove.append(current_listener['ListenerArn'])

                for arn in arns_to_remove:
                    connection.delete_listener(ListenerArn=arn)

            if listeners_to_add:
                listener_changed = True
                for listener in listeners_to_add:
                    listener['LoadBalancerArn'] = elb['LoadBalancerArn']
                    for default_action in listener['DefaultActions']:
                        default_action['TargetGroupArn'] = convert_tg_name_arn(connection, module, default_action['TargetGroupName'])
                        del default_action['TargetGroupName']
                    connection.create_listener(**listener)

            # Lookup the listeners again and this time we will retain the rules so we can comapre for changes:
            current_listeners = connection.describe_listeners(LoadBalancerArn=elb['LoadBalancerArn'])['Listeners']

            # lookup the arns of the current listeners
            for listener in listeners_rules:
                # we only want listeners which have rules defined
                if 'Rules' in listener.keys():
                    for current_listener in current_listeners:
                        if current_listener['Port'] == listener['Port']:
                            # look up current rules for the current listener
                            current_rules = connection.describe_rules(ListenerArn=current_listener['ListenerArn'])['Rules']
                            current_rules_array = []
                            for rules in current_rules:
                                del rules['RuleArn']
                                del rules['IsDefault']
                                if rules['Priority'] != 'default':
                                    current_rules_s = convert(rules)
                                    current_rules_array.append(current_rules_s)

                            for curr_rule in current_rules_array:
                                for action in curr_rule['Actions']:
                                    action['TargetGroupName'] = convert_tg_arn_name(connection, module, action['TargetGroupArn'])
                                    del action['TargetGroupArn']

                            rules_to_remove = []
                            for current_rule in current_rules_array:
                                if listener['Rules']:
                                    if current_rule not in listener['Rules']:
                                        rules_to_remove.append(current_rule)
                                else:
                                    rules_to_remove.append(current_rule)

                            # for rules to remove we need to lookup the rule arn using unique attributes.
                            # I have used path and priority
                            if rules_to_remove:
                                rule_arns_to_remove = []
                                current_rules = connection.describe_rules(ListenerArn=current_listener['ListenerArn'])['Rules']
                                # listener_changed = True
                                for rules in rules_to_remove:
                                    for current_rule in current_rules:
                                        # if current_rule['Priority'] != 'default':
                                        if current_rule['Conditions'] == rules['Conditions'] and current_rule['Priority'] == rules['Priority']:
                                            rule_arns_to_remove.append(current_rule['RuleArn'])

                                listener_changed = True
                                for arn in rule_arns_to_remove:
                                    connection.delete_rule(RuleArn=arn)

                            rules_to_add = []
                            if listener['Rules']:
                                for rules in listener['Rules']:
                                    if rules not in current_rules_array:
                                        rules_to_add.append(rules)

                            if rules_to_add:
                                listener_changed = True
                                for rule in rules_to_add:
                                    rule['ListenerArn'] = current_listener['ListenerArn']
                                    rule['Priority'] = int(rule['Priority'])
                                    for action in rule['Actions']:
                                        action['TargetGroupArn'] = convert_tg_name_arn(connection, module, action['TargetGroupName'])
                                        del action['TargetGroupName']
                                    connection.create_rule(**rule)

        else:
            for listener in listeners:
                listener['LoadBalancerArn'] = elb['LoadBalancerArn']
                if 'Rules' in listener.keys():
                    del listener['Rules']

                # handle default
                for default_action in listener['DefaultActions']:
                    default_action['TargetGroupArn'] = convert_tg_name_arn(connection, module, default_action['TargetGroupName'])
                    del default_action['TargetGroupName']

                connection.create_listener(**listener)
                listener_changed = True

            # lookup the new listeners
            current_listeners = connection.describe_listeners(LoadBalancerArn=elb['LoadBalancerArn'])['Listeners']

            for current_listener in current_listeners:
                for listener in listeners_rules:
                    if current_listener['Port'] == listener['Port']:
                        if 'Rules' in listener.keys():
                            for rules in listener['Rules']:
                                rules['ListenerArn'] = current_listener['ListenerArn']
                                rules['Priority'] = int(rules['Priority'])
                                for action in rules['Actions']:
                                    action['TargetGroupArn'] = convert_tg_name_arn(connection, module, action['TargetGroupName'])
                                    del action['TargetGroupName']
                                connection.create_rule(**rules)

    # listeners is none. If we have any current listeners we need to remove them
    else:
        current_listeners = connection.describe_listeners(LoadBalancerArn=elb['LoadBalancerArn'])['Listeners']
        if current_listeners:
            for listener in current_listeners:
                listener_changed = True
                connection.delete_listener(ListenerArn=listener['ListenerArn'])

    return listener_changed


def create_or_update_elb(connection, connection_ec2, module):
    """Create ELB or modify main attributes. json_exit here"""

    changed = False
    new_load_balancer = False
    params = dict()
    params['Name'] = module.params.get("name")
    params['Subnets'] = module.params.get("subnets")
    try:
        params['SecurityGroups'] = get_ec2_security_group_ids_from_names(module.params.get('security_groups'), connection_ec2, boto3=True)
    except ValueError as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except NoCredentialsError as e:
        module.fail_json(msg="AWS authentication problem. " + e.message, exception=traceback.format_exc())

    params['Scheme'] = module.params.get("scheme")
    if module.params.get("tags"):
        params['Tags'] = ansible_dict_to_boto3_tag_list(module.params.get("tags"))
    purge_tags = module.params.get("purge_tags")
    access_logs_enabled = module.params.get("access_logs_enabled")
    access_logs_s3_bucket = module.params.get("access_logs_s3_bucket")
    access_logs_s3_prefix = module.params.get("access_logs_s3_prefix")
    deletion_protection = module.params.get("deletion_protection")
    idle_timeout = module.params.get("idle_timeout")

    # Does the ELB currently exist?
    elb = get_elb(connection, module)

    if elb:
        # ELB exists so check subnets, security groups and tags match what has been passed

        # Subnets
        if set(_get_subnet_ids_from_subnet_list(elb['AvailabilityZones'])) != set(params['Subnets']):
            try:
                connection.set_subnets(LoadBalancerArn=elb['LoadBalancerArn'], Subnets=params['Subnets'])
            except ClientError as e:
                module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
            changed = True

        # Security Groups
        if set(elb['SecurityGroups']) != set(params['SecurityGroups']):
            try:
                connection.set_security_groups(LoadBalancerArn=elb['LoadBalancerArn'], SecurityGroups=params['SecurityGroups'])
            except ClientError as e:
                module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
            changed = True

        # Tags - only need to play with tags if tags parameter has been set to something
        if module.params.get("tags"):
            try:
                elb_tags = connection.describe_tags(ResourceArns=[elb['LoadBalancerArn']])['TagDescriptions'][0]['Tags']
            except ClientError as e:
                module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

            # Delete necessary tags
            tags_need_modify, tags_to_delete = compare_aws_tags(boto3_tag_list_to_ansible_dict(elb_tags), boto3_tag_list_to_ansible_dict(params['Tags']),
                                                                purge_tags)
            if tags_to_delete:
                try:
                    connection.remove_tags(ResourceArns=[elb['LoadBalancerArn']], TagKeys=tags_to_delete)
                except ClientError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
                changed = True

            # Add/update tags
            if tags_need_modify:
                try:
                    connection.add_tags(ResourceArns=[elb['LoadBalancerArn']], Tags=params['Tags'])
                except ClientError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
                changed = True

    else:
        try:
            elb = connection.create_load_balancer(**params)['LoadBalancers'][0]
            changed = True
            new_load_balancer = True
        except ClientError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

        if module.params.get("wait"):
            status_achieved, new_elb = wait_for_status(connection, module, elb['LoadBalancerArn'], 'active')

    # Now set ELB attributes. Use try statement here so we can remove the ELB if this stage fails
    update_attributes = []

    # Get current attributes
    current_elb_attributes = get_elb_attributes(connection, module, elb['LoadBalancerArn'])

    if access_logs_enabled and current_elb_attributes['access_logs_s3_enabled'] != "true":
        update_attributes.append({'Key': 'access_logs.s3.enabled', 'Value': "true"})
    if not access_logs_enabled and current_elb_attributes['access_logs_s3_enabled'] != "false":
        update_attributes.append({'Key': 'access_logs.s3.enabled', 'Value': 'false'})
    if access_logs_s3_bucket is not None and access_logs_s3_bucket != current_elb_attributes['access_logs_s3_bucket']:
        update_attributes.append({'Key': 'access_logs.s3.bucket', 'Value': access_logs_s3_bucket})
    if access_logs_s3_prefix is not None and access_logs_s3_prefix != current_elb_attributes['access_logs_s3_prefix']:
        update_attributes.append({'Key': 'access_logs.s3.prefix', 'Value': access_logs_s3_prefix})
    if deletion_protection and current_elb_attributes['deletion_protection_enabled'] != "true":
        update_attributes.append({'Key': 'deletion_protection.enabled', 'Value': "true"})
    if not deletion_protection and current_elb_attributes['deletion_protection_enabled'] != "false":
        update_attributes.append({'Key': 'deletion_protection.enabled', 'Value': "false"})
    if idle_timeout is not None and str(idle_timeout) != current_elb_attributes['idle_timeout_timeout_seconds']:
        update_attributes.append({'Key': 'idle_timeout.timeout_seconds', 'Value': str(idle_timeout)})

    if update_attributes:
        try:
            connection.modify_load_balancer_attributes(LoadBalancerArn=elb['LoadBalancerArn'], Attributes=update_attributes)
            changed = True
        except ClientError as e:
            # Something went wrong setting attributes. If this ELB was created during this task, delete it to leave a consistent state
            if new_load_balancer:
                connection.delete_load_balancer(LoadBalancerArn=elb['LoadBalancerArn'])
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    # Now, if required, set ELB listeners. Use try statement here so we can remove the ELB if this stage fails
    try:
        listener_changed = create_or_update_elb_listeners(connection, module, elb)
        if listener_changed:
            changed = True
    except ClientError as e:
        # Something went wrong setting listeners. If this ELB was created during this task, delete it to leave a consistent state
        if new_load_balancer:
            connection.delete_load_balancer(LoadBalancerArn=elb['LoadBalancerArn'])
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    # Get the ELB again
    elb = get_elb(connection, module)

    # Get the ELB listeners again
    elb['listeners'] = get_elb_listeners(connection, module, elb['LoadBalancerArn'])

    # Get the ELB attributes again
    elb.update(get_elb_attributes(connection, module, elb['LoadBalancerArn']))

    # Convert to snake_case
    snaked_elb = camel_dict_to_snake_dict(elb)

    # Get the tags of the ELB
    elb_tags = connection.describe_tags(ResourceArns=[elb['LoadBalancerArn']])['TagDescriptions'][0]['Tags']
    snaked_elb['tags'] = boto3_tag_list_to_ansible_dict(elb_tags)

    module.exit_json(changed=changed, **snaked_elb)


def delete_elb(connection, module):

    changed = False
    elb = get_elb(connection, module)

    if elb:
        try:
            connection.delete_load_balancer(LoadBalancerArn=elb['LoadBalancerArn'])
            changed = True
        except ClientError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
        except NoCredentialsError as e:
            module.fail_json(msg="AWS authentication problem. " + e.message, exception=traceback.format_exc())

    module.exit_json(changed=changed)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            access_logs_enabled=dict(required=False, type='bool'),
            access_logs_s3_bucket=dict(required=False, type='str'),
            access_logs_s3_prefix=dict(required=False, type='str'),
            deletion_protection=dict(required=False, default=False, type='bool'),
            idle_timeout=dict(required=False, type='int'),
            listeners=dict(required=False, type='list'),
            name=dict(required=True, type='str'),
            purge_tags=dict(required=False, default=True, type='bool'),
            subnets=dict(required=False, type='list'),
            security_groups=dict(required=False, type='list'),
            scheme=dict(required=False, default='internet-facing', choices=['internet-facing', 'internal']),
            state=dict(required=True, choices=['present', 'absent'], type='str'),
            tags=dict(required=False, default={}, type='dict'),
            wait_timeout=dict(required=False, type='int'),
            wait=dict(required=False, type='bool')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=[
                               ('state', 'present', ['subnets', 'security_groups'])
                           ],
                           required_together=(
                               ['access_logs_enabled', 'access_logs_s3_bucket', 'access_logs_s3_prefix']
                           )
                           )

    # Quick check of listeners parameters
    listeners = module.params.get("listeners")
    if listeners is not None:
        for listener in listeners:
            for key in listener.keys():
                if key not in ['Protocol', 'Port', 'SslPolicy', 'Certificates', 'DefaultActions', 'Rules']:
                    module.fail_json(msg="listeners parameter contains invalid dict keys. Should be one of 'Protocol', "
                                         "'Port', 'SslPolicy', 'Certificates', 'DefaultActions', 'Rules'.")

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        connection = boto3_conn(module, conn_type='client', resource='elbv2', region=region, endpoint=ec2_url, **aws_connect_params)
        connection_ec2 = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)
    else:
        module.fail_json(msg="region must be specified")

    state = module.params.get("state")

    if state == 'present':
        create_or_update_elb(connection, connection_ec2, module)
    else:
        delete_elb(connection, module)

if __name__ == '__main__':
    main()
