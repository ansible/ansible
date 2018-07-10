#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: efs_facts
short_description: Get information about Amazon EFS file systems
description:
    - Module searches Amazon EFS file systems
version_added: "2.2"
requirements: [ boto3 ]
author:
    - "Ryan Sydnor (@ryansydnor)"
options:
    name:
        description:
            - Creation Token of Amazon EFS file system.
    id:
        description:
            - ID of Amazon EFS.
    tags:
        description:
            - List of tags of Amazon EFS. Should be defined as dictionary
    targets:
        description:
          - list of targets on which to filter the returned results
          - result must match all of the specified targets, each of which can be
            a security group ID, a subnet ID or an IP address
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# find all existing efs
- efs_facts:
  register: result

- efs_facts:
    name: myTestNameTag

- efs_facts:
    id: fs-1234abcd

# Searching all EFS instances with tag Name = 'myTestNameTag', in subnet 'subnet-1a2b3c4d' and with security group 'sg-4d3c2b1a'
- efs_facts:
    tags:
        name: myTestNameTag
    targets:
        - subnet-1a2b3c4d
        - sg-4d3c2b1a
'''

RETURN = '''
creation_time:
    description: timestamp of creation date
    returned: always
    type: str
    sample: "2015-11-16 07:30:57-05:00"
creation_token:
    description: EFS creation token
    returned: always
    type: str
    sample: console-88609e04-9a0e-4a2e-912c-feaa99509961
file_system_id:
    description: ID of the file system
    returned: always
    type: str
    sample: fs-xxxxxxxx
life_cycle_state:
    description: state of the EFS file system
    returned: always
    type: str
    sample: creating, available, deleting, deleted
mount_point:
    description: url of file system
    returned: always
    type: str
    sample: .fs-xxxxxxxx.efs.us-west-2.amazonaws.com:/
mount_targets:
    description: list of mount targets
    returned: always
    type: list
    sample:
        [
            {
                "file_system_id": "fs-a7ad440e",
                "ip_address": "172.31.17.173",
                "life_cycle_state": "available",
                "mount_target_id": "fsmt-d8907871",
                "network_interface_id": "eni-6e387e26",
                "owner_id": "740748460359",
                "security_groups": [
                    "sg-a30b22c6"
                ],
                "subnet_id": "subnet-e265c895"
            },
            ...
        ]
name:
    description: name of the file system
    returned: always
    type: str
    sample: my-efs
number_of_mount_targets:
    description: the number of targets mounted
    returned: always
    type: int
    sample: 3
owner_id:
    description: AWS account ID of EFS owner
    returned: always
    type: str
    sample: XXXXXXXXXXXX
size_in_bytes:
    description: size of the file system in bytes as of a timestamp
    returned: always
    type: dict
    sample:
        {
            "timestamp": "2015-12-21 13:59:59-05:00",
            "value": 12288
        }
performance_mode:
    description: performance mode of the file system
    returned: always
    type: str
    sample: "generalPurpose"
tags:
    description: tags on the efs instance
    returned: always
    type: dict
    sample:
        {
            "name": "my-efs",
            "key": "Value"
        }

