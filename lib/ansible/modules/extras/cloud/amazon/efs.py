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
module: efs
short_description: create and maintain EFS file systems
description:
    - Module allows create, search and destroy Amazon EFS file systems
version_added: "2.2"
requirements: [ boto3 ]
author:
    - "Ryan Sydnor (@ryansydnor)"
    - "Artem Kazakov (@akazakov)"
options:
    state:
        description:
            - Allows to create, search and destroy Amazon EFS file system
        required: false
        default: 'present'
        choices: ['present', 'absent']
    name:
        description:
            - Creation Token of Amazon EFS file system. Required for create. Either name or ID required for delete.
        required: false
        default: None
    id:
        description:
            - ID of Amazon EFS. Either name or ID required for delete.
        required: false
        default: None
    performance_mode:
        description:
            - File system's performance mode to use. Only takes effect during creation.
        required: false
        default: 'general_purpose'
        choices: ['general_purpose', 'max_io']
    tags:
        description:
            - "List of tags of Amazon EFS. Should be defined as dictionary
              In case of 'present' state with list of tags and existing EFS (matched by 'name'), tags of EFS will be replaced with provided data."
        required: false
        default: None
    targets:
        description:
            - "List of mounted targets. It should be a list of dictionaries, every dictionary should include next attributes:
                   - subnet_id - Mandatory. The ID of the subnet to add the mount target in.
                   - ip_address - Optional. A valid IPv4 address within the address range of the specified subnet.
                   - security_groups - Optional. List of security group IDs, of the form 'sg-xxxxxxxx'. These must be for the same VPC as subnet specified
               This data may be modified for existing EFS using state 'present' and new list of mount targets."
        required: false
        default: None
    wait:
        description:
            - "In case of 'present' state should wait for EFS 'available' life cycle state (of course, if current state not 'deleting' or 'deleted')
               In case of 'absent' state should wait for EFS 'deleted' life cycle state"
        required: false
        default: "no"
        choices: ["yes", "no"]
    wait_timeout:
        description:
            - How long the module should wait (in seconds) for desired state before returning. Zero means wait as long as necessary.
        required: false
        default: 0
extends_documentation_fragment:
    - aws
'''

EXAMPLES = '''
# EFS provisioning
- efs:
    state: present
    name: myTestEFS
    tags:
        name: myTestNameTag
        purpose: file-storage
    targets:
        - subnet_id: subnet-748c5d03
          security_groups: [ "sg-1a2b3c4d" ]

# Modifying EFS data
- efs:
    state: present
    name: myTestEFS
    tags:
        name: myAnotherTestTag
    targets:
        - subnet_id: subnet-7654fdca
          security_groups: [ "sg-4c5d6f7a" ]

# Deleting EFS
- efs:
    state: absent
    name: myTestEFS
'''

RETURN = '''
creation_time:
    description: timestamp of creation date
    returned:
    type: datetime
    sample: 2015-11-16 07:30:57-05:00
creation_token:
    description: EFS creation token
    returned:
    type: UUID
    sample: console-88609e04-9a0e-4a2e-912c-feaa99509961
file_system_id:
    description: ID of the file system
    returned:
    type: unique ID
    sample: fs-xxxxxxxx
life_cycle_state:
    description: state of the EFS file system
    returned:
    type: str
    sample: creating, available, deleting, deleted
mount_point:
    description: url of file system
    returned:
    type: str
    sample: .fs-xxxxxxxx.efs.us-west-2.amazonaws.com:/
mount_targets:
    description: list of mount targets
    returned:
    type: list of dicts
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
    returned:
    type: str
    sample: my-efs
number_of_mount_targets:
    description: the number of targets mounted
    returned:
    type: int
    sample: 3
owner_id:
    description: AWS account ID of EFS owner
    returned:
    type: str
    sample: XXXXXXXXXXXX
size_in_bytes:
    description: size of the file system in bytes as of a timestamp
    returned:
    type: dict
    sample:
        {
            "timestamp": "2015-12-21 13:59:59-05:00",
            "value": 12288
        }
performance_mode:
    description: performance mode of the file system
    returned:
    type: str
    sample: "generalPurpose"
