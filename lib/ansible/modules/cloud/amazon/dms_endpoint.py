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
module: dms_endpoint
short_description: Manage endpoints for AWS Database Migration Service.
description:
    - Create, update, and destroy AWS Database Migration Service endpoints.
author: "Aaron Smith (@slapula)"
version_added: "2.6"
requirements: [ 'botocore', 'boto3' ]
options:
  name:
    description:
    - The database endpoint identifier.
    - Identifiers must begin with a letter; must contain only ASCII letters, digits, and hyphens;
      and must not end with a hyphen or contain two consecutive hyphens.
    required: true
  state:
    description:
    - Whether the replication subnet group should be exist or not.
    choices: ['present', 'absent']
    default: 'present'
  endpoint_type:
    description:
    - The type of endpoint.
    required: true
    choices: ['source', 'target']
  engine_name:
    description:
    - The type of engine for the endpoint.
    required: true
    choices: ['mysql', 'oracle', 'postgres', 'mariadb', 'aurora', 'aurora-postgresql',
        'redshift', 's3', 'db2', 'azuredb', 'sybase', 'dynamodb', 'mongodb', 'sqlserver']
  username:
    description:
    - The user name to be used to login to the endpoint database.
  password:
    description:
    - The password to be used to login to the endpoint database.
  server_name:
    description:
    - The name of the server where the endpoint database resides.
  port:
    description:
    - The port used by the endpoint database.
  database_name:
    description:
    - The name of the endpoint database.
  connection_attributes:
    description:
    - Additional attributes associated with the connection.
  kms_key_id:
    description:
    - The KMS key identifier that will be used to encrypt the connection parameters.
  tags:
    description:
    - Tags to be added to the endpoint.
  certificate_arn:
    description:
    - The Amazon Resource Name (ARN) for the certificate.
  ssl_mode:
    description:
    - The SSL mode to use for the SSL connection.
    choices: ['none', 'require', 'verify-ca', 'verify-null']
    default: 'none'
  service_access_role:
    description:
    - The Amazon Resource Name (ARN) for the service access role you want to use to create the endpoint.
  external_table:
    description:
    - The external table definition.
  dynamodb_settings:
    description:
    - Settings for the target Amazon DynamoDB endpoint.
    suboptions:
      service_access_role:
        description:
        - The Amazon Resource Name (ARN) used by the service access IAM role.
  s3_settings:
    description:
    - Settings for the target Amazon S3 endpoint.
    suboptions:
      service_access_role:
        description:
        - The Amazon Resource Name (ARN) used by the service access IAM role.
      external_table:
        description:
        - The external table definition.
      csv_row_delimiter:
        description:
        - The delimiter used to separate rows in the source files.
        default: "\\n"
      csv_delimiter:
        description:
        - The delimiter used to separate columns in the source files.
        default: ','
      bucket_folder:
        description:
        - An optional parameter to set a folder name in the S3 bucket.
      bucket_name:
        description:
        - The name of the S3 bucket.
      compression_type:
        description:
        - An optional parameter to use GZIP to compress the target files.
        choices: ['none', 'gzip']
        default: 'none'
  mongodb_settings:
    description:
    - Settings for the source MongoDB endpoint.
    suboptions:
      username:
        description:
        - The user name you use to access the MongoDB source endpoint.
      password:
        description:
        - The password for the user account you use to access the MongoDB source endpoint.
      server_name:
        description:
        - The name of the server on the MongoDB source endpoint.
      port:
        description:
        - The port value for the MongoDB source endpoint.
      database_name:
        description:
        - The database name on the MongoDB source endpoint.
      auth_type:
        description:
        - The authentication type you use to access the MongoDB source endpoint.
        choices: ['NO', 'PASSWORD']
        default: 'NO'
      auth_mechanism:
        description:
        - The authentication mechanism you use to access the MongoDB source endpoint.
        - This attribute is not used when authType=No.
        choices: ['DEFAULT', 'MONGODB_CR', 'SCRAM_SHA_1']
      nesting_level:
        description:
        - Specifies either document or table mode.
        - Specify NONE to use document mode. Specify ONE to use table mode.
        choices: ['NONE', 'ONE']
        default: 'NONE'
      extract_doc_id:
        description:
        - Specifies the document ID.
        - Use this attribute when NestingLevel is set to NONE.
        default: 'false'
      docs_to_investigate:
        description:
        - Indicates the number of documents to preview to determine the document organization.
        default: '1000'
      auth_source:
        description:
        - The MongoDB database name.
        - This attribute is not used when authType=NO.
        default: 'admin'
      kms_key_id:
        description:
        - The KMS key identifier that will be used to encrypt the connection parameters.
