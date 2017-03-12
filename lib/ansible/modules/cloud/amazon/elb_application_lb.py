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
                    'supported_by': 'committer',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: elb_application_lb
short_description: Manage an Application load balancer
description:
    - Manage an AWS Application Elastic Load Balancer. See U(https://aws.amazon.com/blogs/aws/new-aws-application-load-balancer/) for details.
version_added: "2.3"
author: "Rob White (@wimnat)"
options:
  access_logs_s3_bucket:
    description:
      - "The name of the S3 bucket for the access logs. This attribute is required if access logs in Amazon S3 are enabled. The bucket must exist in the same \
      region as the load balancer and have a bucket policy that grants Elastic Load Balancing permission to write to the bucket."
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
      - A list of dicts containing listeners to attach to the ELB. See examples for a detail of the dict required.
    required: false
  name:
    description:
      - The name of the load balancer. This name must be unique within your AWS account, can have a maximum of 32 characters, must contain only alphanumeric characters or hyphens, and must not begin or end with a hyphen.
    required: true
  purge_tags:
    description:
      - If yes, existing tags will be purged from the resource to match exactly what is defined by tags parameter. If the tag parameter is not set then tags will not be modified.
    required: false
    default: yes
    choices: [ 'yes', 'no' ]
  subnets:
    description:
      - "A list of the IDs of the subnets to attach to the load balancer. You can specify only one subnet per Availability Zone. You must specify subnets from \
      at least two Availability Zones. Required if state=present."
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
- name: elb_application_lb
    name: myelb
    security_groups:
      - sg-12345678
      - my-sec-group
    subnets:
      - subnet-012345678
      - subnet-abcdef000
    listeners:
      - protocol: http # Required. The protocol for connections from clients to the load balancer (http or https).
        port: 80 # Required. The port on which the load balancer is listening.
        ssl_policy: # The security policy that defines which ciphers and protocols are supported. The default is the current predefined security policy.
        certificates: # The ARN of the certificate (only one certficate ARN should be provided)
        default_actions:
          - type: forward # Required. Only 'forward' is accepted at this time
            target_group_arn: # Required. The ARN of the target group
    state: present

# Create an ELB and attach a listener and attributes
- name: elb_application_lb
    name: myelb
    security_groups:
      - sg-12345678
      - my-sec-group
    subnets:
      - subnet-012345678
      - subnet-abcdef000
    listeners:
      - protocol: http # Required. The protocol for connections from clients to the load balancer (http or https).
        port: 80 # Required. The port on which the load balancer is listening.
        ssl_policy: # The security policy that defines which ciphers and protocols are supported. The default is the current predefined security policy.
        certificates: # The ARN of the certificate (only one certficate ARN should be provided)
        default_actions:
          - type: forward # Required. Only 'forward' is accepted at this time
            target_group_arn: # Required. The ARN of the target group
    attributes:
        - Key: idle_timeout.timeout_seconds
          Value: '60'
    state: present

# Create an ALB with listeners and rules
- name: Create an ALB load balancer
  elb_lb_application:
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
'''

RETURN = '''
load_balancer:
    load_balancer_arn:
        description: The Amazon Resource Name (ARN) of the load balancer.
        type: string
        sample: TBA
    dns_name:
        description: The public DNS name of the load balancer.
        type: string
        sample: TBA
    canonical_hosted_zone_id:
        description: The ID of the Amazon Route 53 hosted zone associated with the load balancer.
        type: string
        sample: TBA
    created_time:
        description: The date and time the load balancer was created.
        type: datetime
        sample: 2015-02-12T02:14:02+00:00
    load_balancer_name:
        description: The name of the load balancer.
        type: string
        sample: TBA
    scheme:
        description: Internet-facing or internal load balancer.
        type: string
        sample: internet-facing
    vpc_id:
        description: The ID of the VPC for the load balancer.
        type: string
        sample: My important backup
    state:
        description: The state of the load balancer.
        type: dict
        sample: TBA
    type:
        description: The type of load balancer.
        type: string
        sample: application
    availability_zones:
        description: The Availability Zones for the load balancer.
        type: list
        sample: TBA
    security_groups:
        description: The IDs of the security groups for the load balancer.
        type: list
        sample: TBA
    tags:
        description: The tags attached to the load balancer.
        type: dict
        sample: "{
            'Tag': 'Example'
        }"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, camel_dict_to_snake_dict, ec2_argument_spec, get_ec2_security_group_ids_from_names, \
    ansible_dict_to_boto3_tag_list, boto3_tag_list_to_ansible_dict