tags:
    description: tags on the efs instance
    returned:
    type: dict
    sample:
        {
            "name": "my-efs",
            "key": "Value"
        }

'''

import sys
from time import sleep
from time import time as timestamp
from collections import defaultdict

try:
    from botocore.exceptions import ClientError
    import boto3
    HAS_BOTO3 = True
except ImportError as e:
    HAS_BOTO3 = False


class EFSConnection(object):

    DEFAULT_WAIT_TIMEOUT_SECONDS = 0

    STATE_CREATING = 'creating'
    STATE_AVAILABLE = 'available'
    STATE_DELETING = 'deleting'
    STATE_DELETED = 'deleted'

    def __init__(self, module, region, **aws_connect_params):
        try:
            self.connection = boto3_conn(module, conn_type='client',
                                         resource='efs', region=region,
                                         **aws_connect_params)
        except Exception as e:
            module.fail_json(msg="Failed to connect to AWS: %s" % str(e))

        self.region = region
        self.wait = module.params.get('wait')
        self.wait_timeout = module.params.get('wait_timeout')

    def get_file_systems(self, **kwargs):
        """
         Returns generator of file systems including all attributes of FS
        """
        items = iterate_all(
            'FileSystems',
            self.connection.describe_file_systems,
            **kwargs
        )
        for item in items:
            item['CreationTime'] = str(item['CreationTime'])
            """
            Suffix of network path to be used as NFS device for mount. More detail here:
            http://docs.aws.amazon.com/efs/latest/ug/gs-step-three-connect-to-ec2-instance.html
            """
            item['MountPoint'] = '.%s.efs.%s.amazonaws.com:/' % (item['FileSystemId'], self.region)
            if 'Timestamp' in item['SizeInBytes']:
                item['SizeInBytes']['Timestamp'] = str(item['SizeInBytes']['Timestamp'])
            if item['LifeCycleState'] == self.STATE_AVAILABLE:
                item['Tags'] = self.get_tags(FileSystemId=item['FileSystemId'])
                item['MountTargets'] = list(self.get_mount_targets(FileSystemId=item['FileSystemId']))
            else:
                item['Tags'] = {}
                item['MountTargets'] = []
            yield item

    def get_tags(self, **kwargs):
        """
         Returns tag list for selected instance of EFS
        """
        tags = iterate_all(
            'Tags',
            self.connection.describe_tags,
            **kwargs
        )
        return dict((tag['Key'], tag['Value']) for tag in tags)

    def get_mount_targets(self, **kwargs):
        """
         Returns mount targets for selected instance of EFS
        """
        targets = iterate_all(
            'MountTargets',
            self.connection.describe_mount_targets,
            **kwargs
        )
        for target in targets:
            if target['LifeCycleState'] == self.STATE_AVAILABLE:
                target['SecurityGroups'] = list(self.get_security_groups(
                    MountTargetId=target['MountTargetId']
                ))
            else:
                target['SecurityGroups'] = []
            yield target

    def get_security_groups(self, **kwargs):
        """
         Returns security groups for selected instance of EFS
        """
        return iterate_all(
            'SecurityGroups',
            self.connection.describe_mount_target_security_groups,
            **kwargs
        )

    def get_file_system_id(self, name):
        """
         Returns ID of instance by instance name
        """
        info = first_or_default(iterate_all(
            'FileSystems',
            self.connection.describe_file_systems,
            CreationToken=name
        ))
        return info and info['FileSystemId'] or None

    def get_file_system_state(self, name, file_system_id=None):
        """
         Returns state of filesystem by EFS id/name
        """
        info = first_or_default(iterate_all(
            'FileSystems',
            self.connection.describe_file_systems,
            CreationToken=name,
            FileSystemId=file_system_id
        ))
        return info and info['LifeCycleState'] or self.STATE_DELETED

    def get_mount_targets_in_state(self, file_system_id, states=None):
        """
         Returns states of mount targets of selected EFS with selected state(s) (optional)
        """
        targets = iterate_all(
            'MountTargets',
            self.connection.describe_mount_targets,
            FileSystemId=file_system_id
        )

        if states:
            if not isinstance(states, list):
                states = [states]
            targets = filter(lambda target: target['LifeCycleState'] in states, targets)

        return list(targets)

    def create_file_system(self, name, performance_mode):
        """
         Creates new filesystem with selected name
        """
        changed = False
        state = self.get_file_system_state(name)
        if state in [self.STATE_DELETING, self.STATE_DELETED]:
            wait_for(
                lambda: self.get_file_system_state(name),
                self.STATE_DELETED
            )
            self.connection.create_file_system(CreationToken=name, PerformanceMode=performance_mode)
            changed = True

        # we always wait for the state to be available when creating.
        # if we try to take any actions on the file system before it's available
        # we'll throw errors
        wait_for(
            lambda: self.get_file_system_state(name),
            self.STATE_AVAILABLE,
            self.wait_timeout
        )

        return changed

    def converge_file_system(self, name, tags, targets):
        """
         Change attributes (mount targets and tags) of filesystem by name
        """
        result = False
        fs_id = self.get_file_system_id(name)

        if tags is not None:
            tags_to_create, _, tags_to_delete = dict_diff(self.get_tags(FileSystemId=fs_id), tags)

            if tags_to_delete:
                self.connection.delete_tags(
                    FileSystemId=fs_id,
                    TagKeys=[item[0] for item in tags_to_delete]
                )
                result = True

            if tags_to_create:
                self.connection.create_tags(
                    FileSystemId=fs_id,
                    Tags=[{'Key': item[0], 'Value': item[1]} for item in tags_to_create]
                )
                result = True

        if targets is not None:
            incomplete_states = [self.STATE_CREATING, self.STATE_DELETING]
            wait_for(
                lambda: len(self.get_mount_targets_in_state(fs_id, incomplete_states)),
                0
            )

            index_by_subnet_id = lambda items: dict((item['SubnetId'], item) for item in items)

            current_targets = index_by_subnet_id(self.get_mount_targets(FileSystemId=fs_id))
            targets = index_by_subnet_id(targets)

            targets_to_create, intersection, targets_to_delete = dict_diff(current_targets,
                                                                           targets, True)

            """ To modify mount target it should be deleted and created again """
            changed = filter(
                lambda sid: not targets_equal(['SubnetId', 'IpAddress', 'NetworkInterfaceId'],
                                              current_targets[sid], targets[sid]), intersection)
            targets_to_delete = list(targets_to_delete) + changed
            targets_to_create = list(targets_to_create) + changed

            if targets_to_delete:
                for sid in targets_to_delete:
                    self.connection.delete_mount_target(
                        MountTargetId=current_targets[sid]['MountTargetId']
                    )
                wait_for(
                    lambda: len(self.get_mount_targets_in_state(fs_id, incomplete_states)),
                    0
                )
                result = True

            if targets_to_create:
                for sid in targets_to_create:
                    self.connection.create_mount_target(
                        FileSystemId=fs_id,
                        **targets[sid]
                    )
                wait_for(
                    lambda: len(self.get_mount_targets_in_state(fs_id, incomplete_states)),
                    0,
                    self.wait_timeout
                )
                result = True

            security_groups_to_update = filter(
                lambda sid: 'SecurityGroups' in targets[sid] and
                            current_targets[sid]['SecurityGroups'] != targets[sid]['SecurityGroups'],
                intersection
            )

            if security_groups_to_update:
                for sid in security_groups_to_update:
                    self.connection.modify_mount_target_security_groups(
                        MountTargetId=current_targets[sid]['MountTargetId'],
                        SecurityGroups=targets[sid]['SecurityGroups']
                    )
                result = True

        return result

    def delete_file_system(self, name, file_system_id=None):
        """
         Removes EFS instance by id/name
        """
        result = False
        state = self.get_file_system_state(name, file_system_id)
        if state in [self.STATE_CREATING, self.STATE_AVAILABLE]:
            wait_for(
                lambda: self.get_file_system_state(name),
                self.STATE_AVAILABLE
            )
            if not file_system_id:
                file_system_id = self.get_file_system_id(name)
            self.delete_mount_targets(file_system_id)
            self.connection.delete_file_system(FileSystemId=file_system_id)
            result = True

        if self.wait:
            wait_for(
                lambda: self.get_file_system_state(name),
                self.STATE_DELETED,
                self.wait_timeout
            )

        return result

    def delete_mount_targets(self, file_system_id):
        """
         Removes mount targets by EFS id
        """
        wait_for(
            lambda: len(self.get_mount_targets_in_state(file_system_id, self.STATE_CREATING)),
            0
        )

        targets = self.get_mount_targets_in_state(file_system_id, self.STATE_AVAILABLE)
        for target in targets:
            self.connection.delete_mount_target(MountTargetId=target['MountTargetId'])

        wait_for(
            lambda: len(self.get_mount_targets_in_state(file_system_id, self.STATE_DELETING)),
            0
        )

        return len(targets) > 0


def iterate_all(attr, map_method, **kwargs):
    """
     Method creates iterator from boto result set
    """
    args = dict((key, value) for (key, value) in kwargs.items() if value is not None)
    wait = 1
    while True:
        try:
            data = map_method(**args)
            for elm in data[attr]:
                yield elm
            if 'NextMarker' in data:
                args['Marker'] = data['Nextmarker']
                continue
            break
        except ClientError as e:
            if e.response['Error']['Code'] == "ThrottlingException" and wait < 600:
                sleep(wait)
                wait = wait * 2
                continue

def targets_equal(keys, a, b):
    """
     Method compare two mount targets by specified attributes
    """
    for key in keys:
        if key in b and a[key] != b[key]:
            return False

    return True


def dict_diff(dict1, dict2, by_key=False):
    """
     Helper method to calculate difference of two dictionaries
    """
    keys1 = set(dict1.keys() if by_key else dict1.items())
    keys2 = set(dict2.keys() if by_key else dict2.items())

    intersection = keys1 & keys2

    return keys2 ^ intersection, intersection, keys1 ^ intersection


def first_or_default(items, default=None):
    """
     Helper method to fetch first element of list (if exists)
    """
    for item in items:
        return item
    return default


def wait_for(callback, value, timeout=EFSConnection.DEFAULT_WAIT_TIMEOUT_SECONDS):
    """
     Helper method to wait for desired value returned by callback method
    """
    wait_start = timestamp()
    while True:
        if callback() != value:
            if timeout != 0 and (timestamp() - wait_start > timeout):
                raise RuntimeError('Wait timeout exceeded (' + str(timeout) + ' sec)')
            else:
                sleep(5)
            continue
        break


def main():
    """
     Module action handler
    """
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=False, type='str', choices=["present", "absent"], default="present"),
        id=dict(required=False, type='str', default=None),
        name=dict(required=False, type='str', default=None),
        tags=dict(required=False, type="dict", default={}),
        targets=dict(required=False, type="list", default=[]),
        performance_mode=dict(required=False, type='str', choices=["general_purpose", "max_io"], default="general_purpose"),
        wait=dict(required=False, type="bool", default=False),
        wait_timeout=dict(required=False, type="int", default=0)
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, _, aws_connect_params = get_aws_connection_info(module, boto3=True)
    connection = EFSConnection(module, region, **aws_connect_params)

    name = module.params.get('name')
    fs_id = module.params.get('id')
    tags = module.params.get('tags')
    target_translations = {
        'ip_address': 'IpAddress',
        'security_groups': 'SecurityGroups',
        'subnet_id': 'SubnetId'
    }
    targets = [dict((target_translations[key], value) for (key, value) in x.items()) for x in module.params.get('targets')]
    performance_mode_translations = {
        'general_purpose': 'generalPurpose',
        'max_io': 'maxIO'
    }
    performance_mode = performance_mode_translations[module.params.get('performance_mode')]
    changed = False

    state = str(module.params.get('state')).lower()

    if state == 'present':
        if not name:
            module.fail_json(msg='Name parameter is required for create')

        changed = connection.create_file_system(name, performance_mode)
        changed = connection.converge_file_system(name=name, tags=tags, targets=targets) or changed
        result = first_or_default(connection.get_file_systems(CreationToken=name))

    elif state == 'absent':
        if not name and not fs_id:
            module.fail_json(msg='Either name or id parameter is required for delete')

        changed = connection.delete_file_system(name, fs_id)
        result = None
    if result:
        result = camel_dict_to_snake_dict(result)
    module.exit_json(changed=changed, efs=result)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
