#!/usr/bin/python
# -*- coding: utf-8 -*
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code, get_boto3_client_method_parameters
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
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
'''

EXAMPLES = '''
'''

RETURN = '''
'''


from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code, get_boto3_client_method_parameters
from time import sleep

try:
    from botocore.exceptions import ClientError, BotoCoreError, WaiterError
except ImportError:
    pass  # caught by AnsibleAWSModule


def main():
    arg_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        endpointidentifier = dict(required=True),
        endpointtype = dict(choices=['source', 'target'], required=True),
        enginename = dict(choices=['mysql', 'oracle', 'postgres', 'mariadb', 'aurora', 'redshift', 's3', 'db2', 'azuredb', 'sybase', 'dynamodb', 'mongodb', 'sqlserver'], required=True),
        username = dict(),
        password = dict(),
        servername = dict(),
        port = dict(type='int'),
        databasename = dict(),
        extraconnectionattributes = dict(),
        kmskeyid = dict(),
        tags = dict(type='dict'),
        certificatearn = dict(),
        sslmode = dict(choices=['none', 'require', 'verify-ca', 'verify-full'], default='none'),
        serviceaccessrolearn = dict(),
        externaltabledefinition = dict(),
        dynamodbsettings = dict(type='dict'),
        s3settings = dict(type='dict'),
        dmstransfersettings = dict(type='dict'),
        mongodbsettings = dict(type='dict'),
        kinesissettings = dict(type='dict'),
        elasticsearchsettings = dict(type='dict')
    )

    module = AnsibleAWSModule(

        supports_check_mode=True
    )