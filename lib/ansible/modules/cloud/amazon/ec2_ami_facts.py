#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_ami_facts
version_added: '2.5'
short_description: Gather facts about ec2 AMIs
description: Gather facts about ec2 AMIs
author:
  - Prasad Katti, @prasadkatti
requirements: [ boto3 ]
options:
  image_ids:
    description: One or more image IDs.
    aliases: [image_id]
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value.
      - See U(https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeImages.html) for possible filters.
      - Filter names and values are case sensitive.
  owners:
    description:
      - Filter the images by the owner. Valid options are an AWS account ID, self,
      - or an AWS owner alias ( amazon | aws-marketplace | microsoft ).
    aliases: [owner]
  executable_users:
    description:
      - Filter images by users with explicit launch permissions. Valid options are an AWS account ID, self, or all (public AMIs).
    aliases: [executable_user]
  describe_image_attributes:
    description:
      - Describe attributes (like launchPermission) of the images found.
    default: no
    type: bool

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: gather facts about an AMI using ami-id
  ec2_ami_facts:
    image_ids: ami-5b488823

- name: gather facts about all AMIs with tag key Name and value webapp
  ec2_ami_facts:
    filters:
      "tag:Name": webapp

- name: gather facts about an AMI with 'AMI Name' equal to foobar
  ec2_ami_facts:
    filters:
      name: foobar

- name: gather facts about Ubuntu 17.04 AMIs published by Canonical (099720109477)
  ec2_ami_facts:
    owners: 099720109477
    filters:
      name: "ubuntu/images/ubuntu-zesty-17.04-*"
'''

RETURN = '''
images:
  description: a list of images
  returned: always
  type: complex
  contains:
    architecture:
      description: The architecture of the image
      returned: always
      type: string
      sample: x86_64
    block_device_mappings:
      description: Any block device mapping entries
      returned: always
      type: complex
      contains:
        device_name:
          description: The device name exposed to the instance
          returned: always
          type: string
          sample: /dev/sda1
        ebs:
          description: EBS volumes
          returned: always
          type: complex
    creation_date:
      description: The date and time the image was created
      returned: always
      type: string
      sample: '2017-10-16T19:22:13.000Z'
    description:
      description: The description of the AMI
      returned: always
      type: string
      sample: ''
    ena_support:
      description: whether enhanced networking with ENA is enabled
      returned: always
      type: bool
      sample: true
    hypervisor:
      description: The hypervisor type of the image
      returned: always
      type: string
      sample: xen
    image_id:
      description: The ID of the AMI
      returned: always
      type: string
      sample: ami-5b466623
    image_location:
      description: The location of the AMI
      returned: always
      type: string
      sample: 408466080000/Webapp
    image_type:
      description: The type of image
      returned: always
      type: string
      sample: machine
    launch_permissions:
      description: launch permissions of the ami
      returned: when image is owned by calling account and describe_image_attributes is yes
      type: complex
      sample: [{"group": "all"}, {"user_id": "408466080000"}]
    name:
      description: The name of the AMI that was provided during image creation
      returned: always
      type: string
      sample: Webapp
    owner_id:
      description: The AWS account ID of the image owner
      returned: always
      type: string
      sample: '408466080000'
    public:
      description: whether the image has public launch permissions
      returned: always
      type: bool
      sample: true
    root_device_name:
      description: The device name of the root device
      returned: always
      type: string
      sample: /dev/sda1
    root_device_type:
      description: The type of root device used by the AMI
      returned: always
      type: string
      sample: ebs
    sriov_net_support:
      description: whether enhanced networking is enabled
      returned: always
      type: string
      sample: simple
    state:
      description: The current state of the AMI
      returned: always
      type: string
      sample: available
    tags:
      description: Any tags assigned to the image
      returned: always
      type: complex
    virtualization_type:
      description: The type of virtualization of the AMI
      returned: always
      type: string
      sample: hvm
'''

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (boto3_conn, ec2_argument_spec, get_aws_connection_info, ansible_dict_to_boto3_filter_list,
                                      camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict)


def list_ec2_images(ec2_client, module):

    image_ids = module.params.get("image_ids")
    owners = module.params.get("owners")
    executable_users = module.params.get("executable_users")
    filters = module.params.get("filters")
    owner_param = []

    # describe_images is *very* slow if you pass the `Owners`
    # param (unless it's self), for some reason.
    # Converting the owners to filters and removing from the
    # owners param greatly speeds things up.
    # Implementation based on aioue's suggestion in #24886
    for owner in owners:
        if owner.isdigit():
            if 'owner-id' not in filters:
                filters['owner-id'] = list()
            filters['owner-id'].append(owner)
        elif owner == 'self':
            # self not a valid owner-alias filter (https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeImages.html)
            owner_param.append(owner)
        else:
            if 'owner-alias' not in filters:
                filters['owner-alias'] = list()
            filters['owner-alias'].append(owner)

    filters = ansible_dict_to_boto3_filter_list(filters)

    try:
        images = ec2_client.describe_images(ImageIds=image_ids, Filters=filters, Owners=owner_param, ExecutableUsers=executable_users)
        images = [camel_dict_to_snake_dict(image) for image in images["Images"]]
    except (ClientError, BotoCoreError) as err:
        module.fail_json_aws(err, msg="error describing images")
    for image in images:
        try:
            image['tags'] = boto3_tag_list_to_ansible_dict(image.get('tags', []))
            if module.params.get("describe_image_attributes"):
                launch_permissions = ec2_client.describe_image_attribute(Attribute='launchPermission', ImageId=image['image_id'])['LaunchPermissions']
                image['launch_permissions'] = [camel_dict_to_snake_dict(perm) for perm in launch_permissions]
        except (ClientError, BotoCoreError) as err:
            # describing launch permissions of images owned by others is not permitted, but shouldn't cause failures
            pass

    images.sort(key=lambda e: e.get('creation_date', ''))  # it may be possible that creation_date does not always exist
    module.exit_json(images=images)


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            image_ids=dict(default=[], type='list', aliases=['image_id']),
            filters=dict(default={}, type='dict'),
            owners=dict(default=[], type='list', aliases=['owner']),
            executable_users=dict(default=[], type='list', aliases=['executable_user']),
            describe_image_attributes=dict(default=False, type='bool')
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        ec2_client = boto3_conn(module, conn_type='client', resource='ec2', region=region, endpoint=ec2_url, **aws_connect_params)
    else:
        module.fail_json(msg="region must be specified")

    list_ec2_images(ec2_client, module)


if __name__ == '__main__':
    main()
