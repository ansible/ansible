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
module: rds_instance
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
    state:
        description:
          - Whether the launch template should exist or not. To delete only a
            specific version of a launch template, combine I(state=absent) with
            the I(version) option. By default, I(state=absent) will remove all
            versions of the template.
        choices: [present, absent]
        default: present
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
arn:
  description: The full Amazon Resource Name for the launch template
  returned: when state=present
  type: string
'''
import q
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
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            module.fail_json_aws(e, msg="Could not find instance_role {0}".format(name_or_arn))
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
        q('No template with that name')
        return None, []
    except is_boto3_error_code('InvalidLaunchTemplateId.Malformed') as e:
        module.fail_json_aws(e, msg='Launch template with ID {0} is not a valid ID. It should start with `lt-....`'.format(module.params.get('launch_template_id')))
    except is_boto3_error_code('InvalidLaunchTemplateId.NotFoundException') as e:
        module.fail_json_aws(e, msg='Launch template with ID {0} could not be found, please supply a name instead so that a new template can be created'.format(module.params.get('launch_template_id')))
    except (ClientError, BotoCoreError, WaiterError) as e:
        module.fail_json_aws(e, msg='Could not check existing launch templates. This may be an IAM permission problem.')
    else:
        template = matches['LaunchTemplates'][0]
        template_id, template_version, template_default = template['LaunchTemplateId'], template['LatestVersionNumber'], template['DefaultVersionNumber']
        q('Found template', template_id, template_version, template_default)
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
    q(template_params)
    if module.params.get('iam_instance_profile'):
        template_params['iam_instance_profile'] = determine_iam_role(module, module.params['iam_instance_profile'])
    params = snake_dict_to_camel_dict(
        dict((k, v) for k, v in template_params.items() if v is not None),
        capitalize_first=True,
    )
    q(params)
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
                q(v_resp)
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
        q('Create result', resp)
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
            q('New version response', resp)
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
    output['default_template'] = [v for v in template_versions
        if v.get('default_version')
    ][0]
    output['latest_template'] = [v for v in template_versions
        if v.get('version_number') and int(v['version_number']) == int(template['latest_version_number'])
    ][0]
    q(output)
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
            options=dict(
                market_type=dict(),
                spot_options=dict(
                    options=dict(
                        block_duration_minutes=dict(type='int'),
                        instance_interruption_behavior=dict(),
                        max_price=dict(),
                        spot_instance_type=dict(),
                    ),
                    type='dict',
                ),
            ),
            type='dict',
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

# TODO: remove this
# service_module_shape_to_argspec('RequestLaunchTemplateData')
def service_module_shape_to_argspec(shape_name):
    launch_template_input = ec2._service_model.shape_for(shape_name)
    def long_to_short(l):
        if l in 'string':
            return 'str'
        if l in 'integer':
            return 'int'
        if l in 'boolean':
            return 'bool'

    def recurse_complex(struct):
        out = {}
        for field, structure in struct.members.items():
            if structure.type_name == 'string':
                out[field] = dict()
            elif structure.type_name in ('string', 'integer', 'boolean'):
                out[field] = dict(type=long_to_short(structure.type_name))
            elif structure.type_name == 'list':
                if structure.member.type_name in ('integer', 'boolean'):
                    out[field] = dict(type='list', options=dict(type=long_to_short(structure.member.type_name)))
                if structure.member.type_name == 'string':
                    out[field] = dict(type='list')
                else:
                    out[field] = dict(type='list', options=recurse_complex(structure.member))
            elif structure.type_name == 'structure':
                out[field] = dict(type='dict', options=recurse_complex(structure))
            else:
                q('Got', field, structure.type_name)
        return out
    comp = camel_dict_to_snake_dict(recurse_complex(launch_template_input))
    yaml.dump(comp, open('/tmp/comp.yml', 'w'))
    return comp
