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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: dms_endpoint
short_description: creates or destroys a data migration services endpoint
description:
    - creates or destroys a data migration services endpoint,
      that can be used to replicate data.
version_added: "2.9"
options:
    state:
      description:
        - State of the endpoint
      default: present
      choices: ['present', 'absent']
    endpointidentifier:
      description:
        - An identifier name for the endpoint
    endpointtype:
      description:
        - Type of endpoint we want to manage
      choices: ['source', 'target']
    enginename:
      description:
        - Database engine that we want to use, please refer to
          the AWS DMS for more information on the supported
          engines and their limitation
      choices: ['mysql', 'oracle', 'postgres', 'mariadb', 'aurora',
                         'redshift', 's3', 'db2', 'azuredb', 'sybase',
                         'dynamodb', 'mongodb', 'sqlserver']
    username:
      description:
        - Username our endpoint will use to connect to the database
    password:
      description:
        - Password used to connect to the database
          this attribute can only be written
          the AWS API does not return this parameter
    servername:
      description:
        - Servername that the endpoint will connect to
    port:
      description:
        - TCP port for access to the database
    databasename:
      description:
        - Name for the database on the origin or target side
    extraconnectionattributes:
      description:
        - Extra attributes for the database connection, the AWS documentation
          states " For more information about extra connection attributes,
          see the documentation section for your data store."
    kmskeyid:
      description:
        - Encryption key to use to encrypt replication storage and
          connection information
    tags:
      description:
        - A list of tags to add to the endpoint
    certificatearn:
       description:
         -  Amazon Resource Name (ARN) for the certificate
    sslmode:
       description:
         - Mode used for the ssl connection
       default: none
       choices: ['none', 'require', 'verify-ca', 'verify-full']
    serviceaccessrolearn:
       description:
         -  Amazon Resource Name (ARN) for the service access role that you
            want to use to create the endpoint.
    externaltabledefinition:
       description:
         - The external table definition
    dynamodbsettings:
       description:
         - Settings in JSON format for the target Amazon DynamoDB endpoint
           if source or target is dynamodb
    s3settings:
       description:
         - S3 buckets settings for the target Amazon S3 endpoint.
    dmstransfersettings:
       description:
         - The settings in JSON format for the DMS transfer type of
           source endpoint
    mongodbsettings:
       description:
         - Settings in JSON format for the source MongoDB endpoint
    kinesissettings:
       description:
         - Settings in JSON format for the target Amazon Kinesis
           Data Streams endpoint
    elasticsearchsettings:
       description:
         - Settings in JSON format for the target Elasticsearch endpoint
    wait:
       description:
         - should wait for the object to be deleted when state = absent
       type: bool
       default: 'false'
    timeout:
       description:
         - time in seconds we should wait for when deleting a resource
       type: int
    retries:
       description:
          - number of times we should retry when deleting a resource
       type: int
    region:
       description:
          - aws region, should be read from the running aws config
    ec2_region:
       description:
          - alias for region
    aws_region:
       description:
          - alias for region
author:
   - "Rui Moreira (@ruimoreira)"
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Note: These examples do not set authentication details
# Endpoint Creation
- dms_endpoint:
    state: absent
    endpointidentifier: 'testsource'
    endpointtype: source
    enginename: aurora
    username: testing1
    password: testint1234
    servername: testing.domain.com
    port: 3306
    databasename: 'testdb'
    sslmode: none
    wait: false
'''

RETURN = ''' # '''
__metaclass__ = type
import traceback
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, HAS_BOTO3, \
    camel_dict_to_snake_dict, get_aws_connection_info, AWSRetry
try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

backoff_params = dict(tries=5, delay=1, backoff=1.5)


@AWSRetry.backoff(**backoff_params)
def describe_endpoints(connection, endpoint_identifier):
    """ checks if the endpoint exists """
    try:
        endpoint_filter = dict(Name='endpoint-id',
                               Values=[endpoint_identifier])
        return connection.describe_endpoints(Filters=[endpoint_filter])
    except botocore.exceptions.ClientError:
        return {'Endpoints': []}


@AWSRetry.backoff(**backoff_params)
def dms_delete_endpoint(client, **params):
    """deletes the DMS endpoint based on the EndpointArn"""
    if module.params.get('wait'):
        return delete_dms_endpoint(client)
    else:
        return client.delete_endpoint(**params)


