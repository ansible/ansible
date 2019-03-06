# Copyright: (c) 2018, Aaron Smith <ajsmith10381@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
lookup: aws_secret
author:
  - Aaron Smith <ajsmith10381@gmail.com>
version_added: "2.8"
requirements:
  - boto3
  - botocore>=1.10.0
extends_documentation_fragment:
  - aws_credentials
short_description: Look up secrets stored in AWS Secrets Manager.
description:
  - Look up secrets stored in AWS Secrets Manager provided the caller
    has the appropriate permissions to read the secret.
  - Lookup is based on the secret's `Name` value.
  - Optional parameters can be passed into this lookup; `version_id` and `version_stage`
options:
  _terms:
    description: Name of the secret to look up in AWS Secrets Manager.
    required: True
  version_id:
    description: Version of the secret(s).
    required: False
  version_stage:
    description: Stage of the secret version.
    required: False
  join:
    description:
        - Join two or more entries to form an extended secret.
        - This is useful for overcoming the 4096 character limit imposed by AWS.
    type: boolean
    default: false
"""

EXAMPLES = r"""
 - name: Create RDS instance with aws_secret lookup for password param
   rds:
     command: create
     instance_name: app-db
     db_engine: MySQL
     size: 10
     instance_type: db.m1.small
     username: dbadmin
     password: "{{ lookup('aws_secret', 'DbSecret') }}"
     tags:
       Environment: staging
"""

RETURN = r"""
_raw:
  description:
    Returns the value of the secret stored in AWS Secrets Manager.
"""

from ansible.errors import AnsibleError

try:
    import boto3
    import botocore
except ImportError:
    raise AnsibleError("The lookup aws_secret requires boto3 and botocore.")

from ansible.plugins import AnsiblePlugin
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_native


def _boto3_conn(region, credentials):
    boto_profile = credentials.pop('aws_profile', None)

    try:
        connection = boto3.session.Session(profile_name=boto_profile).client('secretsmanager', region, **credentials)
    except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
        if boto_profile:
            try:
                connection = boto3.session.Session(profile_name=boto_profile).client('secretsmanager', region)
            except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
                raise AnsibleError("Insufficient credentials found.")
        else:
            raise AnsibleError("Insufficient credentials found.")
    return connection


class LookupModule(LookupBase):
    def _get_credentials(self):
        credentials = {}
        credentials['aws_profile'] = self.get_option('aws_profile')
        credentials['aws_secret_access_key'] = self.get_option('aws_secret_key')
        credentials['aws_access_key_id'] = self.get_option('aws_access_key')
        credentials['aws_session_token'] = self.get_option('aws_security_token')

        # fallback to IAM role credentials
        if not credentials['aws_profile'] and not (credentials['aws_access_key_id'] and credentials['aws_secret_access_key']):
            session = botocore.session.get_session()
            if session.get_credentials() is not None:
                credentials['aws_access_key_id'] = session.get_credentials().access_key
                credentials['aws_secret_access_key'] = session.get_credentials().secret_key
                credentials['aws_session_token'] = session.get_credentials().token

        return credentials

    def run(self, terms, variables, **kwargs):

        self.set_options(var_options=variables, direct=kwargs)
        boto_credentials = self._get_credentials()

        region = self.get_option('region')
        client = _boto3_conn(region, boto_credentials)

        secrets = []
        for term in terms:
            params = {}
            params['SecretId'] = term
            if kwargs.get('version_id'):
                params['VersionId'] = kwargs.get('version_id')
            if kwargs.get('version_stage'):
                params['VersionStage'] = kwargs.get('version_stage')

            try:
                response = client.get_secret_value(**params)
                if 'SecretBinary' in response:
                    secrets.append(response['SecretBinary'])
                if 'SecretString' in response:
                    secrets.append(response['SecretString'])
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                raise AnsibleError("Failed to retrieve secret: %s" % to_native(e))

        if kwargs.get('join'):
            joined_secret = []
            joined_secret.append(''.join(secrets))
            return joined_secret
        else:
            return secrets
