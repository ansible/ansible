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
        required: false
        default: None
    id:
        description:
            - ID of Amazon EFS.
        required: false
        default: None
    tags:
        description:
            - List of tags of Amazon EFS. Should be defined as dictionary
        required: false
        default: None
    targets:
        description:
            - "List of mounted targets. It should be a list of dictionaries, every dictionary should include next attributes:
                    - SubnetId - Mandatory. The ID of the subnet to add the mount target in.
                    - IpAddress - Optional. A valid IPv4 address within the address range of the specified subnet.
                    - SecurityGroups - Optional. List of security group IDs, of the form 'sg-xxxxxxxx'. These must be for the same VPC as subnet specified."
        required: false
        default: None
extends_documentation_fragment:
    - aws
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


from time import sleep
from collections import defaultdict

try:
    from botocore.exceptions import ClientError
    import boto3
    HAS_BOTO3 = True
except ImportError as e:
    HAS_BOTO3 = False

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
        except Exception as e:
            module.fail_json(msg="Failed to connect to AWS: %s" % str(e))

        self.region = region

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


def prefix_to_attr(attr_id):
    """
     Helper method to convert ID prefix to mount target attribute
    """
    attr_by_prefix = {
        'fsmt-': 'MountTargetId',
        'subnet-': 'SubnetId',
        'eni-': 'NetworkInterfaceId',
        'sg-': 'SecurityGroups'
    }
    prefix = first_or_default(filter(
        lambda pref: str(attr_id).startswith(pref),
        attr_by_prefix.keys()
    ))
    if prefix:
        return attr_by_prefix[prefix]
    return 'IpAddress'

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
    Helper method to determine if mount tager requested already exists
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
        id=dict(required=False, type='str', default=None),
        name=dict(required=False, type='str', default=None),
        tags=dict(required=False, type="dict", default={}),
        targets=dict(required=False, type="list", default=[])
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, _, aws_connect_params = get_aws_connection_info(module, boto3=True)
    connection = EFSConnection(module, region, **aws_connect_params)

    name = module.params.get('name')
    fs_id = module.params.get('id')
    tags = module.params.get('tags')
    targets = module.params.get('targets')

    file_systems_info = connection.get_file_systems(FileSystemId=fs_id, CreationToken=name)

    if tags:
        file_systems_info = filter(lambda item: has_tags(item['Tags'], tags), file_systems_info)

    if targets:
        targets = [(item, prefix_to_attr(item)) for item in targets]
        file_systems_info = filter(lambda item:
                                   has_targets(item['MountTargets'], targets), file_systems_info)

    file_systems_info = [camel_dict_to_snake_dict(x) for x in file_systems_info]
    module.exit_json(changed=False, ansible_facts={'efs': file_systems_info})

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
