#!/usr/bin/python
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ec2_launch_template
version_added: "2.8"
short_description: Manage EC2 launch templates
description:
  - Create, modify, and delete EC2 Launch Templates, which can be used to
    create individual instances or with Autoscaling Groups.
  - The I(ec2_instance) and I(ec2_asg) modules can, instead of specifying all
    parameters on those tasks, be passed a Launch Template which contains
    settings like instance size, disk type, subnet, and more.
requirements:
  - botocore
  - boto3 >= 1.6.0
extends_documentation_fragment:
  - aws
  - ec2
author:
  - Ryan Scott Brown (@ryansb)
options:
  template_id:
    description: The ID for the launch template, can be used for all cases except creating a new Launch Template.
    aliases: [id]
  template_name:
    description: The template name. This must be unique in the region-account combination you are using.
    aliases: [name]
  default_version:
    description: Which version should be the default when users spin up new instances based on this template? By default, the latest version will be made the default.
    default: latest
  state:
    description:
    - Whether the launch template should exist or not. To delete only a
      specific version of a launch template, combine I(state=absent) with
      the I(version) option. By default, I(state=absent) will remove all
      versions of the template.
    choices: [present, absent]
    default: present
  cpu_options:
    description:
    - Choose CPU settings for the EC2 instances that will be created with this template.
    - For more information, see U(http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-optimize-cpu.html)
    suboptions:
      core_count:
        type: integer
        description: The number of CPU cores for the instance.
      threads_per_core:
        type: integer
        description: >
          The number of threads per CPU core. To disable Intel Hyper-Threading
          Technology for the instance, specify a value of 1. Otherwise, specify
          the default value of 2.
  credit_specification:
    description: The credit option for CPU usage of the instance. Valid for T2 or T3 instances only.
    suboptions:
      cpu_credits:
        description: >
          The credit option for CPU usage of a T2 or T3 instance. Valid values
          are I(standard) and I(unlimited).
        choices: [standard, unlimited]
  disable_api_termination:
    description: >
      This helps protect instances from accidental termination. If set to true,
      you can't terminate the instance using the Amazon EC2 console, CLI, or
      API. To change this attribute to false after launch, use
      I(ModifyInstanceAttribute).
    type: boolean
  ebs_optimized:
    description: >
      Indicates whether the instance is optimized for Amazon EBS I/O. This
      optimization provides dedicated throughput to Amazon EBS and an optimized
      configuration stack to provide optimal Amazon EBS I/O performance. This
      optimization isn't available with all instance types. Additional usage
      charges apply when using an EBS-optimized instance.
    type: boolean
  elastic_gpu_specifications:
    description: Settings for Elastic GPU attachments. See U(https://aws.amazon.com/ec2/elastic-gpus/) for details.
    suboptions:
      type:
        description: The type of Elastic GPU to attach
  iam_instance_profile:
    description: >
      The name or ARN of an IAM instance profile. Requires permissions to
      describe existing instance roles to confirm ARN is properly formed.
  image_id:
    description: >
      The AMI ID to use for new instances launched with this template. This
      value is region-dependent since AMIs are not global resources.
  instance_initiated_shutdown_behavior:
    description: >
      Indicates whether an instance stops or terminates when you initiate
      shutdown from the instance using the operating system shutdown command.
    choices: [stop, terminate]
  instance_market_options:
    description: Options for alternative instance markets, currently only the spot market is supported.
    suboptions:
      market_type:
        description: The market type. This should always be 'spot'.
      spot_options:
        description: Spot-market specific settings
        type: dict
        suboptions:
          block_duration_minutes:
            type: integer
            description: >
              The required duration for the Spot Instances (also known as Spot
              blocks), in minutes. This value must be a multiple of 60 (60,
              120, 180, 240, 300, or 360).
          instance_interruption_behavior:
            description: The behavior when a Spot Instance is interrupted. The default is I(terminate)
            choices: [hibernate, stop, terminate]
          max_price:
            description: The highest hourly price you're willing to pay for this Spot Instance.
          spot_instance_type:
            description: The request type to send.
            choices: [one-time, persistent]
    type: dict
  instance_type:
    description: >
      The instance type, such as I(c5.2xlarge). For a full list of instance types, see
      http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html
  kernel_id:
    description: >
      The ID of the kernel. We recommend that you use PV-GRUB instead of
      kernels and RAM disks. For more information, see
      U(http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/UserProvidedkernels.html)
  key_name:
    description:
    - The name of the key pair. You can create a key pair using
      I(CreateKeyPair) or I(ImportKeyPair).
    - If you do not specify a key pair, you can't connect to the instance
      unless you choose an AMI that is configured to allow users another way to
      log in.
  monnitoring:
    description: Settings for instance monitoring
    suboptions:
      enabled:
        type: bool
        description: Whether to turn on detailed monitoring for new instances. This will incur extra charges.
  ram_disk_id:
    description: >
      The ID of the RAM disk to launch the instance with. We recommend that you
      use PV-GRUB instead of kernels and RAM disks. For more information, see
      U(http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/UserProvidedkernels.html)
  security_group_ids:
    description: A list of security group IDs (VPC or EC2-Classic) that the new instances will be added to.
    type: list
  security_groups:
    description: A list of security group names (VPC or EC2-Classic) that the new instances will be added to.
    type: list
  tags:
    type: dict
    description:
    - A set of key-value pairs to be applied to resources when this Launch Template is used.
    - Tag key constraints: Tag keys are case-sensitive and accept a maximum of
      127 Unicode characters. May not begin with I(aws:)
    - Tag value constraints: Tag values are case-sensitive and accept a maximum
      of 255 Unicode characters.
  user_data:
    description: >
      The Base64-encoded user data to make available to the instance. For more information, see the Linux
      U(http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html) and Windows
      U(http://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/ec2-instance-metadata.html#instancedata-add-user-data)
      documentation on user-data.
'''

RETURN = '''
latest_version:
  description: Latest available version of the launch template
  returned: when state=present
  type: int
default_version:
  description: The version that will be used if only the template name is specified. Often this is the same as the latest version, but not always.
  returned: when state=present
  type: int
'''
import re
from uuid import uuid4

from ansible.module_utils._text import to_text
from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code, get_boto3_client_method_parameters
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict, snake_dict_to_camel_dict
from ansible.module_utils.ec2 import ansible_dict_to_boto3_tag_list, AWSRetry, boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_tag_list

try:
    from botocore.exceptions import ClientError, BotoCoreError, WaiterError
except ImportError:
    pass  # caught by AnsibleAWSModule


def determine_iam_role(module, name_or_arn):
    if re.match(r'^arn:aws:iam::\d+:instance-profile/[\w+=/,.@-]+$', name_or_arn):
        return name_or_arn
    iam = module.client('iam', retry_decorator=AWSRetry.jittered_backoff())
    try:
        role = iam.get_instance_profile(InstanceProfileName=name_or_arn, aws_retry=True)
        return {'arn': role['InstanceProfile']['Arn']}
    except is_boto3_error_code('NoSuchEntity') as e:
        module.fail_json_aws(e, msg="Could not find instance_role {0}".format(name_or_arn))
    except (BotoCoreError, ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg="An error occurred while searching for instance_role {0}. Please try supplying the full ARN.".format(name_or_arn))


def existing_templates(module):
    ec2 = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())
    matches = None
    try:
        if module.params.get('template_id'):
            matches = ec2.describe_launch_templates(LaunchTemplateIds=[module.params.get('template_id')])
        elif module.params.get('template_name'):
            matches = ec2.describe_launch_templates(LaunchTemplateNames=[module.params.get('template_name')])
    except is_boto3_error_code('InvalidLaunchTemplateName.NotFoundException') as e:
        # no named template was found, return nothing/empty versions
        return None, []
    except is_boto3_error_code('InvalidLaunchTemplateId.Malformed') as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg='Launch template with ID {0} is not a valid ID. It should start with `lt-....`'.format(
            module.params.get('launch_template_id')))
    except is_boto3_error_code('InvalidLaunchTemplateId.NotFoundException') as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(
            e, msg='Launch template with ID {0} could not be found, please supply a name '
            'instead so that a new template can be created'.format(module.params.get('launch_template_id')))
    except (ClientError, BotoCoreError, WaiterError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg='Could not check existing launch templates. This may be an IAM permission problem.')
    else:
        template = matches['LaunchTemplates'][0]
        template_id, template_version, template_default = template['LaunchTemplateId'], template['LatestVersionNumber'], template['DefaultVersionNumber']
        try:
            return template, ec2.describe_launch_template_versions(LaunchTemplateId=template_id)['LaunchTemplateVersions']
        except (ClientError, BotoCoreError, WaiterError) as e:
            module.fail_json_aws(e, msg='Could not find launch template versions for {0} (ID: {1}).'.format(template['LaunchTemplateName'], template_id))


def params_to_launch_data(module, template_params):
    if template_params.get('tags'):
        template_params['tag_specifications'] = [
            {
                'resource_type': r_type,
                'tags': [
                    {'Key': k, 'Value': v} for k, v
                    in template_params['tags'].items()
                ]
            }
            for r_type in ('instance', 'network-interface', 'volume')
        ]
        del template_params['tags']
    if module.params.get('iam_instance_profile'):
        template_params['iam_instance_profile'] = determine_iam_role(module, module.params['iam_instance_profile'])
    params = snake_dict_to_camel_dict(
        dict((k, v) for k, v in template_params.items() if v is not None),
        capitalize_first=True,
    )
    return params


def delete_template(module):
    ec2 = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())
    template, template_versions = existing_templates(module)
    deleted_versions = []
    if template or template_versions:
        non_default_versions = [to_text(t['VersionNumber']) for t in template_versions if not t['DefaultVersion']]
        if non_default_versions:
            try:
                v_resp = ec2.delete_launch_template_versions(
                    LaunchTemplateId=template['LaunchTemplateId'],
                    Versions=non_default_versions,
                )
                if v_resp['UnsuccessfullyDeletedLaunchTemplateVersions']:
                    module.warn('Failed to delete template versions {0} on launch template {1}'.format(
                        v_resp['UnsuccessfullyDeletedLaunchTemplateVersions'],
                        template['LaunchTemplateId'],
                    ))
                deleted_versions = [camel_dict_to_snake_dict(v) for v in v_resp['SuccessfullyDeletedLaunchTemplateVersions']]
            except (ClientError, BotoCoreError) as e:
                module.fail_json_aws(e, msg="Could not delete existing versions of the launch template {0}".format(template['LaunchTemplateId']))
        try:
            resp = ec2.delete_launch_template(
                LaunchTemplateId=template['LaunchTemplateId'],
            )
        except (ClientError, BotoCoreError) as e:
            module.fail_json_aws(e, msg="Could not delete launch template {0}".format(template['LaunchTemplateId']))
        return {
            'deleted_versions': deleted_versions,
            'deleted_template': camel_dict_to_snake_dict(resp['LaunchTemplate']),
            'changed': True,
        }
    else:
        return {'changed': False}


def create_or_update(module, template_options):
    ec2 = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())
    template, template_versions = existing_templates(module)
    out = {}
    lt_data = params_to_launch_data(module, dict((k, v) for k, v in module.params.items() if k in template_options))
    if not (template or template_versions):
        # create a full new one
        try:
            resp = ec2.create_launch_template(
                LaunchTemplateName=module.params['template_name'],
                LaunchTemplateData=lt_data,
                ClientToken=uuid4().hex,
                aws_retry=True,
            )
        except (ClientError, BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't create launch template")
        template, template_versions = existing_templates(module)
        out['changed'] = True
    elif template and template_versions:
        # TODO diff current state with params
        try:
            resp = ec2.create_launch_template_version(
                LaunchTemplateId=template['LaunchTemplateId'],
                LaunchTemplateData=lt_data,
                ClientToken=uuid4().hex,
                aws_retry=True,
            )
            if module.params.get('default_version') in (None, ''):
                # no need to do anything, leave the existing version as default
                pass
            elif module.params.get('default_version') == 'latest':
                set_default = ec2.modify_launch_template(
                    LaunchTemplateId=template['LaunchTemplateId'],
                    DefaultVersion=to_text(resp['LaunchTemplateVersion']['VersionNumber']),
                    ClientToken=uuid4().hex,
                    aws_retry=True,
                )
            else:
                try:
                    int(module.params.get('default_version'))
                except ValueError:
                    module.fail_json(msg='default_version param was not a valid integer, got "{0}"'.format(module.params.get('default_version')))
                set_default = ec2.modify_launch_template(
                    LaunchTemplateId=template['LaunchTemplateId'],
                    DefaultVersion=to_text(int(module.params.get('default_version'))),
                    ClientToken=uuid4().hex,
                    aws_retry=True,
                )
        except (ClientError, BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't create subsequent launch template version")
        template, template_versions = existing_templates(module)
        out['changed'] = True
    return out


def format_module_output(module):
    output = {}
    template, template_versions = existing_templates(module)
    template = camel_dict_to_snake_dict(template)
    template_versions = [camel_dict_to_snake_dict(v) for v in template_versions]
    for v in template_versions:
        for ts in (v['launch_template_data'].get('tag_specifications') or []):
            ts['tags'] = boto3_tag_list_to_ansible_dict(ts.pop('tags'))
    output.update(dict(template=template, versions=template_versions))
    output['default_template'] = [
        v for v in template_versions
        if v.get('default_version')
    ][0]
    output['latest_template'] = [
        v for v in template_versions
        if (
            v.get('version_number') and
            int(v['version_number']) == int(template['latest_version_number'])
        )
    ][0]
    return output


def main():
    template_options = dict(
        block_device_mappings=dict(
            type='list',
            options=dict(
                device_name=dict(),
                ebs=dict(
                    type='dict',
                    options=dict(
                        delete_on_termination=dict(type='bool'),
                        encrypted=dict(type='bool'),
                        iops=dict(type='int'),
                        kms_key_id=dict(),
                        snapshot_id=dict(),
                        volume_size=dict(type='int'),
                        volume_type=dict(),
                    ),
                ),
                no_device=dict(),
                virtual_name=dict(),
            ),
        ),
        cpu_options=dict(
            type='dict',
            options=dict(
                core_count=dict(type='int'),
                threads_per_core=dict(type='int'),
            ),
        ),
        credit_specification=dict(
            dict(type='dict'),
            options=dict(
                cpu_credits=dict(),
            ),
        ),
        disable_api_termination=dict(type='bool'),
        ebs_optimized=dict(type='bool'),
        elastic_gpu_specifications=dict(
            options=dict(type=dict()),
            type='list',
        ),
        iam_instance_profile=dict(),
        image_id=dict(),
        instance_initiated_shutdown_behavior=dict(choices=['stop', 'terminate']),
        instance_market_options=dict(
            type='dict',
            options=dict(
                market_type=dict(),
                spot_options=dict(
                    type='dict',
                    options=dict(
                        block_duration_minutes=dict(type='int'),
                        instance_interruption_behavior=dict(choices=['hibernate', 'stop', 'terminate']),
                        max_price=dict(),
                        spot_instance_type=dict(choices=['one-time', 'persistent']),
                    ),
                ),
            ),
        ),
        instance_type=dict(),
        kernel_id=dict(),
        key_name=dict(),
        monitoring=dict(
            type='dict',
            options=dict(
                enabled=dict(type='bool')
            ),
        ),
        network_interfaces=dict(
            type='list',
            options=dict(
                associate_public_ip_address=dict(type='bool'),
                delete_on_termination=dict(type='bool'),
                description=dict(),
                device_index=dict(type='int'),
                groups=dict(type='list'),
                ipv6_address_count=dict(type='int'),
                ipv6_addresses=dict(
                    options=dict(ipv6_address=dict()),
                    type='list'
                ),
                network_interface_id=dict(),
                private_ip_address=dict(),
                subnet_id=dict(),
            ),
        ),
        placement=dict(
            options=dict(
                affinity=dict(),
                availability_zone=dict(),
                group_name=dict(),
                host_id=dict(),
                spread_domain=dict(),
                tenancy=dict(),
            ),
            type='dict',
        ),
        ram_disk_id=dict(),
        security_group_ids=dict(type='list'),
        security_groups=dict(type='list'),
        tags=dict(type='dict'),
        user_data=dict(),
    )

    arg_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        template_name=dict(aliases=['name']),
        template_id=dict(aliases=['id']),
        default_version=dict(default='latest'),
    )

    arg_spec.update(template_options)

    module = AnsibleAWSModule(
        argument_spec=arg_spec,
        required_one_of=[
            ('template_name', 'template_id')
        ],
        supports_check_mode=True
    )

    if not module.boto3_at_least('1.6.0'):
        module.fail_json(msg="ec2_launch_template requires boto3 >= 1.6.0")

    if module.params.get('state') == 'present':
        out = create_or_update(module, template_options)
        out.update(format_module_output(module))
    elif module.params.get('state') == 'absent':
        out = delete_template(module)
    else:
        module.fail_json(msg='Unsupported value "{0}" for `state` parameter'.format(module.params.get('state')))

    module.exit_json(**out)


if __name__ == '__main__':
    main()
