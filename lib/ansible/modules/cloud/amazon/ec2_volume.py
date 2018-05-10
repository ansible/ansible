#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_volume
short_description: create and attach a volume, return volume id and device map
description:
    - creates an EBS volume and optionally attaches it to an instance.
version_added: '2.6'
requirements: [ boto3, botocore ]
options:
  instance_id:
    description:
      - Instance to attach the volume to.
  name:
    description:
      - Volume name.
  volume_id:
    description:
      - Volume ID. Used to attach an existing volume (requires I(instance_id)) or remove an existing volume
      - Required if I(state=absent)
  volume_size:
    description:
      - Size of volume to create, in gibibytes.
  volume_type:
    description:
      - "Type of EBS volume: standard (magnetic), gp2 (SSD), io1 (Provisioned IOPS), st1 (Throughput Optimized HDD), sc1 (Cold HDD)."
    choices:
      - standard
      - gp2
      - io1
      - st1
      - sc1
    default: gp2
  iops:
    description:
      - The provisioned IOPS you want to associate with this volume
      - Required if I(volume_type=io1)
  encrypted:
    description:
      - Enable encryption at rest for this volume.
    type: bool
    default: no
  kms_key_id:
    description:
      - Specify the id of the KMS key to use.
  device_name:
    description:
      - Device name to map.
    default: /dev/sdf
  delete_on_termination:
    description:
      - When set to "yes", the volume will be deleted upon instance termination.
    type: bool
    default: no
  availability_zone:
    description:
      - Availability zone in which to create the volume, if unset uses the zone the instance is in (if set)
  snapshot:
    description:
      - snapshot ID on which to base the volume
  state:
    description:
      - State of the valume.
    default: present
    choices: ['absent', 'present', 'detached']
  tags:
    description:
      - tag:value pairs to add to the volume after creation
    default: {}
  wait:
    description:
      - Whether or not to wait for the desired state (use I(wait_timeout) to customize the wait).
    type: bool
    default: yes
  wait_timeout:
    description:
      - How long to wait (in seconds) for the volume to reach the desired state.
    default: 300
author:
  - Lester Wade (@lwade)
  - Paul Arthur (@flowerysong)
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# Simple attachment action
- ec2_vol:
    instance_id: i-XXXXXX
    volume_size: 5
    device_name: sdd

# Example using custom iops params
- ec2_vol:
    instance_id: i-XXXXXX
    volume_size: 5
    volume_type: io1
    iops: 100
    device_name: sdd

# Example using snapshot id
- ec2_vol:
    instance_id: i-XXXXXX
    snapshot: "{{ snapshot }}"

# Playbook example combined with instance launch
- ec2_instance:
    key_name: "{{ keypair }}"
    image_id: "{{ image }}"
    count: 3
  register: ec2
- ec2_vol:
    instance_id: "{{ item.instance_id }}"
    volume_size: 5
  with_items: "{{ ec2.instances }}"

# Remove a volume
- ec2_vol:
    volume_id: vol-XXXXXXXX
    state: absent

# Detach a volume
- ec2_vol:
    volume_id: vol-XXXXXXXX
    state: detached

# Create new volume using SSD storage
- ec2_vol:
    instance_id: i-XXXXXX
    volume_size: 50
    volume_type: gp2
    device_name: /dev/xvdf

# Attach an existing volume to instance. The volume will be deleted upon instance termination.
- ec2_vol:
    instance_id: i-XXXXXX
    volume_id: XXXXXX
    device_name: /dev/sdf
    delete_on_termination: yes
