#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: ec2_vol
short_description: create and attach a volume, return volume id and device map
description:
    - creates an EBS volume and optionally attaches it to an instance.
      If both an instance ID and a device name is given and the instance has a device at the device name, then no volume is created and no attachment is made.
      This module has a dependency on python-boto.
version_added: "1.1"
options:
  instance:
    description:
      - instance ID if you wish to attach the volume. Since 1.9 you can set to None to detach.
  name:
    description:
      - volume Name tag if you wish to attach an existing volume (requires instance)
    version_added: "1.6"
  id:
    description:
      - volume id if you wish to attach an existing volume (requires instance) or remove an existing volume
    version_added: "1.6"
  volume_size:
    description:
      - size of volume (in GB) to create.
  volume_type:
    description:
      - Type of EBS volume; standard (magnetic), gp2 (SSD), io1 (Provisioned IOPS), st1 (Throughput Optimized HDD), sc1 (Cold HDD).
        "Standard" is the old EBS default and continues to remain the Ansible default for backwards compatibility.
    default: standard
    version_added: "1.9"
  iops:
    description:
      - the provisioned IOPs you want to associate with this volume (integer).
    default: 100
    version_added: "1.3"
  encrypted:
    description:
      - Enable encryption at rest for this volume.
    default: 'no'
    version_added: "1.8"
  kms_key_id:
    description:
      - Specify the id of the KMS key to use.
    version_added: "2.3"
  device_name:
    description:
      - device id to override device mapping. Assumes /dev/sdf for Linux/UNIX and /dev/xvdf for Windows.
  delete_on_termination:
    description:
      - When set to "yes", the volume will be deleted upon instance termination.
    type: bool
    default: 'no'
    version_added: "2.1"
  zone:
    description:
      - zone in which to create the volume, if unset uses the zone the instance is in (if set)
    aliases: ['aws_zone', 'ec2_zone']
  snapshot:
    description:
      - snapshot ID on which to base the volume
    version_added: "1.5"
  validate_certs:
    description:
      - When set to "no", SSL certificates will not be validated for boto versions >= 2.6.0.
    type: bool
    default: 'yes'
    version_added: "1.5"
  state:
    description:
      - whether to ensure the volume is present or absent, or to list existing volumes (The C(list) option was added in version 1.8).
    default: present
    choices: ['absent', 'present', 'list']
    version_added: "1.6"
  tags:
    description:
      - tag:value pairs to add to the volume after creation
    default: {}
    version_added: "2.3"
author: "Lester Wade (@lwade)"
extends_documentation_fragment:
    - aws
    - ec2
requirements:
  - botocore
  - boto3
'''

EXAMPLES = '''
# Simple attachment action
- ec2_vol:
    instance: XXXXXX
    volume_size: 5
    device_name: sdd

# Example using custom iops params
- ec2_vol:
    instance: XXXXXX
    volume_size: 5
    iops: 100
    device_name: sdd

# Example using snapshot id
- ec2_vol:
    instance: XXXXXX
    snapshot: "{{ snapshot }}"

# Playbook example combined with instance launch
- ec2:
    keypair: "{{ keypair }}"
    image: "{{ image }}"
    wait: yes
    count: 3
  register: ec2
- ec2_vol:
    instance: "{{ item.id }}"
    volume_size: 5
  with_items: "{{ ec2.instances }}"
  register: ec2_vol

# Example: Launch an instance and then add a volume if not already attached
#   * Volume will be created with the given name if not already created.
#   * Nothing will happen if the volume is already attached.
#   * Requires Ansible 2.0

- ec2:
    keypair: "{{ keypair }}"
    image: "{{ image }}"
    zone: YYYYYY
    id: my_instance
    wait: yes
    count: 1
  register: ec2

- ec2_vol:
    instance: "{{ item.id }}"
    name: my_existing_volume_Name_tag
    device_name: /dev/xvdf
  with_items: "{{ ec2.instances }}"
  register: ec2_vol

# Remove a volume
- ec2_vol:
    id: vol-XXXXXXXX
    state: absent