@AWSRetry.backoff(**backoff_params)
def dms_create_endpoint(client, **params):
    """ creates the DMS endpoint"""
    return client.create_endpoint(**params)


@AWSRetry.backoff(**backoff_params)
def dms_modify_endpoint(client, **params):
    """ updates the endpoint"""
    return client.modify_endpoint(**params)


@AWSRetry.backoff(**backoff_params)
def get_endpoint_deleted_waiter(client):
    return client.get_waiter('endpoint_deleted')


def endpoint_exists(endpoint):
    """ Returns boolean based on the existence of the endpoint
    :param endpoint: dict containing the described endpoint
    :return: bool
    """
    return bool(len(endpoint['Endpoints']))


def get_dms_client(aws_connect_params, client_region, ec2_url):
    client_params = dict(
        module=module,
        conn_type='client',
        resource='dms',
        region=client_region,
        endpoint=ec2_url,
        **aws_connect_params
    )
    return boto3_conn(**client_params)


def delete_dms_endpoint(connection):
    try:
        endpoint = describe_endpoints(connection,
                                      module.params.get('endpointidentifier'))
        endpoint_arn = endpoint['Endpoints'][0].get('EndpointArn')
        delete_arn = dict(
            EndpointArn=endpoint_arn
        )
        if module.params.get('wait'):

            delete_output = connection.delete_endpoint(**delete_arn)
            delete_waiter = get_endpoint_deleted_waiter(connection)
            delete_waiter.wait(
                Filters=[{
                    'Name': 'endpoint-arn',
                    'Values': [endpoint_arn]

                }],
                WaiterConfig={
                    'Delay': module.params.get('timeout'),
                    'MaxAttempts': module.params.get('retries')
                }
            )
            return delete_output
        else:
            return connection.delete_endpoint(**delete_arn)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to delete the  DMS endpoint.",
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Failed to delete the DMS endpoint.",
                         exception=traceback.format_exc())


def create_module_params():
    """
    Reads the module parameters and returns a dict
    :return: dict
    """
    endpoint_parameters = dict(
        EndpointIdentifier=module.params.get('endpointidentifier'),
        EndpointType=module.params.get('endpointtype'),
        EngineName=module.params.get('enginename'),
        Username=module.params.get('username'),
        Password=module.params.get('password'),
        ServerName=module.params.get('servername'),
        Port=module.params.get('port'),
        DatabaseName=module.params.get('databasename'),
        SslMode=module.params.get('sslmode')
    )
    if module.params.get('EndpointArn'):
        endpoint_parameters['EndpointArn'] = module.params.get('EndpointArn')
    if module.params.get('certificatearn'):
        endpoint_parameters['CertificateArn'] = \
            module.params.get('certificatearn')

    if module.params.get('dmstransfersettings'):
        endpoint_parameters['DmsTransferSettings'] = \
            module.params.get('dmstransfersettings')

    if module.params.get('extraconnectionattributes'):
        endpoint_parameters['ExtraConnectionAttributes'] =\
            module.params.get('extraconnectionattributes')

    if module.params.get('kmskeyid'):
        endpoint_parameters['KmsKeyId'] = module.params.get('kmskeyid')

    if module.params.get('tags'):
        endpoint_parameters['Tags'] = module.params.get('tags')

    if module.params.get('serviceaccessrolearn'):
        endpoint_parameters['ServiceAccessRoleArn'] = \
            module.params.get('serviceaccessrolearn')

    if module.params.get('externaltabledefinition'):
        endpoint_parameters['ExternalTableDefinition'] = \
            module.params.get('externaltabledefinition')

    if module.params.get('dynamodbsettings'):
        endpoint_parameters['DynamoDbSettings'] = \
            module.params.get('dynamodbsettings')

    if module.params.get('s3settings'):
        endpoint_parameters['S3Settings'] = module.params.get('s3settings')

    if module.params.get('mongodbsettings'):
        endpoint_parameters['MongoDbSettings'] = \
            module.params.get('mongodbsettings')

    if module.params.get('kinesissettings'):
        endpoint_parameters['KinesisSettings'] = \
            module.params.get('kinesissettings')

    if module.params.get('elasticsearchsettings'):
        endpoint_parameters['ElasticsearchSettings'] = \
            module.params.get('elasticsearchsettings')

    if module.params.get('wait'):
        endpoint_parameters['wait'] = module.boolean(module.params.get('wait'))

    if module.params.get('timeout'):
        endpoint_parameters['timeout'] = module.params.get('timeout')

    if module.params.get('retries'):
        endpoint_parameters['retries'] = module.params.get('retries')

    return endpoint_parameters