extends_documentation_fragment:
    - ec2
    - aws
'''


EXAMPLES = r'''
- name: Create source endpoint for DMS instances
  dms_endpoint:
    name: 'my-dms-source-endpoint'
    state: present
    endpoint_type: source
    engine_name: mysql
    username: 'dbadmin'
    password: "{{ my_db_password }}"
    server_name: "mysql-instance.123456789012.us-east-1.rds.amazonaws.com"
    port: 3306

- name: Create target endpoint for DMS instances
  dms_endpoint:
    name: 'pg-dms-target-endpoint'
    state: present
    endpoint_type: target
    engine_name: postgres
    username: 'admin'
    password: "{{ pg_db_password }}"
    server_name: "postgres-instance.123456789012.us-east-1.rds.amazonaws.com"
    port: 5432

- name: Destroy source endpoint for DMS instances
  dms_endpoint:
    name: 'my-dms-source-endpoint'
    state: absent
    endpoint_type: source
    engine_name: mysql
    username: 'dbadmin'
    password: "{{ my_db_password }}"
    server_name: "mysql-instance.123456789012.us-east-1.rds.amazonaws.com"
    port: 3306

- name: Destroy target endpoint for DMS instances
  dms_endpoint:
    name: 'pg-dms-target-endpoint'
    state: absent
    endpoint_type: target
    engine_name: postgres
    username: 'admin'
    password: "{{ pg_db_password }}"
    server_name: "postgres-instance.123456789012.us-east-1.rds.amazonaws.com"
    port: 5432
'''


RETURN = r'''
endpoint_arn:
    description: The ARN of the endpoint you just created or updated.
    returned: always
    type: string