# Detach a volume (since 1.9)
- ec2_vol:
    id: vol-XXXXXXXX
    instance: None

# List volumes for an instance
- ec2_vol:
    instance: i-XXXXXX
    state: list

# Create new volume using SSD storage
- ec2_vol:
    instance: XXXXXX
    volume_size: 50
    volume_type: gp2
    device_name: /dev/xvdf

# Attach an existing volume to instance. The volume will be deleted upon instance termination.
- ec2_vol:
    instance: XXXXXX
    id: XXXXXX
    device_name: /dev/sdf
    delete_on_termination: yes
'''

RETURN = '''
device:
    description: device name of attached volume
    returned: when success
    type: string
    sample: "/def/sdf"
volume_id:
    description: the id of volume
    returned: when success
    type: string
    sample: "vol-35b333d9"
volume_type:
    description: the volume type
    returned: when success
    type: string
    sample: "standard"
volume:
    description: a dictionary containing detailed attributes of the volume
    returned: when success
    type: string
    sample: {
        "attachment_set": {
            "attach_time": "2015-10-23T00:22:29.000Z",
            "deleteOnTermination": "false",
            "device": "/dev/sdf",
            "instance_id": "i-8356263c",
            "status": "attached"
        },
        "create_time": "2015-10-21T14:36:08.870Z",
        "encrypted": false,
        "id": "vol-35b333d9",
        "iops": null,
        "size": 1,
        "snapshot_id": "",
        "status": "in-use",
        "tags": {
            "env": "dev"
        },
        "type": "standard",
        "zone": "us-east-1b"
    }
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (
    AWSRetry,
    ec2_argument_spec,
    camel_dict_to_snake_dict,
    boto3_tag_list_to_ansible_dict,
    ansible_dict_to_boto3_filter_list,
    ansible_dict_to_boto3_tag_list,
    compare_aws_tags
)


def get_instance(module, ec2_conn, instance_id=None):
    instance = None
    if not instance_id:
        return instance

    try:
        reservation_response = ec2_conn.describe_instances(InstanceIds=[instance_id])
        instance = camel_dict_to_snake_dict(reservation_response['Reservations'][0]['Instances'][0])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Error while getting Instance wiht id {0}'.format(instance))

    return instance


def get_volume(module, ec2_conn, vol_id=None, fail_on_not_found=True):
    name = module.params.get('name')
    param_id = module.params.get('id')
    zone = module.params.get('zone')

    if not vol_id:
        vol_id = param_id

    # If no name or id supplied, just try volume creation based on module parameters
    if vol_id is None and name is None:
        return None

    find_params = dict()
    vols = []
    if vol_id:
        find_params['VolumeIds'] = [vol_id]
    elif name:
            find_params['Filters'] = ansible_dict_to_boto3_filter_list({'tag:Name': name})
    elif zone:
            find_params['Filters'] = ansible_dict_to_boto3_filter_list({'availability-zone': zone})

    try:
        vols_response = ec2_conn.describe_volumes(**find_params)
        vols = vols_response.get('Volumes', [])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Error while getting EBS volumes', params=find_params)

    if not vols:
        if fail_on_not_found and vol_id:
            msg = "Could not find the volume with id: %s" % vol_id
            if name:
                msg += (" and name: %s" % name)
            module.fail_json(msg=msg)
        else:
            return None

    if len(vols) > 1:
        module.fail_json(
            msg="Found more than one volume in zone (if specified) with name: %s" % name,
            found=[v['VolumeId'] for v in vols]
        )
    vol = camel_dict_to_snake_dict(vols[0])
    return vol


def get_volumes(module, ec2_conn):

    instance = module.params.get('instance')

    find_params = dict()
    if instance:
        find_params['Filters'] = ansible_dict_to_boto3_filter_list({'attachment.instance-id': instance})

    vols = []
    try:
        vols_response = ec2_conn.describe_volumes(**find_params)
        vols = [camel_dict_to_snake_dict(vol) for vol in vols_response.get('Volumes', [])]
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Error while getting EBS volumes')
    return vols


