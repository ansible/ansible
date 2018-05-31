#!/usr/bin/python

# Copyright: (c) 2018, Aaron Smith <ajsmith10381@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: storage_gateway_file_share
short_description: Manage NFS file shares on an AWS Storage Gateway instance
description:
    - Add, modify, or remove NFS file shares on an AWS Storage Gateway instance
version_added: "2.7"
requirements: [ 'botocore', 'boto3' ]
author:
    - "Aaron Smith (@slapula)"
options:
  gateway_arn:
    description:
    - The Amazon Resource Name (ARN) of the file gateway on which you want to create a file share.
    required: true
  state:
    description:
     - Whether the lexicon should be exist or not.
    required: true
    choices: ['present', 'absent']
  nfs_token:
    description:
    - A unique string value that you supply that is used by file gateway to ensure idempotent file share creation.
    required: true
  iam_role:
    description:
    - The ARN of the AWS Identity and Access Management (IAM) role that a file gateway assumes when it accesses the underlying storage.
    required: true
  location_arn:
    description:
    - The ARN of the backed storage used for storing file data.
    required: true
  nfs_defaults:
    description:
    - File share default values.
    suboptions:
      file_mode:
        description:
        - The Unix file mode in the form "nnnn".
      directory_mode:
        description:
        - The Unix directory mode in the form "nnnn".
      group_id:
        description:
        - The default group ID for the file share.
      owner_id:
        description:
        - The default owner ID for files in the file share.
  kms_encrypted:
    description:
    - True to use Amazon S3 server side encryption with your own AWS KMS key, or false to use a key managed by Amazon S3.
    type: bool
  kms_key:
    description:
    - The KMS key used for Amazon S3 server side encryption.
  default_storage_class:
    description:
    - The default storage class for objects put into an Amazon S3 bucket by file gateway.
    default: 'S3_STANDARD'
    choices: ['S3_STANDARD', 'S3_STANDARD_IA']
  object_acl:
    description:
    - Sets the access control list permission for objects in the Amazon S3 bucket that a file gateway puts objects into.
    default: 'private'
  client_list:
    description:
    - The list of clients that are allowed to access the file gateway. The list must contain either valid IP addresses or valid CIDR blocks.
  squash:
    description:
    - Maps a user to anonymous user.
    choices: ['RootSquash', 'NoSquash', 'AllSquash']
  read_only:
    description:
    - Sets the write status of a file share.
    type: bool
  guess_mime_type_enabled:
    description:
    - Enables guessing of the MIME type for uploaded objects based on file extensions.
    type: bool
    default: 'true'
  requester_pays:
    description:
    - Sets who pays the cost of the request and the data download from the Amazon S3 bucket.
    type: bool
    default: 'false'
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = r'''
  - name: Create NFS file share on a storage gateway instance
    storage_gateway_file_share:
      gateway_arn: 'arn:aws:storagegateway:us-east-1:123456789012:gateway/sgw-12A3456B'
      nfs_token: '5734980946'
      iam_role: 'arn:aws:iam::123456789012:role/StorageGatewatRole'
      location_arn: "arn:aws:s3:::storage-gateway-nfs-test-bucket"
'''

RETURN = r'''
file_share_arn:
    description: The ARN of the NFS file share you just created or updated.
    returned: always
    type: string
'''

try:
    import botocore
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict


def share_exists(client, module, params, result):
    try:
        file_share_list = client.list_file_shares()
        for i in file_share_list['FileShareInfoList']:
            file_share_deets = client.describe_nfs_file_shares(
                FileShareARNList=[i['FileShareARN']]
            )
            if file_share_deets['NFSFileShareInfoList'][0]['LocationARN'] == params['LocationARN']:
                result['file_share_arn'] = i['FileShareARN']
                return True
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError):
        return False

    return False


def create_share(client, module, params, result):
    try:
        response = client.create_nfs_file_share(**params)
        result['file_share_arn'] = response['FileShareARN']
        result['changed'] = True
        return result
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't create NFS file share")

    return result