'''


from collections import defaultdict

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, ec2_argument_spec, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict


class EFSConnection(object):
    STATE_CREATING = 'creating'
    STATE_AVAILABLE = 'available'
    STATE_DELETING = 'deleting'
    STATE_DELETED = 'deleted'

    def __init__(self, module, region, **aws_connect_params):
        try:
            self.connection = boto3_conn(module, conn_type='client',
                                         resource='efs', region=region,
                                         **aws_connect_params)
            self.module = module
        except Exception as e:
            module.fail_json(msg="Failed to connect to AWS: %s" % str(e))

        self.region = region

    @AWSRetry.exponential_backoff(catch_extra_error_codes=['ThrottlingException'])
    def list_file_systems(self, **kwargs):
        """
         Returns generator of file systems including all attributes of FS
        """
        paginator = self.connection.get_paginator('describe_file_systems')
        return paginator.paginate(**kwargs).build_full_result()['FileSystems']

    @AWSRetry.exponential_backoff(catch_extra_error_codes=['ThrottlingException'])
    def get_tags(self, file_system_id):
        """
         Returns tag list for selected instance of EFS
        """
        paginator = self.connection.get_paginator('describe_tags')
        return boto3_tag_list_to_ansible_dict(paginator.paginate(FileSystemId=file_system_id).build_full_result()['Tags'])

    @AWSRetry.exponential_backoff(catch_extra_error_codes=['ThrottlingException'])
    def get_mount_targets(self, file_system_id):
        """
         Returns mount targets for selected instance of EFS
        """
        paginator = self.connection.get_paginator('describe_mount_targets')
        return paginator.paginate(FileSystemId=file_system_id).build_full_result()['MountTargets']

    @AWSRetry.jittered_backoff(catch_extra_error_codes=['ThrottlingException'])
    def get_security_groups(self, mount_target_id):
        """
         Returns security groups for selected instance of EFS
        """
        return self.connection.describe_mount_target_security_groups(MountTargetId=mount_target_id)['SecurityGroups']

    def get_mount_targets_data(self, file_systems):
        for item in file_systems:
            if item['life_cycle_state'] == self.STATE_AVAILABLE:
                try:
                    mount_targets = self.get_mount_targets(item['file_system_id'])
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    self.module.fail_json_aws(e, msg="Couldn't get EFS targets")
                for mt in mount_targets:
                    item['mount_targets'].append(camel_dict_to_snake_dict(mt))
        return file_systems

    def get_security_groups_data(self, file_systems):
        for item in file_systems:
            if item['life_cycle_state'] == self.STATE_AVAILABLE:
                for target in item['mount_targets']:
                    if target['life_cycle_state'] == self.STATE_AVAILABLE:
                        try:
                            target['security_groups'] = self.get_security_groups(target['mount_target_id'])
                        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                            self.module.fail_json_aws(e, msg="Couldn't get EFS security groups")
                    else:
                        target['security_groups'] = []
            else:
                item['tags'] = {}
                item['mount_targets'] = []
        return file_systems

    def get_file_systems(self, file_system_id=None, creation_token=None):
        kwargs = dict()
        if file_system_id:
            kwargs['FileSystemId'] = file_system_id
        if creation_token:
            kwargs['CreationToken'] = creation_token
        try:
            file_systems = self.list_file_systems(**kwargs)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Couldn't get EFS file systems")

        results = list()
        for item in file_systems:
            item['CreationTime'] = str(item['CreationTime'])
            """
            Suffix of network path to be used as NFS device for mount. More detail here:
            http://docs.aws.amazon.com/efs/latest/ug/gs-step-three-connect-to-ec2-instance.html
            """
            item['MountPoint'] = '.%s.efs.%s.amazonaws.com:/' % (item['FileSystemId'], self.region)
            if 'Timestamp' in item['SizeInBytes']:
                item['SizeInBytes']['Timestamp'] = str(item['SizeInBytes']['Timestamp'])
            result = camel_dict_to_snake_dict(item)
            result['tags'] = {}
            result['mount_targets'] = []
            # Set tags *after* doing camel to snake
            if result['life_cycle_state'] == self.STATE_AVAILABLE:
                try:
                    result['tags'] = self.get_tags(result['file_system_id'])
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    self.module.fail_json_aws(e, msg="Couldn't get EFS tags")
            results.append(result)
        return results


def prefix_to_attr(attr_id):
    """
     Helper method to convert ID prefix to mount target attribute
    """
    attr_by_prefix = {
        'fsmt-': 'mount_target_id',
        'subnet-': 'subnet_id',
        'eni-': 'network_interface_id',
        'sg-': 'security_groups'
    }
    return first_or_default([attr_name for (prefix, attr_name) in attr_by_prefix.items()
                             if str(attr_id).startswith(prefix)], 'ip_address')


def first_or_default(items, default=None):
    """
     Helper method to fetch first element of list (if exists)
    """
    for item in items:
        return item
    return default


def has_tags(available, required):
    """
    Helper method to determine if tag requested already exists
    """
    for key, value in required.items():
        if key not in available or value != available[key]:
            return False
    return True


def has_targets(available, required):
    """
    Helper method to determine if mount target requested already exists
    """
    grouped = group_list_of_dict(available)
    for (value, field) in required:
        if field not in grouped or value not in grouped[field]:
            return False
    return True


def group_list_of_dict(array):
    """
     Helper method to group list of dict to dict with all possible values
    """
    result = defaultdict(list)
    for item in array:
        for key, value in item.items():
            result[key] += value if isinstance(value, list) else [value]
    return result


def main():
    """
     Module action handler
    """
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        id=dict(),
        name=dict(),
        tags=dict(type="dict", default={}),
        targets=dict(type="list", default=[])
    ))

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True)

    region, _, aws_connect_params = get_aws_connection_info(module, boto3=True)
    connection = EFSConnection(module, region, **aws_connect_params)

    name = module.params.get('name')
    fs_id = module.params.get('id')
    tags = module.params.get('tags')
    targets = module.params.get('targets')

    file_systems_info = connection.get_file_systems(fs_id, name)

    if tags:
        file_systems_info = [item for item in file_systems_info if has_tags(item['tags'], tags)]

    file_systems_info = connection.get_mount_targets_data(file_systems_info)
    file_systems_info = connection.get_security_groups_data(file_systems_info)

    if targets:
        targets = [(item, prefix_to_attr(item)) for item in targets]
        file_systems_info = [item for item in file_systems_info if has_targets(item['mount_targets'], targets)]

    module.exit_json(changed=False, ansible_facts={'efs': file_systems_info})


if __name__ == '__main__':
    main()