def delete_volume(module, ec2_conn, volume_id=None):
    changed = False
    if volume_id:
        try:
            ec2_conn.delete_volume(VolumeId=volume_id)
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            if e.response['Error']['Code'] != 'InvalidVolume.NotFound':
                module.fail_json_aws(e, msg='Error while deleting volume')
    return changed


def create_volume(module, ec2_conn, zone):
    changed = False
    iops = module.params.get('iops')
    encrypted = module.params.get('encrypted')
    kms_key_id = module.params.get('kms_key_id')
    volume_size = module.params.get('volume_size')
    volume_type = module.params.get('volume_type')
    snapshot = module.params.get('snapshot')
    # If custom iops is defined we use volume_type "io1" rather than the default of "standard"
    if iops:
        volume_type = 'io1'

    volume = get_volume(module, ec2_conn)
    if volume is None:
        try:
            additional_params = dict()
            changed = True

            if volume_size:
                additional_params['Size'] = int(volume_size)

            if kms_key_id:
                additional_params['KmsKeyId'] = kms_key_id

            if snapshot:
                additional_params['SnapshotId'] = snapshot

            if iops:
                additional_params['Iops'] = int(iops)

            create_vol_response = ec2_conn.create_volume(
                AvailabilityZone=zone,
                Encrypted=encrypted,
                VolumeType=volume_type,
                **additional_params
            )

            waiter = ec2_conn.get_waiter('volume_available')
            waiter.wait(
                VolumeIds=[create_vol_response['VolumeId']],
            )
            volume = get_volume(module, ec2_conn, vol_id=create_vol_response['VolumeId'])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Error while creating EBS volume')

    return volume, changed


def attach_volume(module, ec2_conn, volume_dict, instance_dict, device_name):
    changed = False

    # If device_name isn't set, make a choice based on best practices here:
    # http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/block-device-mapping-concepts.html

    # In future this needs to be more dynamic but combining block device mapping best practices
    # (bounds for devices, as above) with instance.block_device_mapping data would be tricky. For me ;)

    attachment_data = get_attachment_data(volume_dict, wanted_state='attached')
    if attachment_data:
        if attachment_data.get('instance_id', None) != instance_dict['instance_id']:
            module.fail_json(msg="Volume %s is already attached to another instance: %s"
                             % (volume_dict['volume_id'], attachment_data.get('instance_id', None)))
        else:
            return volume_dict, changed
    try:
        attach_response = ec2_conn.attach_volume(
            Device=device_name,
            InstanceId=instance_dict['instance_id'],
            VolumeId=volume_dict['volume_id'],
        )
        waiter = ec2_conn.get_waiter('volume_in_use')
        waiter.wait(
            VolumeIds=[attach_response['VolumeId']],
        )
        changed = True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Error while attaching EBS volume')

    modify_dot_attribute(module, ec2_conn, instance_dict, device_name)

    volume = get_volume(module, ec2_conn, vol_id=volume_dict['volume_id'])
    return volume, changed


def modify_dot_attribute(module, ec2_conn, instance_dict, device_name):
    """ Modify delete_on_termination attribute """

    delete_on_termination = module.params.get('delete_on_termination')
    changed = False

    instance_dict = get_instance(module, ec2_conn=ec2_conn, instance_id=instance_dict['instance_id'])
    mapped_block_device = get_mapped_block_device(instance_dict=instance_dict, device_name=device_name)

    if delete_on_termination != mapped_block_device['ebs']['delete_on_termination']:
        try:
            ec2_conn.modify_instance_attribute(
                InstanceId=instance_dict['instance_id'],
                BlockDeviceMappings={
                    "DeviceName": device_name,
                    "Ebs": {
                        "DeleteOnTermination": delete_on_termination
                    }
                }
            )

            # while instance.block_device_mapping[device_name].delete_on_termination != delete_on_termination:
            #     time.sleep(3)
            #     instance.update()
            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e,
                                 msg='Error while modifiying Block Device Mapping of instances',
                                 instance_id=instance_dict['instance_id'])

    return changed


