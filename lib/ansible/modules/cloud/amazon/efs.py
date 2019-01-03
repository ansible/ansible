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
    encrypt:
        description:
            - A boolean value that, if true, creates an encrypted file system. This can not be modfied after the file
              system is created.
        type: bool
        default: 'no'
        version_added: 2.5
    kms_key_id:
        description:
            - The id of the AWS KMS CMK that will be used to protect the encrypted file system. This parameter is only
              required if you want to use a non-default CMK. If this parameter is not specified, the default CMK for
              Amazon EFS is used. The key id can be Key ID, Key ID ARN, Key Alias or Key Alias ARN.
        version_added: 2.5
    purge_tags:
        description:
            - If yes, existing tags will be purged from the resource to match exactly what is defined by I(tags) parameter. If the I(tags) parameter
              is not set then tags will not be modified.
        type: bool
        default: 'yes'
        version_added: 2.5
    state:
        description:
            - Allows to create, search and destroy Amazon EFS file system
        default: 'present'
        choices: ['present', 'absent']
    name:
        description:
            - Creation Token of Amazon EFS file system. Required for create and update. Either name or ID required for delete.
    id:
        description:
            - ID of Amazon EFS. Either name or ID required for delete.
    performance_mode:
        description:
            - File system's performance mode to use. Only takes effect during creation.
        default: 'general_purpose'
        choices: ['general_purpose', 'max_io']
    tags:
        description:
            - "List of tags of Amazon EFS. Should be defined as dictionary
              In case of 'present' state with list of tags and existing EFS (matched by 'name'), tags of EFS will be replaced with provided data."
    targets:
        description:
            - "List of mounted targets. It should be a list of dictionaries, every dictionary should include next attributes:
                   - subnet_id - Mandatory. The ID of the subnet to add the mount target in.
                   - ip_address - Optional. A valid IPv4 address within the address range of the specified subnet.
                   - security_groups - Optional. List of security group IDs, of the form 'sg-xxxxxxxx'. These must be for the same VPC as subnet specified
               This data may be modified for existing EFS using state 'present' and new list of mount targets."
    throughput_mode:
        description:
            - The throughput_mode for the file system to be created.
            - Requires botocore >= 1.10.57
        choices: ['bursting', 'provisioned']
        version_added: 2.8
    provisioned_throughput_in_mibps:
        description:
            - If the throughput_mode is provisioned, select the amount of throughput to provisioned in Mibps.
            - Requires botocore >= 1.10.57
        type: float
        version_added: 2.8
    wait:
        description:
            - "In case of 'present' state should wait for EFS 'available' life cycle state (of course, if current state not 'deleting' or 'deleted')
               In case of 'absent' state should wait for EFS 'deleted' life cycle state"
        type: bool
        default: 'no'
    wait_timeout:
        description:
            - How long the module should wait (in seconds) for desired state before returning. Zero means wait as long as necessary.
        default: 0

extends_documentation_fragment:
    - aws
    - ec2
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
    returned: always
    type: str
    sample: "2015-11-16 07:30:57-05:00"
creation_token:
    description: EFS creation token
    returned: always
    type: str
    sample: "console-88609e04-9a0e-4a2e-912c-feaa99509961"
file_system_id:
    description: ID of the file system
    returned: always
    type: str
    sample: "fs-xxxxxxxx"
life_cycle_state:
    description: state of the EFS file system
    returned: always
    type: str
    sample: "creating, available, deleting, deleted"
mount_point:
    description: url of file system with leading dot from the time when AWS EFS required to add a region suffix to the address
    returned: always
    type: str
    sample: ".fs-xxxxxxxx.efs.us-west-2.amazonaws.com:/"
filesystem_address:
    description: url of file system valid for use with mount
    returned: always
    type: str
    sample: "fs-xxxxxxxx.efs.us-west-2.amazonaws.com:/"
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
    sample: "my-efs"
number_of_mount_targets:
    description: the number of targets mounted
    returned: always
    type: int
    sample: 3
owner_id:
    description: AWS account ID of EFS owner
    returned: always
    type: str
    sample: "XXXXXXXXXXXX"
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

from time import sleep
from time import time as timestamp
import traceback

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError as e:
    pass  # Taken care of by ec2.HAS_BOTO3

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (HAS_BOTO3, boto3_conn, camel_dict_to_snake_dict,
                                      ec2_argument_spec, get_aws_connection_info, ansible_dict_to_boto3_tag_list,
                                      compare_aws_tags, boto3_tag_list_to_ansible_dict)


def _index_by_key(key, items):
    return dict((item[key], item) for item in items)


