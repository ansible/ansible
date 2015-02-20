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
module: ec2_ami
version_added: "1.3"
short_description: create or destroy an image in ec2
description:
     - Creates or deletes ec2 images. 
options:
  instance_id:
    description:
      - instance id of the image to create
    required: false
    default: null
    aliases: []
  name:
    description:
      - The name of the new image to create
    required: false
    default: null
    aliases: []
  wait:
    description:
      - wait for the AMI to be in state 'available' before returning.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    aliases: []
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 300
    aliases: []
  state:
    description:
      - create or deregister/delete image
    required: false
    default: 'present'
    aliases: []
  region:
    description:
      - The AWS region to use.  Must be specified if ec2_url is not used. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: false
    default: null
    aliases: [ 'aws_region', 'ec2_region' ]
  description:
    description:
      - An optional human-readable string describing the contents and purpose of the AMI.
    required: false
    default: null
    aliases: []
  no_reboot:
    description:
      - An optional flag indicating that the bundling process should not attempt to shutdown the instance before bundling. If this flag is True, the responsibility of maintaining file system integrity is left to the owner of the instance. The default choice is "no".
    required: false
    default: no
    choices: [ "yes", "no" ]
    aliases: []
  image_id:
    description:
      - Image ID to be deregistered.
    required: false
    default: null
    aliases: []
  delete_snapshot:
    description:
      - Whether or not to delete an AMI while deregistering it.
    required: false
    default: null
    aliases: []

author: Evan Duffield <eduffield@iacquire.com>
extends_documentation_fragment: aws
'''

# Thank you to iAcquire for sponsoring development of this module.

EXAMPLES = '''
# Basic AMI Creation
- ec2_ami:
    aws_access_key: xxxxxxxxxxxxxxxxxxxxxxx
    aws_secret_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    instance_id: i-xxxxxx
    wait: yes
    name: newtest
  register: instance

# Basic AMI Creation, without waiting
- ec2_ami:
    aws_access_key: xxxxxxxxxxxxxxxxxxxxxxx
    aws_secret_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    region: xxxxxx
    instance_id: i-xxxxxx
    wait: no
    name: newtest
  register: instance

# Deregister/Delete AMI
- ec2_ami:
    aws_access_key: xxxxxxxxxxxxxxxxxxxxxxx
    aws_secret_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    region: xxxxxx
    image_id: "{{ instance.image_id }}"
    delete_snapshot: True
    state: absent

# Deregister AMI
- ec2_ami:
    aws_access_key: xxxxxxxxxxxxxxxxxxxxxxx
    aws_secret_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    region: xxxxxx
    image_id: "{{ instance.image_id }}"
    delete_snapshot: False
    state: absent

'''
import sys
import time

try:
    import boto
    import boto.ec2
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)

def create_image(module, ec2):
    """
    Creates new AMI

    module : AnsibleModule object
    ec2: authenticated ec2 connection object
    """

    instance_id = module.params.get('instance_id')
    name = module.params.get('name')
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))
    description = module.params.get('description')
    no_reboot = module.params.get('no_reboot')

    try:
        params = {'instance_id': instance_id,
                  'name': name,
                  'description': description,
                  'no_reboot': no_reboot}

        image_id = ec2.create_image(**params)
    except boto.exception.BotoServerError, e:
        module.fail_json(msg = "%s: %s" % (e.error_code, e.error_message))

    # Wait until the image is recognized. EC2 API has eventual consistency,
    # such that a successful CreateImage API call doesn't guarantee the success
    # of subsequent DescribeImages API call using the new image id returned.
    for i in range(wait_timeout):
        try:
            img = ec2.get_image(image_id)
            break
        except boto.exception.EC2ResponseError, e:
            if 'InvalidAMIID.NotFound' in e.error_code and wait:
                time.sleep(1)
            else:
                module.fail_json(msg="Error while trying to find the new image. Using wait=yes and/or a longer wait_timeout may help.")
    else:
        module.fail_json(msg="timed out waiting for image to be recognized")

    # wait here until the image is created
    wait_timeout = time.time() + wait_timeout
    while wait and wait_timeout > time.time() and (img is None or img.state != 'available'):
        img = ec2.get_image(image_id)
        time.sleep(3)
    if wait and wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(msg = "timed out waiting for image to be created")

    module.exit_json(msg="AMI creation operation complete", image_id=image_id, state=img.state, changed=True)


def deregister_image(module, ec2):
    """
    Deregisters AMI
    """

    image_id = module.params.get('image_id')
    delete_snapshot = module.params.get('delete_snapshot')
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))

    img = ec2.get_image(image_id)
    if img == None:
        module.fail_json(msg = "Image %s does not exist" % image_id, changed=False)

    try:
        params = {'image_id': image_id,
                  'delete_snapshot': delete_snapshot}

        res = ec2.deregister_image(**params)
    except boto.exception.BotoServerError, e:
        module.fail_json(msg = "%s: %s" % (e.error_code, e.error_message))

    # wait here until the image is gone
    img = ec2.get_image(image_id)
    wait_timeout = time.time() + wait_timeout
    while wait and wait_timeout > time.time() and img is not None:
        img = ec2.get_image(image_id)
        time.sleep(3)
    if wait and wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(msg = "timed out waiting for image to be reregistered/deleted")

    module.exit_json(msg="AMI deregister/delete operation complete", changed=True)
    sys.exit(0)

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
            instance_id = dict(),
            image_id = dict(),
            delete_snapshot = dict(),
            name = dict(),
            wait = dict(type="bool", default=False),
            wait_timeout = dict(default=900),
            description = dict(default=""),
            no_reboot = dict(default=False, type="bool"),
            state = dict(default='present'),
        )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    try:
        ec2 = ec2_connect(module)
    except Exception, e:
        module.json_fail(msg="Error while connecting to aws: %s" % str(e))

    if module.params.get('state') == 'absent':
        if not module.params.get('image_id'):
            module.fail_json(msg='image_id needs to be an ami image to registered/delete')

        deregister_image(module, ec2)

    elif module.params.get('state') == 'present':
        # Changed is always set to true when provisioning new AMI
        if not module.params.get('instance_id'):
            module.fail_json(msg='instance_id parameter is required for new image')
        if not module.params.get('name'):
            module.fail_json(msg='name parameter is required for new image')
        create_image(module, ec2)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()