def get_attachment_data(volume_dict, wanted_state=None):
    attachment_data = {}
    if not volume_dict:
        return attachment_data
    for data in volume_dict.get('attachments', []):
        if wanted_state and wanted_state == data['state']:
            attachment_data = data
            break
        else:
            # No filter, return first
            attachment_data = data
            break

    return attachment_data


def detach_volume(module, ec2_conn, volume_dict):

    changed = False

    attachment_data = get_attachment_data(volume_dict, wanted_state='attached')
    if attachment_data:
        ec2_conn.detach_volume(VolumeId=volume_dict['volume_id'])
        waiter = ec2_conn.get_waiter('volume_available')
        waiter.wait(
            VolumeIds=[volume_dict['volume_id']],
        )
        changed = True

    volume_dict = get_volume(module, ec2_conn, vol_id=volume_dict['volume_id'])
    return volume_dict, changed


def get_volume_info(volume):

    attachment_data = get_attachment_data(volume)
    volume_info = {
        'create_time': volume.get('create_time'),
        'encrypted': volume.get('encrypted'),
        'id': volume.get('volume_id'),
        'iops': volume.get('iops'),
        'size': volume.get('size'),
        'snapshot_id': volume.get('snapshot_id'),
        'status': volume.get('state'),
        'type': volume.get('volume_type'),
        'zone': volume.get('availability_zone'),
        'attachment_set': {
            'attach_time': attachment_data.get('attach_time', None),
            'device': attachment_data.get('device', None),
            'instance_id': attachment_data.get('instance_id', None),
            'status': attachment_data.get('state', None),
            'deleteOnTermination': attachment_data.get('delete_on_termination', None)
        },
        'tags': boto3_tag_list_to_ansible_dict(volume.get('tags'))
    }

    return volume_info


def get_mapped_block_device(instance_dict=None, device_name=None):
    mapped_block_device = None
    if not instance_dict:
        return mapped_block_device
    if not device_name:
        return mapped_block_device

    for device in instance_dict.get('block_device_mappings', []):
        if device['device_name'] == device_name:
            mapped_block_device = device
            break

    return mapped_block_device