'''

RETURN = '''
volume:
    description: a dictionary containing detailed attributes of the volume
    returned: when state is not absent
    type: complex
    contains:
        attachments:
            description: List of attachments
            returned: always
            type: list
            sample: [
                {
                    "attach_time": "2015-10-23T00:22:29.000Z",
                    "device": "/dev/sdf",
                    "instance_id": "i-8356263c",
                    "state": "attached",
                    "volume_id": "vol-35b333d9",
                    "delete_on_termination": False
                }
            ]
        availability_zone:
            description: AZ for the volume
            returned: always
            type: string
            sample: us-east-1b
        create_time:
            description: Volume creation time
            returned: always
            type: string
            sample: "2015-10-21T14:36:08.870Z"
        encrypted:
            description: Whether the volume is encrypted
            returned: always
            type: bool
        kms_key_id:
            description: Key Management Service master key ID
            returned: when encrypted
            type: string
            sample: arn:aws:kms:us-east-1:123456789012:key/dead60ff-dead-60ff-dada-60ffdadadead
        size:
            description: Size of the volume, in gibibytes
            returned: always
            type: int
            sample: 1
        snapshot_id:
            description: The snapshot used when creating the volume
            returned: always
            type: string
            sample: ""
        state:
            description: The state of the volume
            returned: always
            type: string
            sample: available
        volume_id:
            description: ID of the volume
            returned: always
            type: string
            sample: vol-35b333d9
        iops:
            description: The number of IOPS that the volume supports
            returned: always
            type: int
            sample: 100
        tags:
            description: Tags associated with the volume
            returned: always
            type: dict
            sample: {
                "env": "dev"
            }
        volume_type:
            description: The volume type
            returned: always
            type: string
            sample: gp2
