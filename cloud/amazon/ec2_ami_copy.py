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

DOCUMENTATION = '''
---
module: ec2_ami_copy
short_description: copies AMI between AWS regions, return new image id
description:
    - Copies AMI from a source region to a destination region. This module has a dependency on python-boto >= 2.5
version_added: "2.0"
options:
  source_region:
    description:
      - the source region that AMI should be copied from
    required: true
  source_image_id:
    description:
      - the id of the image in source region that should be copied
    required: true
  name:
    description:
      - The name of the new image to copy
    required: false
    default: null
  description:
    description:
      - An optional human-readable string describing the contents and purpose of the new AMI.
    required: false
    default: null
  encrypted:
    description:
      - Whether or not to encrypt the target image
    required: false
    default: null
    version_added: "2.2"
  kms_key_id:
    description:
      - KMS key id used to encrypt image. If not specified, uses default EBS Customer Master Key (CMK) for your account.
    required: false
    default: null
    version_added: "2.2"
  wait:
    description:
      - wait for the copied AMI to be in state 'available' before returning.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    required: false
    default: 1200
  tags:
    description:
      - a hash/dictionary of tags to add to the new copied AMI; '{"key":"value"}' and '{"key":"value","key":"value"}'
    required: false
    default: null

author: Amir Moulavi <amir.moulavi@gmail.com>
extends_documentation_fragment:
    - aws
    - ec2
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
  register: image_id

# Named AMI copy
- ec2_ami_copy:
    source_region: us-east-1
    region: eu-west-1
    source_image_id: ami-xxxxxxx
    name: My-Awesome-AMI
    description: latest patch

# Tagged AMI copy
- ec2_ami_copy:
    source_region: us-east-1
    region: eu-west-1
    source_image_id: ami-xxxxxxx
    tags:
        Name: My-Super-AMI
        Patch: 1.2.3

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

import time

try:
    import boto
    import boto.ec2
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, ec2_connect, get_aws_connection_info


def copy_image(module, ec2):
    """
    Copies an AMI

    module : AnsibleModule object
    ec2: authenticated ec2 connection object
    """

    source_region = module.params.get('source_region')
    source_image_id = module.params.get('source_image_id')
    name = module.params.get('name')
    description = module.params.get('description')
    encrypted = module.params.get('encrypted')
    kms_key_id = module.params.get('kms_key_id')
    tags = module.params.get('tags')
    wait_timeout = int(module.params.get('wait_timeout'))
    wait = module.params.get('wait')

    try:
        params = {'source_region': source_region,
                  'source_image_id': source_image_id,
                  'name': name,
                  'description': description,
                  'encrypted': encrypted,
                  'kms_key_id': kms_key_id
        }

        image_id = ec2.copy_image(**params).image_id
    except boto.exception.BotoServerError as e:
        module.fail_json(msg="%s: %s" % (e.error_code, e.error_message))

    img = wait_until_image_is_recognized(module, ec2, wait_timeout, image_id, wait)

    img = wait_until_image_is_copied(module, ec2, wait_timeout, img, image_id, wait)

    register_tags_if_any(module, ec2, tags, image_id)

    module.exit_json(msg="AMI copy operation complete", image_id=image_id, state=img.state, changed=True)


# register tags to the copied AMI
def register_tags_if_any(module, ec2, tags, image_id):
    if tags:
        try:
            ec2.create_tags([image_id], tags)
        except Exception as e:
            module.fail_json(msg=str(e))


# wait here until the image is copied (i.e. the state becomes available
def wait_until_image_is_copied(module, ec2, wait_timeout, img, image_id, wait):
    wait_timeout = time.time() + wait_timeout
    while wait and wait_timeout > time.time() and (img is None or img.state != 'available'):
        img = ec2.get_image(image_id)
        time.sleep(3)
    if wait and wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(msg="timed out waiting for image to be copied")
    return img


# wait until the image is recognized.
def wait_until_image_is_recognized(module, ec2, wait_timeout, image_id, wait):
    for i in range(wait_timeout):
        try:
            return ec2.get_image(image_id)
        except boto.exception.EC2ResponseError as e:
            # This exception we expect initially right after registering the copy with EC2 API
            if 'InvalidAMIID.NotFound' in e.error_code and wait:
                time.sleep(1)
            else:
                # On any other exception we should fail
                module.fail_json(
                    msg="Error while trying to find the new image. Using wait=yes and/or a longer wait_timeout may help: " + str(
                        e))
    else:
        module.fail_json(msg="timed out waiting for image to be recognized")


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        source_region=dict(required=True),
        source_image_id=dict(required=True),
        name=dict(),
        description=dict(default=""),
        encrypted=dict(type='bool', required=False),
        kms_key_id=dict(type='str', required=False),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(default=1200),
        tags=dict(type='dict')))

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    try:
        ec2 = ec2_connect(module)
    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json(msg=str(e))

    try:
        region, ec2_url, boto_params = get_aws_connection_info(module)
    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json(msg=str(e))

    if not region:
        module.fail_json(msg="region must be specified")

    copy_image(module, ec2)


if __name__ == '__main__':
    main()

