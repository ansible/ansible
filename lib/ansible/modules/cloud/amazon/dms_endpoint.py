#!/usr/bin/python
# -*- coding: utf-8 -*
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
import traceback
#from ansible.module_utils.aws.core import AnsibleAWSModule, \
#    is_boto3_error_code, get_boto3_client_method_parameters

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
---
module: dms_endpoint
short_description: creates or destroys a data migration services endpoint
description:
    - creates or destroys a data migration services endpoint
version_added: "2.8"
options:
author:
   - Rui Moreira (@ruimoreira)
extends_documentation_fragment: aws
"""

EXAMPLES = '''
'''

RETURN = '''
'''


from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code, get_boto3_client_method_parameters
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, HAS_BOTO3, camel_dict_to_snake_dict, get_aws_connection_info, AWSRetry


try:
    from botocore.exceptions import ClientError, BotoCoreError, WaiterError
except ImportError:
    pass  # caught by AnsibleAWSModule

backoff_params = dict(tries=10, delay=3, backoff=1.5)


@AWSRetry.backoff(**backoff_params)
def describe_endpoints(connection, endpoint_identifier):
    """ checks if the endpoint exists """
    endpoint_filter = dict(Name='endpoint-id', Values=endpoint_identifier)
    return connection.describe_endpoints(**endpoint_filter)


@AWSRetry.backoff(**backoff_params)
def create_endpoint(connection, **params):
    """ creates the endpoint"""
    return connection.create_endpoint(**params)

def create_dms_endpoint(connection):
    """
    Function to create the dms endpoint
    :param connection: boto3 aws connection
    :return: information about the dms endpoint object
    """
    endpoint_identifier = module.params.get('endpointidentifier')
    endpoint_type = module.params.get('endpointtype')
    engine_name = module.params.get('enginename')
    username = module.params.get('username')
    password = module.params.get('password')
    servername = module.params.get('servername')
    port = module.params.get('port')

    try:
        endpoint_exists = describe_endpoints(connection, endpoint_identifier)
    except (ClientError, BotoCoreError) as e:
        module.fail_json(msg="Failed to describe DMS endpoint.",
                         exception=traceback.format_exc())
    endpoint = dict(
        EndpointIdentifier=endpoint_identifier,
        EndpointType=endpoint_type,
        EngineName=engine_name,
        Username=username,
        Password=password,
        ServerName=servername,
        Port=port,
    )

def main():
    """ main function, instanciates the ansible module and performs the initial logic"""
    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        endpointidentifier=dict(required=True),
        endpointtype=dict(choices=['source', 'target'], required=True),
        enginename=dict(choices=['mysql', 'oracle', 'postgres', 'mariadb', 'aurora', 'redshift', 's3', 'db2', 'azuredb', 'sybase', 'dynamodb', 'mongodb', 'sqlserver'], required=True),
        username=dict(),
        password=dict(),
        servername=dict(),
        port=dict(type='int'),
        databasename=dict(),
        extraconnectionattributes=dict(),
        kmskeyid=dict(),
        tags=dict(type='dict'),
        certificatearn=dict(),
        sslmode=dict(choices=['none', 'require', 'verify-ca', 'verify-full'], default='none'),
        serviceaccessrolearn=dict(),
        externaltabledefinition=dict(),
        dynamodbsettings=dict(type='dict'),
        s3settings=dict(type='dict'),
        dmstransfersettings=dict(type='dict'),
        mongodbsettings=dict(type='dict'),
        kinesissettings=dict(type='dict'),
        elasticsearchsettings=dict(type='dict')
    )
    global module
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    state = module.params.get('state')
    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    connection = boto3_conn(module,
                            conn_type='client',
                            resource='dms',
                            region=region,
                            endpoint=ec2_url,
                            **aws_connect_params)

    if state == 'present':
        create_dms_endpoint(connection)

    if __name__ == '__main__':
        main()

