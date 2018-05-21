#!/usr/bin/python
# -*- coding: utf-8 -*-
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_ami_copy
short_description: copies AMI between AWS regions, return new image id
description:
    - Copies AMI from a source region to a destination region. B(Since version 2.3 this module depends on boto3.)
version_added: "2.0"
options:
  source_region:
    description:
      - The source region the AMI should be copied from.
    required: true
  source_image_id:
    description:
      - The ID of the AMI in source region that should be copied.
    required: true
  name:
    description:
      - The name of the new AMI to copy. (As of 2.3 the default is 'default', in prior versions it was 'null'.)
    default: "default"
  description:
    description:
      - An optional human-readable string describing the contents and purpose of the new AMI.
  encrypted:
    description:
      - Whether or not the destination snapshots of the copied AMI should be encrypted.
    version_added: "2.2"
  kms_key_id:
    description:
      - KMS key id used to encrypt image. If not specified, uses default EBS Customer Master Key (CMK) for your account.
    version_added: "2.2"
  wait:
    description:
      - Wait for the copied AMI to be in state 'available' before returning.
    type: bool
    default: 'no'
  wait_timeout:
    description:
      - How long before wait gives up, in seconds. Prior to 2.3 the default was 1200.
      - From 2.3-2.5 this option was deprecated in favor of boto3 waiter defaults.
        This was reenabled in 2.6 to allow timeouts greater than 10 minutes.
    default: 600
  tags:
    description:
      - A hash/dictionary of tags to add to the new copied AMI; '{"key":"value"}' and '{"key":"value","key":"value"}'
  tag_equality:
    description:
      - Whether to use tags if the source AMI already exists in the target region. If this is set, and all tags match
        in an existing AMI, the AMI will not be copied again.
    default: false
    version_added: 2.6
author: "Amir Moulavi <amir.moulavi@gmail.com>, Tim C <defunct@defunct.io>"
extends_documentation_fragment:
    - aws
    - ec2
requirements:
    - boto3
'''

EXAMPLES = '''
# Basic AMI Copy
- ec2_ami_copy:
    source_region: us-east-1
    region: eu-west-1
    source_image_id: ami-xxxxxxx

# AMI copy wait until available
- ec2_ami_copy:
    source_region: us-east-1
    region: eu-west-1
    source_image_id: ami-xxxxxxx
    wait: yes
    wait_timeout: 1200  # Default timeout is 600
  register: image_id

# Named AMI copy
- ec2_ami_copy:
    source_region: us-east-1
    region: eu-west-1
    source_image_id: ami-xxxxxxx
    name: My-Awesome-AMI
    description: latest patch

# Tagged AMI copy (will not copy the same AMI twice)
- ec2_ami_copy:
    source_region: us-east-1
    region: eu-west-1
    source_image_id: ami-xxxxxxx
    tags:
        Name: My-Super-AMI
        Patch: 1.2.3
    tag_equality: yes

# Encrypted AMI copy
- ec2_ami_copy:
    source_region: us-east-1
    region: eu-west-1
    source_image_id: ami-xxxxxxx
    encrypted: yes

# Encrypted AMI copy with specified key
- ec2_ami_copy:
    source_region: us-east-1
    region: eu-west-1
    source_image_id: ami-xxxxxxx
    encrypted: yes
    kms_key_id: arn:aws:kms:us-east-1:XXXXXXXXXXXX:key/746de6ea-50a4-4bcb-8fbc-e3b29f2d367b
'''

RETURN = '''
image_id:
  description: AMI ID of the copied AMI
  returned: always
  type: string
  sample: ami-e689729e
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import ec2_argument_spec
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, ansible_dict_to_boto3_tag_list

try:
    from botocore.exceptions import ClientError, NoCredentialsError, WaiterError, BotoCoreError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def copy_image(module, ec2):
    """
    Copies an AMI

    module : AnsibleModule object
    ec2: ec2 connection object
    """

    image = None
    changed = False
    tags = module.params.get('tags')

    params = {'SourceRegion': module.params.get('source_region'),
              'SourceImageId': module.params.get('source_image_id'),
              'Name': module.params.get('name'),
              'Description': module.params.get('description'),
              'Encrypted': module.params.get('encrypted'),
              }
    if module.params.get('kms_key_id'):
        params['KmsKeyId'] = module.params.get('kms_key_id')

    try:
        if module.params.get('tag_equality'):
            filters = [{'Name': 'tag:%s' % k, 'Values': [v]} for (k, v) in module.params.get('tags').items()]
            filters.append(dict(Name='state', Values=['available', 'pending']))
            images = ec2.describe_images(Filters=filters)
            if len(images['Images']) > 0:
                image = images['Images'][0]
        if not image:
            image = ec2.copy_image(**params)
            image_id = image['ImageId']
            if tags:
                ec2.create_tags(Resources=[image_id],
                                Tags=ansible_dict_to_boto3_tag_list(tags))
            changed = True

        if module.params.get('wait'):
            delay = 15
            max_attempts = module.params.get('wait_timeout') // delay
            ec2.get_waiter('image_available').wait(
                ImageIds=[image_id],
                WaiterConfig={'Delay': delay, 'MaxAttempts': max_attempts}
            )

        module.exit_json(changed=changed, **camel_dict_to_snake_dict(image))
    except WaiterError as e:
        module.fail_json_aws(e, msg='An error occurred waiting for the image to become available')
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Could not copy AMI")
    except Exception as e:
        module.fail_json(msg='Unhandled exception. (%s)' % str(e))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        source_region=dict(required=True),
        source_image_id=dict(required=True),
        name=dict(default='default'),
        description=dict(default=''),
        encrypted=dict(type='bool', default=False, required=False),
        kms_key_id=dict(type='str', required=False),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=600),
        tags=dict(type='dict')),
        tag_equality=dict(type='bool', default=False))

    module = AnsibleAWSModule(argument_spec=argument_spec)
    # TODO: Check botocore version
    ec2 = module.client('ec2')
    copy_image(module, ec2)


if __name__ == '__main__':
    main()
