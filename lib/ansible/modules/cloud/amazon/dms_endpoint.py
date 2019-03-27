#!/usr/bin/python
# -*- coding: utf-8 -*
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
import pdb

import traceback

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


from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, HAS_BOTO3, ansible_dict_to_boto3_filter_list, camel_dict_to_snake_dict, get_aws_connection_info, AWSRetry


try:
    #from botocore.exceptions import ClientError, BotoCoreError, WaiterError
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

backoff_params = dict(tries=5, delay=1, backoff=1.5)


@AWSRetry.backoff(**backoff_params)
def describe_endpoints(connection, endpoint_identifier):
    """ checks if the endpoint exists """
    try:
        endpoint_filter = dict(Name='endpoint-id', Values=[endpoint_identifier])
        return connection.describe_endpoints(Filters=[endpoint_filter])
    except:
        return {'Endpoints': []}


@AWSRetry.backoff(**backoff_params)
def dms_delete_endpoint(client, **params):
    """deletes the DMS endpoint based on the EndpointArn"""
    if module.params.get('wait'):
        return False
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


def endpoint_exists(endpoint):
    """ Returns boolean based on the existance of the endpoint
    :param endpoint: dict containing the described endpoint
    :return: bool
    """
    return bool(len(endpoint['Endpoints']))


#def get_dms_waiters(connection):
#    return True

def get_dms_client(aws_connect_params, region, ec2_url):
    client_params = dict(
        module=module,
        conn_type='client',
        resource='dms',
        region=region,
        endpoint=ec2_url,
        **aws_connect_params
    )
    return boto3_conn(**client_params)

def delete_dms_endpoint(connection):
    try:
        endpoint_data = describe_endpoints(connection, module.params.get('endpointidentifier'))
        endpoint_arn = endpoint_data['Endpoints'][0].get('EndpointArn')
        delete_arn = dict(
            EndpointArn=endpoint_arn
        )
        return connection.delete_endpoint(**delete_arn)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to delete the  DMS endpoint.",
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Failed to delete the DMS endpoint.",
                         exception=traceback.format_exc())
    except:
        module.fail_json(msg="Failed to delete the DMS endpoint.",
                         exception=traceback.format_exc())


def create_module_params():
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
        endpoint_parameters['CertificateArn'] = module.params.get('certificatearn')

    if module.params.get('dmstransfersettings'):
        endpoint_parameters['DmsTransferSettings'] = module.params.get('dmstransfersettings')

    if module.params.get('extraconnectionattributes'):
        endpoint_parameters['ExtraConnectionAttributes'] = module.params.get('extraconnectionattributes')

    if module.params.get('kmskeyid'):
        endpoint_parameters['KmsKeyId'] = module.params.get('kmskeyid')

    if module.params.get('tags'):
        endpoint_parameters['Tags'] = module.params.get('tags')

    if module.params.get('serviceaccessrolearn'):
        endpoint_parameters['ServiceAccessRoleArn'] = module.params.get('serviceaccessrolearn')

    if module.params.get('externaltabledefinition'):
        endpoint_parameters['ExternalTableDefinition'] = module.params.get('externaltabledefinition')

    if module.params.get('dynamodbsettings'):
        endpoint_parameters['DynamoDbSettings'] = module.params.get('dynamodbsettings')

    if module.params.get('s3settings'):
        endpoint_parameters['S3Settings'] = module.params.get('s3settings')

    if module.params.get('mongodbsettings'):
        endpoint_parameters['MongoDbSettings'] = module.params.get('mongodbsettings')

    if module.params.get('kinesissettings'):
        endpoint_parameters['KinesisSettings'] = module.params.get('kinesissettings')

    if module.params.get('elasticsearchsettings'):
        endpoint_parameters['ElasticsearchSettings'] = module.params.get('elasticsearchsettings')

    return endpoint_parameters


def compare_params(param_described):
    """
    Compares the dict obtained from the describe DMS endpoint and what we are reading from the values in the template
    We can never compare the password as boto3's method for describing a DMS endpoint does not return the value for
    the password for security reasons ( I assume )
    """
    modparams = create_module_params()
    changed = False
    for paramname in modparams:
        if paramname == 'Password' or paramname in param_described   and param_described[paramname] == modparams[paramname] or \
                str(param_described[paramname]).lower() == modparams[paramname]:
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
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Failed to update DMS endpoint.",
                         exception=traceback.format_exc())
    except:
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
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Failed to create DMS endpoint.",
                         exception=traceback.format_exc())
    except:
        module.fail_json(msg="Failed to create DMS endpoint.",
                         exception=traceback.format_exc())


def main():
    """ main function, instanciates the ansible module and performs the initial logic"""
    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        endpointidentifier=dict(required=True),
        endpointtype=dict(choices=['source', 'target'], required=True),
        enginename=dict(choices=['mysql', 'oracle', 'postgres', 'mariadb', 'aurora',
                                 'redshift', 's3', 'db2', 'azuredb', 'sybase',
                                 'dynamodb', 'mongodb', 'sqlserver'], required=True),
        username=dict(),
        password=dict(no_log=True),
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
        elasticsearchsettings=dict(type='dict'),
        wait=dict(type='bool')
    )
    global module
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[
            ["state", "absent", ["wait"]],
        ],
        supports_check_mode=True
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    state = module.params.get('state')
    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    dmsclient = get_dms_client(aws_connect_params, region, ec2_url)
    endpoint = describe_endpoints(dmsclient, module.params.get('endpointidentifier'))
    if state == 'present':
        if endpoint_exists(endpoint):
            module.params['EndpointArn'] = endpoint['Endpoints'][0].get('EndpointArn')
            changed = compare_params(endpoint["Endpoints"][0])
            if changed:
                updated_dms = modify_dms_endpoint(dmsclient)
                module.exit_json(changed=True, msg=updated_dms)
            else:
                module.exit_json(changed=False, msg="Endpoint Already Exists")
        else:
            dms_properties = create_dms_endpoint(dmsclient)
            module.exit_json(changed=True, **dms_properties)
    elif state == 'absent':
        if endpoint_exists(endpoint):
            delete_results = delete_dms_endpoint(dmsclient)
            module.exit_json(changed=True, **delete_results)
        else:
            module.exit_json(changed=False, msg='DMS Endpoint does not exists')



if __name__ == '__main__':
    main()