'''

import time

from copy import copy

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import AWSRetry, ansible_dict_to_boto3_tag_list, boto3_tag_list_to_ansible_dict
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass    # Handled by AnsibleAWSModule


def _format_volume_info(volume):
    volume_info = camel_dict_to_snake_dict(volume, ignore_list=['Tags'])
    if 'tags' in volume_info:
        volume_info['tags'] = boto3_tag_list_to_ansible_dict(volume_info['tags'])
    else:
        volume_info['tags'] = {}

    return volume_info


def _describe_volume(module, ec2, volume_id):
    try:
        return ec2.describe_volumes(Filters=[{'Name': 'volume-id', 'Values': [volume_id]}], aws_retry=True)['Volumes'][0]
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to get volume data')


def _get_device(instance, device_name):
    for dev in instance['BlockDeviceMappings']:
        if dev['DeviceName'] == device_name:
            return dev


class EC2Volume(object):
    def __init__(self, module, ec2):
        self.module = module
        self.ec2 = ec2
        self.changed = False
        self.volume = None
        self.instance = None

        self.delete_on_termination = module.params['delete_on_termination']
        self.device_name = module.params['device_name']
        self.encrypted = module.params['encrypted']
        self.instance_id = module.params['instance_id']
        self.iops = module.params['iops']
        self.kms_key_id = module.params['kms_key_id']
        self.name = module.params['name']
        self.snapshot = module.params['snapshot']
        self.state = module.params['state']
        self.tags = module.params['tags']
        self.volume_id = module.params['volume_id']
        self.volume_name = module.params['name']
        self.volume_size = module.params['volume_size']
        self.volume_type = module.params['volume_type']
        self.wait = module.params['wait']
        self.wait_timeout = module.params['wait_timeout']
        self.zone = module.params['availability_zone']

        if self.name:
            self.tags['Name'] = self.name

        if self.instance_id:
            self._update_instance()
            if self.zone:
                if self.zone != self.instance['Placement']['AvailabilityZone']:
                    module.fail_json(msg="Instance %s is not in availability zone %s" % (self.instance_id, self.zone))
            else:
                self.zone = self.instance['Placement']['AvailabilityZone']

        self._update()

    def _update_instance(self):
        try:
            self.instance = self.ec2.describe_instances(
                Filters=[{'Name': 'instance-id', 'Values': [self.instance_id]}],
                aws_retry=True,
            )['Reservations'][0]['Instances'][0]
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg='Failed to get instance data')

    def _update(self):
        if self.volume:
            self.volume = _describe_volume(self.module, self.ec2, self.volume['VolumeId'])
            return

        filters = []

        if self.volume_id is None and self.name is None:
            self.volume = None
            return

        if self.zone:
            filters.append({'Name': 'availability-zone', 'Values': [self.zone]})
        if self.volume_id:
            filters.append({'Name': 'volume-id', 'Values': [self.volume_id]})
        elif self.name:
            filters.append({'Name': 'tag:Name', 'Values': [self.name]})

        try:
            vols = self.ec2.describe_volumes(Filters=filters, aws_retry=True)['Volumes']
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg='Failed to fetch existing volume')

        if not vols:
            if self.volume_id:
                msg = "Could not find the volume with id: %s" % self.volume_id
                if self.name:
                    msg += (" and name: %s" % self.name)
                self.module.fail_json(msg=msg)
            else:
                self.volume = None
                return

        if len(vols) > 1:
            self.module.fail_json(msg="Found more than one volume in zone (if specified) with name: %s" % self.name)
        self.volume = vols[0]

    def delete(self):
        if not self.volume:
            return
        self.changed = True
        if self.module.check_mode:
            return
        try:
            self.ec2.delete_volume(VolumeId=self.volume_id, aws_retry=True)
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidVolume.NotFound':
                # Something else deleted the volume?
                self.changed = False
            else:
                self.module.fail_json_aws(e, msg='Failed to delete volume')
        except BotoCoreError as e:
            self.module.fail_json_aws(e, msg='Failed to delete volume')

    def create(self):
        if self.volume:
            return

        self.changed = True
        if self.module.check_mode:
            return
        args = {
            'aws_retry': True,
            'AvailabilityZone': self.zone,
            'Encrypted': self.encrypted,
            'VolumeType': self.volume_type,
            'Size': self.volume_size,
        }

        if self.tags:
            args['TagSpecifications'] = [{
                'ResourceType': 'volume',
                'Tags': ansible_dict_to_boto3_tag_list(self.tags),
            }]
        if self.iops:
            args['Iops'] = self.iops
        if self.kms_key_id:
            args['KmsKeyId'] = self.kms_key_id
        if self.snapshot:
            args['SnapshotId'] = self.snapshot
        try:
            self.volume = self.ec2.create_volume(**args)
            if self.wait:
                start = time.time()
                waiter = self.ec2.get_waiter('volume_available')
                waiter.wait(VolumeIds=[self.volume['VolumeId']], WaiterConfig={'Delay': 3, 'MaxAttempts': self.wait_timeout / 3})
                self.wait_timeout -= int(time.time() - start)
        except (BotoCoreError, ClientError) as e:
            self.module.fail_json_aws(e, msg='Failed to create volume')

        self._update()

    def attach(self):
        if not self.instance:
            return

        dev = _get_device(self.instance, self.device_name)
        if dev and dev['Ebs']['VolumeId'] != self.volume['VolumeId']:
            self.module.fail_json(
                msg="Can't attach %s, volume %s is already attached to %s as %s" % (
                    self.volume['VolumeId'],
                    dev['Ebs']['VolumeId'],
                    self.instance['InstanceId'],
                    self.device_name,
                )
            )

        if self.volume['Attachments'] and self.volume['Attachments'][0]['State'] in ('attaching', 'attached'):
            if self.volume['Attachments'][0]['InstanceId'] != self.instance['InstanceId']:
                self.module.fail_json(
                    msg="Volume %s is already attached to another instance: %s" % (self.volume['VolumeId'], self.volume['Attachments'][0]['InstanceId'])
                )
        else:
            self.changed = True
            if self.module.check_mode:
                return
            try:
                self.ec2.attach_volume(
                    Device=self.device_name,
                    InstanceId=self.instance['InstanceId'],
                    VolumeId=self.volume['VolumeId'],
                    aws_retry=True,
                )
            except (BotoCoreError, ClientError) as e:
                self.module.fail_json_aws(e, msg='Failed to attach volume to instance')

        if self.wait:
            start = time.time()
            try:
                waiter = self.ec2.get_waiter('volume_in_use')
                waiter.wait(
                    VolumeIds=[self.volume['VolumeId']],
                    Filters=[{'Name': 'attachment.status', 'Values': ['attached']}],
                    WaiterConfig={'Delay': 3, 'MaxAttempts': self.wait_timeout / 3}
                )
                self.wait_timeout -= int(time.time() - start)
            except (BotoCoreError, ClientError) as e:
                self.module.fail_json_aws(e, msg='Failed to attach volume to instance')

        self._update()
        self._update_instance()
        dev = _get_device(self.instance, self.device_name)['Ebs']

        if dev['DeleteOnTermination'] != self.delete_on_termination:
            self.changed = True
            if self.module.check_mode:
                return
            try:
                self.ec2.modify_instance_attribute(
                    InstanceId=self.instance['InstanceId'],
                    BlockDeviceMappings=[{
                        'DeviceName': self.device_name,
                        'Ebs': {
                            'DeleteOnTermination': self.delete_on_termination,
                        }
                    }],
                    aws_retry=True,
                )
                self._update()
                # There's some lag on this actually being reflected,
                # so make sure the correct value is returned.
                self.volume['Attachments'][0]['DeleteOnTermination'] = self.delete_on_termination
            except (BotoCoreError, ClientError) as e:
                self.module.fail_json_aws(e, msg='Failed to update DeleteOnTermination')

    def detach(self):
        if self.volume['Attachments'] and self.volume['Attachments'][0]['State'] in ('attaching', 'attached'):
            self.changed = True
            if self.module.check_mode:
                return

            try:
                self.ec2.detach_volume(VolumeId=self.volume['VolumeId'], aws_retry=True)
                if self.wait:
                    waiter = self.ec2.get_waiter('volume_available')
                    waiter.wait(VolumeIds=[self.volume['VolumeId']], WaiterConfig={'Delay': 3, 'MaxAttempts': self.wait_timeout / 3})
            except (BotoCoreError, ClientError) as e:
                self.module.fail_json_aws(e, msg='Failed to detach volume')

            self._update()

    def reconcile_state(self):
        if self.state == 'absent':
            self.delete()
        else:
            self.create()
            if self.state == 'detached':
                self.detach()
            else:
                self.attach()


def main():
    argument_spec = dict(
        instance_id=dict(),
        volume_id=dict(),
        name=dict(),
        volume_size=dict(type='int'),
        volume_type=dict(choices=['standard', 'gp2', 'io1', 'st1', 'sc1'], default='gp2'),
        iops=dict(type='int'),
        encrypted=dict(type='bool', default=False),
        kms_key_id=dict(),
        device_name=dict(default='/dev/sdf'),
        delete_on_termination=dict(type='bool', default=False),
        availability_zone=dict(),
        snapshot=dict(),
        state=dict(choices=['absent', 'present', 'detached', 'list'], default='present'),
        tags=dict(type='dict', default={}),
        wait=dict(type='bool', default=True),
        wait_timeout=dict(type='int', default=300),
    )

    mutually_exclusive = [('volume_id', 'volume_size')]
    required_if = [
        ('state', 'absent', ['volume_id']),
        ('state', 'present', ['instance_id', 'availability_zone'], True),
        ('state', 'present', ['volume_id', 'volume_size', 'snapshot', 'name'], True),
    ]

    module = AnsibleAWSModule(argument_spec=argument_spec, mutually_exclusive=mutually_exclusive, required_if=required_if, supports_check_mode=True)

    state = module.params['state']

    try:
        ec2 = module.client('ec2', retry_decorator=AWSRetry.jittered_backoff())
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to connect to EC2')

    volume = EC2Volume(module, ec2)

    result = {}
    volume.reconcile_state()
    if state != 'absent':
        result['volume'] = _format_volume_info(volume.volume)
    result['changed'] = volume.changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