'''

import os
import time

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule


def endpoint_exists(client, module, result):
    try:
        response = client.describe_endpoints()
        for i in response['Endpoints']:
            if i['EndpointIdentifier'] == module.params.get('name'):
                result['current_config'] = i
                result['endpoint_arn'] = i['EndpointArn']
                return True
    except (ClientError, IndexError):
        return False

    return False


def endpoint_update_waiter(client, module):
    try:
        endpoint_ready = False
        while endpoint_ready is False:
            time.sleep(5)
            status_check = client.describe_endpoints()
            for i in status_check['Endpoints']:
                if i['EndpointIdentifier'] == module.params.get('name'):
                    if i['Status'] == 'active':
                        endpoint_ready = True
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed while waiting on endpoint status")


def endpoint_delete_waiter(client, module):
    try:
        endpoint_deleted = False
        while endpoint_deleted is False:
            time.sleep(5)
            status_check = client.describe_endpoints()
            for i in status_check['Endpoints']:
                if i['EndpointIdentifier'] == module.params.get('name'):
                    endpoint_deleted = False
                else:
                    endpoint_deleted = True
            if not status_check['Endpoints']:
                endpoint_deleted = True
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed while waiting on endpoint status")


def create_endpoint(client, module, params, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.create_endpoint(**params)
        endpoint_update_waiter(client, module)
        result['endpoint_arn'] = response['EndpointArn']
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to create endpoint")

    return result


def update_endpoint(client, module, params, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        result['current_config']['EndpointType'] = result['current_config']['EndpointType'].lower()
        param_changed = []
        param_keys = list(params.keys())
        current_keys = list(result['current_config'].keys())
        common_keys = set(param_keys) - (set(param_keys) - set(current_keys))
        for key in common_keys:
            if (params[key] != result['current_config'][key]):
                param_changed.append(True)
            else:
                param_changed.append(False)
        params['EndpointArn'] = result['endpoint_arn']
        if any(param_changed):
            response = client.modify_endpoint(**params)
            endpoint_update_waiter(client, module)
            result['changed'] = True
            return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to update endpoint")

    return result


def delete_endpoint(client, module, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.delete_endpoint(
            EndpointArn=result['endpoint_arn']
        )
        endpoint_delete_waiter(client, module)
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to delete endpoint")

    return result


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'name': dict(type='str', required=True),
            'state': dict(type='str', choices=['present', 'absent'], default='present'),
            'endpoint_type': dict(type='str', choices=['source', 'target'], required=True),
            'engine_name': dict(
                type='str',
                choices=[
                    'mysql',
                    'oracle',
                    'postgres',
                    'mariadb',
                    'aurora',
                    'aurora-postgresql',
                    'redshift',
                    's3',
                    'db2',
                    'azuredb',
                    'sybase',
                    'dynamodb',
                    'mongodb',
                    'sqlserver'
                ],
                required=True
            ),
            'username': dict(type='str'),
            'password': dict(type='str'),
            'server_name': dict(type='str'),
            'port': dict(type='int'),
            'database_name': dict(type='str'),
            'connection_attributes': dict(type='str'),
            'kms_key_id': dict(type='str'),
            'tags': dict(type='list'),
            'certificate_arn': dict(type='str'),
            'ssl_mode': dict(type='str', choices=['none', 'require', 'verify-ca', 'verify-null'], default='none'),
            'service_access_role': dict(type='str'),
            'external_table': dict(type='str'),
            'dynamodb_settings': dict(type='dict'),
            's3_settings': dict(type='dict'),
            'mongodb_settings': dict(type='dict'),
        },
        supports_check_mode=True,
    )

    result = {
        'changed': False
    }

    params = {}
    params['EndpointIdentifier'] = module.params.get('name')
    params['EndpointType'] = module.params.get('endpoint_type')
    params['EngineName'] = module.params.get('engine_name')
    if module.params.get('username'):
        params['Username'] = module.params.get('username')
    if module.params.get('password'):
        params['Password'] = module.params.get('password')
    if module.params.get('server_name'):
        params['ServerName'] = module.params.get('server_name')
    if module.params.get('port'):
        params['Port'] = module.params.get('port')
    if module.params.get('database_name'):
        params['DatabaseName'] = module.params.get('database_name')
    if module.params.get('configuration_attributes'):
        params['ExtraConnectionAttributes'] = module.params.get('configuration_attributes')
    if module.params.get('kms_key_id'):
        params['KmsKeyId'] = module.params.get('kms_key_id')
    if module.params.get('tags'):
        params['Tags'] = module.params.get('tags')
    if module.params.get('certificate_arn'):
        params['CertificateArn'] = module.params.get('certificate_arn')
    if module.params.get('ssl_mode'):
        params['SslMode'] = module.params.get('ssl_mode')
    if module.params.get('service_access_role'):
        params['ServiceAccessRoleArn'] = module.params.get('server_access_role')
    if module.params.get('external_table'):
        params['ExternalTableDefinition'] = module.params.get('external_table')
    if module.params.get('dynamodb_settings'):
        params['DynamoDbSettings'] = {}
        if module.params.get('dynamodb_settings').get('service_access_role'):
            params['DynamoDbSettings'].update({
                'ServiceAccessRoleArn': module.params.get('dynamodb_settings').get('service_access_role')
            })
    if module.params.get('s3_settings'):
        params['S3Settings'] = {}
        if module.params.get('s3_settings').get('service_access_role'):
            params['S3Settings'].update({
                'ServiceAccessRoleArn': module.params.get('s3_settings').get('service_access_role')
            })
        if module.params.get('s3_settings').get('external_table'):
            params['S3Settings'].update({
                'ExternalTableDefinition': module.params.get('s3_settings').get('external_table')
            })
        if module.params.get('s3_settings').get('csv_row_delimiter'):
            params['S3Settings'].update({
                'CsvRowDelimiter': module.params.get('s3_settings').get('csv_row_delimiter')
            })
        if module.params.get('s3_settings').get('csv_delimiter'):
            params['S3Settings'].update({
                'CsvDelimiter': module.params.get('s3_settings').get('csv_delimiter')
            })
        if module.params.get('s3_settings').get('bucket_folder'):
            params['S3Settings'].update({
                'BucketFolder': module.params.get('s3_settings').get('bucket_folder')
            })
        if module.params.get('s3_settings').get('bucket_name'):
            params['S3Settings'].update({
                'BucketName': module.params.get('s3_settings').get('bucket_name')
            })
        if module.params.get('s3_settings').get('compression_type'):
            params['S3Settings'].update({
                'CompressionType': module.params.get('s3_settings').get('compression_type')
            })
    if module.params.get('mongodb_settings'):
        params['MongoDbSettings'] = {}
        if module.params.get('mongodb_settings').get('username'):
            params['MongoDbSettings'].update({
                'Username': module.params.get('mongodb_settings').get('username')
            })
        if module.params.get('mongodb_settings').get('password'):
            params['MongoDbSettings'].update({
                'Password': module.params.get('mongodb_settings').get('password')
            })
        if module.params.get('mongodb_settings').get('server_name'):
            params['MongoDbSettings'].update({
                'ServerName': module.params.get('mongodb_settings').get('server_name')
            })
        if module.params.get('mongodb_settings').get('port'):
            params['MongoDbSettings'].update({
                'Port': module.params.get('mongodb_settings').get('port')
            })
        if module.params.get('mongodb_settings').get('database_name'):
            params['MongoDbSettings'].update({
                'DatabaseName': module.params.get('mongodb_settings').get('database_name')
            })
        if module.params.get('mongodb_settings').get('auth_type'):
            params['MongoDbSettings'].update({
                'AuthType': module.params.get('mongodb_settings').get('auth_type')
            })
        if module.params.get('mongodb_settings').get('auth_mechanism'):
            params['MongoDbSettings'].update({
                'AuthMechanism': module.params.get('mongodb_settings').get('auth_mechanism')
            })
        if module.params.get('mongodb_settings').get('nesting_level'):
            params['MongoDbSettings'].update({
                'NestingLevel': module.params.get('mongodb_settings').get('nesting_level')
            })
        if module.params.get('mongodb_settings').get('extract_doc_id'):
            params['MongoDbSettings'].update({
                'ExtractDocId': module.params.get('mongodb_settings').get('extract_doc_id')
            })
        if module.params.get('mongodb_settings').get('docs_to_investigate'):
            params['MongoDbSettings'].update({
                'DocsToInvestigate': module.params.get('mongodb_settings').get('docs_to_investigate')
            })
        if module.params.get('mongodb_settings').get('auth_source'):
            params['MongoDbSettings'].update({
                'AuthSource': module.params.get('mongodb_settings').get('auth_source')
            })
        if module.params.get('mongodb_settings').get('kms_key_id'):
            params['MongoDbSettings'].update({
                'KmsKeyId': module.params.get('mongodb_settings').get('kms_key_id')
            })

    client = module.client('dms')

    endpoint_status = endpoint_exists(client, module, result)

    desired_state = module.params.get('state')

    if desired_state == 'present':
        if not endpoint_status:
            create_endpoint(client, module, params, result)
        if endpoint_status:
            update_endpoint(client, module, params, result)

    if desired_state == 'absent':
        if endpoint_status:
            delete_endpoint(client, module, result)

    module.exit_json(changed=result['changed'], output=result)


if __name__ == '__main__':
    main()