import ast
import collections
from copy import deepcopy
import traceback

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
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
        module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

    tg_arn =response['TargetGroups'][0]['TargetGroupArn']

    return tg_arn


def convert_tg_arn_name(connection, module, tg_arn):
        
    try:
        response = connection.describe_target_groups(TargetGroupArns=[tg_arn])
    except ClientError as e:
        module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

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
            module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

    result = response
    return status_achieved, result


def _compare_tags(current_tags, proposed_tags, purge):
    """Take a list of current tags and proposed tags and return tags to set and tags to delete. Also takes a purge option."""

    tag_keys_to_delete = []
    current_tags = boto3_tag_list_to_ansible_dict(current_tags)
    proposed_tags = boto3_tag_list_to_ansible_dict(proposed_tags)
    for key in current_tags.keys():
        if key not in proposed_tags and purge:
            tag_keys_to_delete.append(key)

    # Remove the keys we're going to delete then compare the dicts to see if modification necessary
    for key in tag_keys_to_delete:
        del current_tags[key]

    if current_tags != proposed_tags:
        tags_need_modify = True
    else:
        tags_need_modify = False

    return tag_keys_to_delete, tags_need_modify


def _get_subnet_ids_from_subnet_list(subnet_list):

    subnet_id_list = []
    for subnet in subnet_list:
        subnet_id_list.append(subnet['SubnetId'])

    return subnet_id_list


def get_elb(connection, module):

    try:
        return connection.describe_load_balancers(Names=[module.params.get("name")])['LoadBalancers'][0]
    except (ClientError, NoCredentialsError) as e:
        if e.response['Error']['Code'] == 'LoadBalancerNotFound':
            return None
        else:
            module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))


def update_elb_attributes(connection, module, elb):
    """Update ELB attributes. Return true if changed, else false"""

    attribute_changed = False
    update_required = False
    params = dict()

    elb_attributes = connection.describe_load_balancer_attributes(LoadBalancerArn=elb['LoadBalancerArn'])
    
    if module.params.get("attributes"):
        params['Attributes'] = module.params.get("attributes")
        
        for new_attribute in params['Attributes']:
            for current_attribute in elb_attributes['Attributes']:
                if new_attribute['Key'] == current_attribute['Key']:
                    if new_attribute['Value'] != current_attribute['Value']:
                        update_required = True

    if update_required: 
        attribute_changed = True
        try:
            connection.modify_load_balancer_attributes(LoadBalancerArn=elb['LoadBalancerArn'], Attributes=params['Attributes'])
        except (ClientError, NoCredentialsError) as e:
                module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    
    return attribute_changed