def ensure_tags(module, connection, res_id, res_type, tags, add_only):
    changed = False

    filters = ansible_dict_to_boto3_filter_list({'resource-id': res_id, 'resource-type': res_type})
    cur_tags = None
    try:
        cur_tags = connection.describe_tags(Filters=filters)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't describe tags")

    purge_tags = bool(not add_only)
    to_update, to_delete = compare_aws_tags(boto3_tag_list_to_ansible_dict(cur_tags.get('Tags')), tags, purge_tags)
    final_tags = boto3_tag_list_to_ansible_dict(cur_tags.get('Tags'))

    if to_update:
        try:
            if module.check_mode:
                # update tags
                final_tags.update(to_update)
            else:
                AWSRetry.exponential_backoff()(connection.create_tags)(
                    Resources=[res_id],
                    Tags=ansible_dict_to_boto3_tag_list(to_update)
                )

            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't create tags")

    if to_delete:
        try:
            if module.check_mode:
                # update tags
                for key in to_delete:
                    del final_tags[key]
            else:
                tags_list = []
                for key in to_delete:
                    tags_list.append({'Key': key})

                AWSRetry.exponential_backoff()(connection.delete_tags)(Resources=[res_id], Tags=tags_list)

            changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't delete tags")

    if not module.check_mode and (to_update or to_delete):
        try:
            response = connection.describe_tags(Filters=filters)
            final_tags = boto3_tag_list_to_ansible_dict(response.get('Tags'))
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't describe tags")

    return final_tags, changed


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        instance=dict(),
        id=dict(),
        name=dict(),
        volume_size=dict(),
        volume_type=dict(choices=['standard', 'gp2', 'io1', 'st1', 'sc1'], default='standard'),
        iops=dict(),
        encrypted=dict(type='bool', default=False),
        kms_key_id=dict(),
        device_name=dict(),
        delete_on_termination=dict(type='bool', default=False),
        zone=dict(aliases=['availability_zone', 'aws_zone', 'ec2_zone']),
        snapshot=dict(),
        state=dict(choices=['absent', 'present', 'list'], default='present'),
        tags=dict(type='dict', default={})
    )
    )
    module = AnsibleAWSModule(argument_spec=argument_spec)

    param_id = module.params.get('id')
    name = module.params.get('name')
    instance = module.params.get('instance')
    volume_size = module.params.get('volume_size')
    device_name = module.params.get('device_name')
    zone = module.params.get('zone')
    snapshot = module.params.get('snapshot')
    state = module.params.get('state')
    tags = module.params.get('tags')

    # Ensure we have the zone or can get the zone
    if instance is None and zone is None and state == 'present':
        module.fail_json(msg="You must specify either instance or zone")

    # Set volume detach flag
    if instance == 'None' or instance == '':
        instance = None
        detach_vol_flag = True
    else:
        detach_vol_flag = False

    # Set changed flag
    changed = False

    ec2_conn = module.client('ec2')

    if state == 'list':
        returned_volumes = []
        vols = get_volumes(module, ec2_conn)

        for v in vols:
            returned_volumes.append(get_volume_info(v))

        module.exit_json(changed=False, volumes=returned_volumes)

    # Here we need to get the zone info for the instance. This covers situation where
    # instance is specified but zone isn't.
    # Useful for playbooks chaining instance launch with volume create + attach and where the
    # zone doesn't matter to the user.
    inst = None

    # Delaying the checks until after the instance check allows us to get volume ids for existing volumes
    # without needing to pass an unused volume_size
    if not volume_size and not (param_id or name or snapshot):
        module.fail_json(msg="You must specify volume_size or identify an existing volume by id, name, or snapshot")

    if volume_size and param_id:
        module.fail_json(msg="Cannot specify volume_size together with id")

    # Try getting volume
    volume = get_volume(module, ec2_conn, fail_on_not_found=False)
    if state == 'present':
        if instance:
            inst = get_instance(module, ec2_conn, instance_id=instance)
            zone = inst['placement']['availability_zone']

            # Use password data attribute to tell whether the instance is Windows or Linux
            if device_name is None:
                if inst['platform'] == 'Windows':
                    device_name = '/dev/xvdf'
                else:
                    device_name = '/dev/sdf'

            # Check if there is a volume already mounted there.
            mapped_device = get_mapped_block_device(instance_dict=inst, device_name=device_name)
            if mapped_device:
                other_volume_mapped = False

                if volume:
                    if volume['volume_id'] != mapped_device['ebs']['volume_id']:
                        other_volume_mapped = True
                else:
                    # No volume found so this is another volume
                    other_volume_mapped = True

                if other_volume_mapped:
                    module.fail_json(
                        msg="Volume mapping for %s already exists on instance %s" % (device_name, instance),
                        volume_id=mapped_device['ebs']['volume_id'],
                        found_volume=volume,
                        device=device_name,
                        changed=False
                    )

        attach_state_changed = False
        volume, created = create_volume(module, ec2_conn, zone=zone)
        tags['Name'] = name
        final_tags, tags_changed = ensure_tags(module, ec2_conn, volume['volume_id'], 'volume', tags, False)
        if detach_vol_flag:
            volume, attach_state_changed = detach_volume(module, ec2_conn, volume_dict=volume)
        elif inst is not None:
            volume, attach_state_changed = attach_volume(
                module, ec2_conn, volume_dict=volume, instance_dict=inst, device_name=device_name)

        changed = changed or tags_changed or created or attach_state_changed

        # Add device, volume_id and volume_type parameters separately to maintain backward compatibility
        volume_info = get_volume_info(volume)

        module.exit_json(changed=changed, volume=volume_info, device=volume_info['attachment_set']['device'],
                         volume_id=volume_info['id'], volume_type=volume_info['type'])
    elif state == 'absent':
        if not name and not param_id:
            module.fail_json('At list name or id is required for deletion')
        if volume:
            detach_volume(module, ec2_conn, volume_dict=volume)
            changed = delete_volume(module, ec2_conn, volume_id=volume['volume_id'])
        module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
