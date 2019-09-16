#!/usr/bin/python
# Copyright (C) 2019 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ec2_snapshot_import
short_description: Imports a disk into an EBS snapshot
description:
    - Imports a disk into an EBS snapshot
version_added: "2.10"
options:
  description:
    description:
      - description of the import snapshot task
    required: false
    type: str
  format:
    description:
      - The format of the disk image being imported.
    required: true
    type: str
  url:
    description:
      - The URL to the Amazon S3-based disk image being imported. It can either be a https URL (https://..) or an Amazon S3 URL (s3://..).
        Either C(url) or C(s3_bucket) and C(s3_key) are required.
    required: false
    type: str
  s3_bucket:
    description:
      - The name of the S3 bucket where the disk image is located.
      - C(s3_bucket) and C(s3_key) are required together if C(url) is not used.
    required: false
    type: str
  s3_key:
    description:
      - The file name of the disk image.
      - C(s3_bucket) and C(s3_key) are required together if C(url) is not used.
    required: false
    type: str
  encrypted:
    description:
      - Whether or not the destination Snapshot should be encrypted.
    type: bool
    default: 'no'
  kms_key_id:
    description:
      - KMS key id used to encrypt snapshot. If not specified, defaults to EBS Customer Master Key (CMK) for that account.
    required: false
    type: str
  role_name:
    description:
      - The name of the role to use when not using the default role, 'vmimport'.
    required: false
    type: str
  wait:
    description:
      - wait for the snapshot to be ready
    type: bool
    required: false
    default: yes
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
      - specify 0 to wait forever
    required: false
    type: int
    default: 900
  tags:
    description:
      - A hash/dictionary of tags to add to the new Snapshot; '{"key":"value"}' and '{"key":"value","key":"value"}'
    required: false
    type: dict

author: "Brian C. Lane (@bcl)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Import an S3 object as a snapshot
ec2_snapshot_import:
  description: simple-http-server
  format: raw
  s3_bucket: mybucket
  s3_key: server-image.ami
  wait: yes
  tags:
    Name: Snapshot-Name
'''

RETURN = '''
snapshot_id:
    description: id of the created snapshot
    returned: when snapshot is created
    type: str
    sample: "snap-1234abcd"
description:
    description: description of snapshot
    returned: when snapshot is created
    type: str
    sample: "simple-http-server"
format:
    description: format of the disk image being imported
    returned: when snapshot is created
    type: str
    sample: "raw"
disk_image_size:
    description: size of the disk image being imported, in bytes.
    returned: when snapshot is created
    type: float
    sample: 3836739584.0
user_bucket:
    description: S3 bucket with the image to import
    returned: when snapshot is created
    type: dict
    sample: {
        "s3_bucket": "mybucket",
        "s3_key": "server-image.ami"
    }
status:
    description: status of the import operation
    returned: when snapshot is created
    type: str
    sample: "completed"
'''


import time

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict

try:
    import botocore
except ImportError:
    pass


def wait_for_import_snapshot(connection, wait_timeout, import_task_id):

    params = {
        'ImportTaskIds': [import_task_id]
    }
    start_time = time.time()
    while True:
        status = connection.describe_import_snapshot_tasks(**params)

        # What are the valid status values?
        if len(status['ImportSnapshotTasks']) > 1:
            raise RuntimeError("Should only be 1 Import Snapshot Task with this id.")

        task = status['ImportSnapshotTasks'][0]
        if task['SnapshotTaskDetail']['Status'] in ['completed']:
            return status

        if time.time() - start_time > wait_timeout:
            raise RuntimeError('Wait timeout exceeded (%s sec)' % wait_timeout)

        time.sleep(5)


def import_snapshot(module, connection):
    description = module.params.get('description')
    image_format = module.params.get('format')
    url = module.params.get('url')
    s3_bucket = module.params.get('s3_bucket')
    s3_key = module.params.get('s3_key')
    encrypted = module.params.get('encrypted')
    kms_key_id = module.params.get('kms_key_id')
    role_name = module.params.get('role_name')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')
    tags = module.params.get('tags')

    if module.check_mode:
        module.exit_json(changed=True, msg="IMPORT operation skipped - running in check mode")

    try:
        params = {
            'Description': description,
            'DiskContainer': {
                'Description': description,
                'Format': image_format,
            },
            'Encrypted': encrypted
        }
        if url:
            params['DiskContainer']['Url'] = url
        else:
            params['DiskContainer']['UserBucket'] = {
                'S3Bucket': s3_bucket,
                'S3Key': s3_key
            }
        if kms_key_id:
            params['KmsKeyId'] = kms_key_id
        if role_name:
            params['RoleName'] = role_name

        task = connection.import_snapshot(**params)
        import_task_id = task['ImportTaskId']
        detail = task['SnapshotTaskDetail']

        if wait:
            status = wait_for_import_snapshot(connection, wait_timeout, import_task_id)
            detail = status['ImportSnapshotTasks'][0]['SnapshotTaskDetail']

        if tags:
            connection.create_tags(
                Resources=[detail["SnapshotId"]],
                Tags=[{'Key': k, 'Value': v} for k, v in tags.items()]
            )
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError, RuntimeError) as e:
        module.fail_json_aws(e, msg="Error importing image")

    module.exit_json(changed=True, **camel_dict_to_snake_dict(detail))


def snapshot_import_ansible_module():
    argument_spec = dict(
        description=dict(default=''),
        wait=dict(type='bool', default=True),
        wait_timeout=dict(type='int', default=900),
        format=dict(required=True),
        url=dict(),
        s3_bucket=dict(),
        s3_key=dict(),
        encrypted=dict(type='bool', default=False),
        kms_key_id=dict(),
        role_name=dict(),
        tags=dict(type='dict')
    )
    return AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[['s3_bucket', 'url']],
        required_one_of=[['s3_bucket', 'url']],
        required_together=[['s3_bucket', 's3_key']]
    )


def main():
    module = snapshot_import_ansible_module()
    connection = module.client('ec2')
    import_snapshot(module, connection)


if __name__ == '__main__':
    main()