class EFSConnection(object):

    DEFAULT_WAIT_TIMEOUT_SECONDS = 0

    STATE_CREATING = 'creating'
    STATE_AVAILABLE = 'available'
    STATE_DELETING = 'deleting'
    STATE_DELETED = 'deleted'

    def __init__(self, module, region, **aws_connect_params):
        self.connection = boto3_conn(module, conn_type='client',
                                     resource='efs', region=region,
                                     **aws_connect_params)

        self.module = module
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
            item['Name'] = item['CreationToken']
            item['CreationTime'] = str(item['CreationTime'])
            """
            In the time when MountPoint was introduced there was a need to add a suffix of network path before one could use it
            AWS updated it and now there is no need to add a suffix. MountPoint is left for back-compatibility purpose
            And new FilesystemAddress variable is introduced for direct use with other modules (e.g. mount)
            AWS documentation is available here:
            https://docs.aws.amazon.com/efs/latest/ug/gs-step-three-connect-to-ec2-instance.html
            """
            item['MountPoint'] = '.%s.efs.%s.amazonaws.com:/' % (item['FileSystemId'], self.region)
            item['FilesystemAddress'] = '%s.efs.%s.amazonaws.com:/' % (item['FileSystemId'], self.region)
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
        tags = self.connection.describe_tags(**kwargs)['Tags']
        return tags

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

    def supports_provisioned_mode(self):
        """
        Ensure boto3 includes provisioned throughput mode feature
        """
        return hasattr(self.connection, 'update_file_system')

    def get_throughput_mode(self, **kwargs):
        """
        Returns throughput mode for selected EFS instance
        """
        info = first_or_default(iterate_all(
            'FileSystems',
            self.connection.describe_file_systems,
            **kwargs
        ))

        return info and info['ThroughputMode'] or None

    def get_provisioned_throughput_in_mibps(self, **kwargs):
        """
        Returns throughput mode for selected EFS instance
        """
        info = first_or_default(iterate_all(
            'FileSystems',
            self.connection.describe_file_systems,
            **kwargs
        ))
        return info.get('ProvisionedThroughputInMibps', None)

    def create_file_system(self, name, performance_mode, encrypt, kms_key_id, throughput_mode, provisioned_throughput_in_mibps):
        """
         Creates new filesystem with selected name
        """
        changed = False
        state = self.get_file_system_state(name)
        params = {}
        params['CreationToken'] = name
        params['PerformanceMode'] = performance_mode
        if encrypt:
            params['Encrypted'] = encrypt
        if kms_key_id is not None:
            params['KmsKeyId'] = kms_key_id
        if throughput_mode:
            if self.supports_provisioned_mode():
                params['ThroughputMode'] = throughput_mode
            else:
                self.module.fail_json(msg="throughput_mode parameter requires botocore >= 1.10.57")
        if provisioned_throughput_in_mibps:
            if self.supports_provisioned_mode():
                params['ProvisionedThroughputInMibps'] = provisioned_throughput_in_mibps
            else:
                self.module.fail_json(msg="provisioned_throughput_in_mibps parameter requires botocore >= 1.10.57")

        if state in [self.STATE_DELETING, self.STATE_DELETED]:
            wait_for(
                lambda: self.get_file_system_state(name),
                self.STATE_DELETED
            )
            try:
                self.connection.create_file_system(**params)
                changed = True
            except ClientError as e:
                self.module.fail_json(msg="Unable to create file system: {0}".format(to_native(e)),
                                      exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
            except BotoCoreError as e:
                self.module.fail_json(msg="Unable to create file system: {0}".format(to_native(e)),
                                      exception=traceback.format_exc())

        # we always wait for the state to be available when creating.
        # if we try to take any actions on the file system before it's available
        # we'll throw errors
        wait_for(
            lambda: self.get_file_system_state(name),
            self.STATE_AVAILABLE,
            self.wait_timeout
        )

        return changed

    def update_file_system(self, name, throughput_mode, provisioned_throughput_in_mibps):
        """
        Update filesystem with new throughput settings
        """
        changed = False
        state = self.get_file_system_state(name)
        if state in [self.STATE_AVAILABLE, self.STATE_CREATING]:
            fs_id = self.get_file_system_id(name)
            current_mode = self.get_throughput_mode(FileSystemId=fs_id)
            current_throughput = self.get_provisioned_throughput_in_mibps(FileSystemId=fs_id)
            params = dict()
            if throughput_mode and throughput_mode != current_mode:
                params['ThroughputMode'] = throughput_mode
            if provisioned_throughput_in_mibps and provisioned_throughput_in_mibps != current_throughput:
                params['ProvisionedThroughputInMibps'] = provisioned_throughput_in_mibps
            if len(params) > 0:
                wait_for(
                    lambda: self.get_file_system_state(name),
                    self.STATE_AVAILABLE,
                    self.wait_timeout
                )
                try:
                    self.connection.update_file_system(FileSystemId=fs_id, **params)
                    changed = True
                except ClientError as e:
                    self.module.fail_json(msg="Unable to update file system: {0}".format(to_native(e)),
                                          exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
                except BotoCoreError as e:
                    self.module.fail_json(msg="Unable to update file system: {0}".format(to_native(e)),
                                          exception=traceback.format_exc())
        return changed

    def converge_file_system(self, name, tags, purge_tags, targets, throughput_mode, provisioned_throughput_in_mibps):
        """
         Change attributes (mount targets and tags) of filesystem by name
        """
        result = False
        fs_id = self.get_file_system_id(name)

        if tags is not None:
            tags_need_modify, tags_to_delete = compare_aws_tags(boto3_tag_list_to_ansible_dict(self.get_tags(FileSystemId=fs_id)), tags, purge_tags)

            if tags_to_delete:
                try:
                    self.connection.delete_tags(
                        FileSystemId=fs_id,
                        TagKeys=tags_to_delete
                    )
                except ClientError as e:
                    self.module.fail_json(msg="Unable to delete tags: {0}".format(to_native(e)),
                                          exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
                except BotoCoreError as e:
                    self.module.fail_json(msg="Unable to delete tags: {0}".format(to_native(e)),
                                          exception=traceback.format_exc())

                result = True

            if tags_need_modify:
                try:
                    self.connection.create_tags(
                        FileSystemId=fs_id,
                        Tags=ansible_dict_to_boto3_tag_list(tags_need_modify)
                    )
                except ClientError as e:
                    self.module.fail_json(msg="Unable to create tags: {0}".format(to_native(e)),
                                          exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
                except BotoCoreError as e:
                    self.module.fail_json(msg="Unable to create tags: {0}".format(to_native(e)),
                                          exception=traceback.format_exc())

                result = True

        if targets is not None:
            incomplete_states = [self.STATE_CREATING, self.STATE_DELETING]
            wait_for(
                lambda: len(self.get_mount_targets_in_state(fs_id, incomplete_states)),
                0
            )
            current_targets = _index_by_key('SubnetId', self.get_mount_targets(FileSystemId=fs_id))
            targets = _index_by_key('SubnetId', targets)

            targets_to_create, intersection, targets_to_delete = dict_diff(current_targets,
                                                                           targets, True)

            # To modify mount target it should be deleted and created again
            changed = [sid for sid in intersection if not targets_equal(['SubnetId', 'IpAddress', 'NetworkInterfaceId'],
                                                                        current_targets[sid], targets[sid])]
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

            # If no security groups were passed into the module, then do not change it.
            security_groups_to_update = [sid for sid in intersection if
                                         'SecurityGroups' in targets[sid] and
                                         current_targets[sid]['SecurityGroups'] != targets[sid]['SecurityGroups']]

            if security_groups_to_update:
                for sid in security_groups_to_update:
                    self.connection.modify_mount_target_security_groups(
                        MountTargetId=current_targets[sid]['MountTargetId'],
                        SecurityGroups=targets[sid].get('SecurityGroups', None)
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
     Method creates iterator from result set
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
            else:
                raise


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
        encrypt=dict(required=False, type="bool", default=False),
        state=dict(required=False, type='str', choices=["present", "absent"], default="present"),
        kms_key_id=dict(required=False, type='str', default=None),
        purge_tags=dict(default=True, type='bool'),
        id=dict(required=False, type='str', default=None),
        name=dict(required=False, type='str', default=None),
        tags=dict(required=False, type="dict", default={}),
        targets=dict(required=False, type="list", default=[]),
        performance_mode=dict(required=False, type='str', choices=["general_purpose", "max_io"], default="general_purpose"),
        throughput_mode=dict(required=False, type='str', choices=["bursting", "provisioned"], default=None),
        provisioned_throughput_in_mibps=dict(required=False, type='float'),
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
    encrypt = module.params.get('encrypt')
    kms_key_id = module.params.get('kms_key_id')
    performance_mode = performance_mode_translations[module.params.get('performance_mode')]
    purge_tags = module.params.get('purge_tags')
    throughput_mode = module.params.get('throughput_mode')
    provisioned_throughput_in_mibps = module.params.get('provisioned_throughput_in_mibps')
    state = str(module.params.get('state')).lower()
    changed = False

    if state == 'present':
        if not name:
            module.fail_json(msg='Name parameter is required for create')

        changed = connection.create_file_system(name, performance_mode, encrypt, kms_key_id, throughput_mode, provisioned_throughput_in_mibps)
        if connection.supports_provisioned_mode():
            changed = connection.update_file_system(name, throughput_mode, provisioned_throughput_in_mibps) or changed
        changed = connection.converge_file_system(name=name, tags=tags, purge_tags=purge_tags, targets=targets,
                                                  throughput_mode=throughput_mode, provisioned_throughput_in_mibps=provisioned_throughput_in_mibps) or changed
        result = first_or_default(connection.get_file_systems(CreationToken=name))

    elif state == 'absent':
        if not name and not fs_id:
            module.fail_json(msg='Either name or id parameter is required for delete')

        changed = connection.delete_file_system(name, fs_id)
        result = None
    if result:
        result = camel_dict_to_snake_dict(result)
    module.exit_json(changed=changed, efs=result)


if __name__ == '__main__':
    main()