def compare_params(param_described):
    """
    Compares the dict obtained from the describe DMS endpoint and
    what we are reading from the values in the template We can
    never compare the password as boto3's method for describing
    a DMS endpoint does not return the value for
    the password for security reasons ( I assume )
    """
    modparams = create_module_params()
    changed = False
    for paramname in modparams:
        if paramname == 'Password' or paramname in param_described \
                and param_described[paramname] == modparams[paramname] or \
                str(param_described[paramname]).lower() \
                == modparams[paramname]:
            pass
        else:
            changed = True
    return changed


def modify_dms_endpoint(connection):

    try:
        params = create_module_params()
        return dms_modify_endpoint(connection, **params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to update DMS endpoint.",
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Failed to update DMS endpoint.",
                         exception=traceback.format_exc())


def create_dms_endpoint(connection):
    """
    Function to create the dms endpoint
    :param connection: boto3 aws connection
    :return: information about the dms endpoint object
    """

    try:
        params = create_module_params()
        return dms_create_endpoint(connection, **params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to create DMS endpoint.",
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Failed to create DMS endpoint.",
                         exception=traceback.format_exc())


def main():
    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        endpointidentifier=dict(required=True),
        endpointtype=dict(choices=['source', 'target'], required=True),
        enginename=dict(choices=['mysql', 'oracle', 'postgres', 'mariadb',
                                 'aurora', 'redshift', 's3', 'db2', 'azuredb',
                                 'sybase', 'dynamodb', 'mongodb', 'sqlserver'],
                        required=True),
        username=dict(),
        password=dict(no_log=True),
        servername=dict(),
        port=dict(type='int'),
        databasename=dict(),
        extraconnectionattributes=dict(),
        kmskeyid=dict(),
        tags=dict(type='dict'),
        certificatearn=dict(),
        sslmode=dict(choices=['none', 'require', 'verify-ca', 'verify-full'],
                     default='none'),
        serviceaccessrolearn=dict(),
        externaltabledefinition=dict(),
        dynamodbsettings=dict(type='dict'),
        s3settings=dict(type='dict'),
        dmstransfersettings=dict(type='dict'),
        mongodbsettings=dict(type='dict'),
        kinesissettings=dict(type='dict'),
        elasticsearchsettings=dict(type='dict'),
        wait=dict(type='bool', default=False),
        timeout=dict(type='int'),
        retries=dict(type='int')
    )
    global module
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[
            ["state", "absent", ["wait"]],
            ["wait", "True", ["timeout"]],
            ["wait", "True", ["retries"]],
        ],
        supports_check_mode=False
    )
    exit_message = None
    changed = False
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    state = module.params.get('state')
    aws_config_region, ec2_url, aws_connect_params = \
        get_aws_connection_info(module, boto3=True)
    dmsclient = get_dms_client(aws_connect_params, aws_config_region, ec2_url)
    endpoint = describe_endpoints(dmsclient,
                                  module.params.get('endpointidentifier'))
    if state == 'present':
        if endpoint_exists(endpoint):
            module.params['EndpointArn'] = \
                endpoint['Endpoints'][0].get('EndpointArn')
            params_changed = compare_params(endpoint["Endpoints"][0])
            if params_changed:
                updated_dms = modify_dms_endpoint(dmsclient)
                exit_message = updated_dms
                changed = True
            else:
                module.exit_json(changed=False, msg="Endpoint Already Exists")
        else:
            dms_properties = create_dms_endpoint(dmsclient)
            exit_message = dms_properties
            changed = True
    elif state == 'absent':
        if endpoint_exists(endpoint):
            delete_results = delete_dms_endpoint(dmsclient)
            exit_message = delete_results
            changed = True
        else:
            changed = False
            exit_message = 'DMS Endpoint does not exist'

    module.exit_json(changed=changed, msg=exit_message)


if __name__ == '__main__':
    main()