def create_or_update_elb_listeners(connection, module, elb):
    """Create or update ELB listeners. Return true if changed, else false"""

    listener_changed = False
    listeners = module.params.get("listeners")
    
    # create a copy of original list as we remove list elements for initial comparisons
    listeners_rules = deepcopy(listeners)
    listener_matches = False

    if listeners is not None:
        current_listeners = connection.describe_listeners(LoadBalancerArn=elb['LoadBalancerArn'])['Listeners']
        # If there are no current listeners we can just create the new ones
        current_listeners_array=[]
        
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
            module.exit_json(list=listeners)
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
        module.fail_json(msg=str(e))
    params['Scheme'] = module.params.get("scheme")
    if module.params.get("tags"):
        params['Tags'] = ansible_dict_to_boto3_tag_list(module.params.get("tags"))
    purge_tags = module.params.get("purge_tags")

    # Does the ELB currently exist?
    elb = get_elb(connection, module)

    if elb:
        # ELB exists so check subnets, security groups and tags match what has been passed

        # Subnets
        if set(_get_subnet_ids_from_subnet_list(elb['AvailabilityZones'])) != set(params['Subnets']):
            try:
                connection.set_subnets(LoadBalancerArn=elb['LoadBalancerArn'], Subnets=params['Subnets'])
            except (ClientError, NoCredentialsError) as e:
                module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
            changed = True

        # Security Groups
        if set(elb['SecurityGroups']) != set(params['SecurityGroups']):
            try:
                connection.set_security_groups(LoadBalancerArn=elb['LoadBalancerArn'], SecurityGroups=params['SecurityGroups'])
            except (ClientError, NoCredentialsError) as e:
                module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
            changed = True

        # Tags - only need to play with tags if tags parameter has been set to something
        if module.params.get("tags"):
            try:
                elb_tags = connection.describe_tags(ResourceArns=[elb['LoadBalancerArn']])['TagDescriptions'][0]['Tags']
            except (ClientError, NoCredentialsError) as e:
                module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

            # Delete necessary tags
            tags_to_delete, tags_need_modify = _compare_tags(elb_tags, params['Tags'], purge_tags)
            if tags_to_delete:
                try:
                    connection.remove_tags(ResourceArns=[elb['LoadBalancerArn']], TagKeys=tags_to_delete)
                except (ClientError, NoCredentialsError) as e:
                    module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))
                changed = True

            # Add/update tags
            if tags_need_modify:
                try:
                    connection.add_tags(ResourceArns=[elb['LoadBalancerArn']], Tags=params['Tags'])
                except (ClientError, NoCredentialsError) as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
                changed = True

    else:
        try:
            elb = connection.create_load_balancer(**params)['LoadBalancers'][0]
            changed = True
            new_load_balancer = True
        except (ClientError, NoCredentialsError) as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
 
        if module.params.get("wait"):
            status_achieved, new_elb = wait_for_status(connection, module, elb['LoadBalancerArn'], 'active')

    # Now set ELB attributes. Use try statement here so we can remove the ELB if this stage fails
    try:
        attribute_changed = update_elb_attributes(connection, module, elb)
        if attribute_changed:
            changed = True
    except (ClientError, NoCredentialsError) as e:
        # Something went wrong setting attributes. If this ELB was created during this task, delete it to leave a consistent state
        if new_load_balancer:
            connection.delete_load_balancer(LoadBalancerArn=elb['LoadBalancerArn'])
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    # Now, if required, set ELB listeners. Use try statement here so we can remove the ELB if this stage fails
    try:
        listener_changed = create_or_update_elb_listeners(connection, module, elb)
        if listener_changed:
            changed = True
    except (ClientError, NoCredentialsError) as e:
        # Something went wrong setting listeners. If this ELB was created during this task, delete it to leave a consistent state
        if new_load_balancer:
            connection.delete_load_balancer(LoadBalancerArn=elb['LoadBalancerArn'])
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    
    # Get the ELB again
    elb = get_elb(connection, module)
    # Get the tags of the ELB
    elb_tags = connection.describe_tags(ResourceArns=[elb['LoadBalancerArn']])['TagDescriptions'][0]['Tags']
    elb['Tags'] = boto3_tag_list_to_ansible_dict(elb_tags)

    module.exit_json(changed=changed, load_balancer=camel_dict_to_snake_dict(elb))


def delete_elb(connection, module):

    changed = False
    elb = get_elb(connection, module)

    if elb:
        try:
            connection.delete_load_balancer(LoadBalancerArn=elb['LoadBalancerArn'])
            changed = True
        except (ClientError, NoCredentialsError) as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    module.exit_json(changed=changed)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
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
            attributes=dict(required=False, type='list'),
            wait_timeout=dict(required=False, type='int'),
            wait=dict(required=False, type='bool')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=[
                               ('state', 'present', ['subnets', 'security_groups'])
                           ],
                           required_together=(
                               ['access_logs_s3_bucket', 'access_logs_s3_prefix']
                           )
                           )

    # Quick check of listeners parameters
    listeners = module.params.get("listeners")
    if listeners is not None:
        for listener in listeners:
            for key in listener.keys():
                if key not in ['Protocol', 'Port', 'SslPolicy', 'Certificates', 'DefaultActions', 'Rules']:
                    module.fail_json(msg="listeners parameter contains invalid dict keys")

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