def update_share(client, module, params, result):
    current_config = client.describe_nfs_file_shares(
        FileShareARNList=[result['file_share_arn']]
    )

    param_changed = []
    param_keys = list(params.keys())
    current_keys = list(current_config['NFSFileShareInfoList'][0].keys())
    common_keys = set(param_keys) - (set(param_keys) - set(current_keys))
    for key in common_keys:
        if (params[key] != current_config['NFSFileShareInfoList'][0][key]):
            param_changed.append(True)
        else:
            param_changed.append(False)

    params['FileShareARN'] = result['file_share_arn']
    del params['ClientToken']
    del params['GatewayARN']
    del params['LocationARN']
    del params['Role']

    if any(param_changed):
        try:
            response = client.update_nfs_file_share(**params)
            result['file_share_arn'] = response['FileShareARN']
            result['changed'] = True
            return result
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't update NFS file share")

    return result


def delete_share(client, module, result):
    try:
        response = client.delete_file_share(
            FileShareARN=result['file_share_arn']
        )
        result['changed'] = True
        return result
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't delete NFS file share")

    return result


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'gateway_arn': dict(type='str', required=True),
            'state': dict(type='str', choices=['present', 'absent'], required=True),
            'nfs_token': dict(type='str', required=True),
            'iam_role': dict(type='str', required=True),
            'location_arn': dict(type='str', required=True),
            'nfs_defaults': dict(type='dict'),
            'kms_encrypted': dict(type='bool', default=False),
            'kms_key': dict(type='str'),
            'default_storage_class': dict(type='str', default='S3_STANDARD', choices=['S3_STANDARD', 'S3_STANDARD_IA']),
            'object_acl': dict(type='str', default='private'),
            'client_list': dict(type='list'),
            'squash': dict(type='str', choices=['RootSquash', 'NoSquash', 'AllSquash']),
            'read_only': dict(type='bool', default=False),
            'guess_mime_type_enabled': dict(type='bool', default=True),
            'requester_pays': dict(type='bool', default=False),
        },
        supports_check_mode=False,
    )

    result = {
        'changed': False,
        'file_share_arn': ''
    }

    desired_state = module.params.get('state')

    params = {}
    params['GatewayARN'] = module.params.get('gateway_arn')
    params['ClientToken'] = module.params.get('nfs_token')
    params['Role'] = module.params.get('iam_role')
    params['LocationARN'] = module.params.get('location_arn')
    if module.params.get('nfs_defaults'):
        params['NFSFileShareDefaults'] = {}
        if module.params.get('nfs_defaults').get('file_mode'):
            params['NFSFileShareDefaults'].update({
                'FileMode': module.params.get('nfs_defaults').get('file_mode')
            })
        if module.params.get('nfs_defaults').get('directory_mode'):
            params['NFSFileShareDefaults'].update({
                'DirectoryMode': module.params.get('nfs_defaults').get('directory_mode')
            })
        if module.params.get('nfs_defaults').get('group_id'):
            params['NFSFileShareDefaults'].update({
                'GroupId': module.params.get('nfs_defaults').get('group_id')
            })
        if module.params.get('nfs_defaults').get('owner_id'):
            params['NFSFileShareDefaults'].update({
                'OwnerId': module.params.get('nfs_defaults').get('owner_id')
            })
    if module.params.get('kms_encrypted'):
        params['KMSEncrypted'] = module.params.get('kms_encrypted')
    if module.params.get('kms_key'):
        params['KMSKey'] = module.params.get('kms_key')
    if module.params.get('default_storage_class'):
        params['DefaultStorageClass'] = module.params.get('default_storage_class')
    if module.params.get('object_acl'):
        params['ObjectACL'] = module.params.get('object_acl')
    if module.params.get('client_list'):
        params['ClientList'] = module.params.get('client_list')
    if module.params.get('squash'):
        params['Squash'] = module.params.get('squash')
    if module.params.get('read_only'):
        params['ReadOnly'] = module.params.get('read_only')
    if module.params.get('guess_mime_type_enabled'):
        params['GuessMIMETypeEnabled'] = module.params.get('guess_mime_type_enabled')
    if module.params.get('requester_pays'):
        params['RequesterPays'] = module.params.get('requester_pays')

    client = module.client('storagegateway')

    share_status = share_exists(client, module, params, result)

    if desired_state == 'present':
        if not share_status:
            create_share(client, module, params, result)
        if share_status:
            update_share(client, module, params, result)

    if desired_state == 'absent':
        if share_status:
            delete_share(client, module, result)

    module.exit_json(changed=result['changed'], file_share_arn=result['file_share_arn'])


if __name__ == '__main__':
    main()
