# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
lookup: aws_account_attribute
author:
  - Sloane Hertel <shertel@redhat.com>
version_added: "2.5"
requirements:
  - boto3
  - botocore
short_description: Look up AWS account attributes.
description:
  - Describes attributes of your AWS account. You can specify one of the listed
    attribute choices or omit it to see all attributes.
options:
  attribute:
    description: The attribute for which to get the value(s).
    default: null
    choices:
      - supported-platforms
      - default-vpc
      - max-instances
      - vpc-max-security-groups-per-interface
      - max-elastic-ips
      - vpc-max-elastic-ips
      - has-ec2-classic
  boto_profile:
    description: The boto profile to use to create the connection.
    default: null
    env:
      - name: AWS_PROFILE
      - name: AWS_DEFAULT_PROFILE
  aws_access_key:
    description: The AWS access key to use.
    default: null
    env:
      - name: AWS_ACCESS_KEY_ID
      - name: AWS_ACCESS_KEY
      - name: EC2_ACCESS_KEY
  aws_secret_key:
    description: The AWS secret key that corresponds to the access key.
    default: null
    env:
      - name: AWS_SECRET_ACCESS_KEY
      - name: AWS_SECRET_KEY
      - name: EC2_SECRET_KEY
  aws_security_token:
    description: The AWS security token if using temporary access and secret keys.
    default: null
    env:
      - name: AWS_SECURITY_TOKEN
      - name: AWS_SESSION_TOKEN
      - name: EC2_SECURITY_TOKEN
  region:
    description: The region for which to create the connection.
    default: null
    env:
      - name: AWS_REGION
      - name: EC2_REGION
"""

EXAMPLES = """
vars:
  has_ec2_classic: "{{ lookup('aws_account_attribute', attribute='has-ec2-classic') }}"
  # true | false

  default_vpc_id: "{{ lookup('aws_account_attribute', attribute='default-vpc') }}"
  # vpc-xxxxxxxx | none

  account_details: "{{ lookup('aws_account_attribute', wantlist='true') }}"
  # [{'AttributeName': 'supported-platforms', 'AttributeValues': [{'AttributeValue': 'VPC'}],...}]
"""

RETURN = """
_raw:
  description:
    Returns a boolean when I(attribute) is check_ec2_classic. Otherwise returns the value(s) of the attribute
    (or all attributes if one is not specified).
"""

from ansible.errors import AnsibleError

try:
    import boto3
    import botocore
except ImportError:
    raise AnsibleError("The lookup aws_account_attribute requires boto3 and botocore.")

from ansible.plugins import AnsiblePlugin
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info
from ansible.module_utils._text import to_native
from ansible.module_utils.six import string_types
import os


def _find_cred(possible_env_vars):
    for env_var in possible_env_vars:
        if os.environ.get(env_var):
            return os.environ.get(env_var)


def _get_region(**kwargs):
    region = kwargs.get('region')

    if not region:
        region = _find_cred(possible_env_vars=('AWS_REGION', 'EC2_REGION'))

    return region


def _get_credentials(**kwargs):
    '''
        :return A dictionary of boto client credentials
    '''
    boto_profile = kwargs.get('boto_profile')
    aws_access_key_id = kwargs.get('aws_access_key')
    aws_secret_access_key = kwargs.get('aws_secret_key')
    aws_security_token = kwargs.get('aws_security_token')

    if not boto_profile:
        env_vars = ('AWS_PROFILE', 'AWS_DEFAULT_PROFILE')
        boto_profile = _find_cred(env_vars)

    if not aws_access_key_id:
        env_vars = ('AWS_ACCESS_KEY_ID', 'AWS_ACCESS_KEY', 'EC2_ACCESS_KEY')
        aws_access_key_id = _find_cred(env_vars)

    if not aws_secret_access_key:
        env_vars = ('AWS_SECRET_ACCESS_KEY', 'AWS_SECRET_KEY', 'EC2_SECRET_KEY')
        aws_secret_access_key = _find_cred(env_vars)

    if not aws_security_token:
        env_vars = ('AWS_SECURITY_TOKEN', 'AWS_SESSION_TOKEN', 'EC2_SECURITY_TOKEN')
        aws_security_token = _find_cred(env_vars)

    if not boto_profile and not (aws_access_key_id and aws_secret_access_key):
        raise AnsibleError("Insufficient boto credentials found.")

    boto_params = {}
    for param_name, credential in (('aws_access_key_id', aws_access_key_id),
                       ('aws_secret_access_key', aws_secret_access_key),
                       ('aws_session_token', aws_security_token),
                       ('boto_profile', boto_profile)):
        if credential:
            boto_params[param_name] = credential

    return boto_params


def _boto3_conn(region, credentials):
    if 'boto_profile' in credentials:
        boto_profile = credentials.pop('boto_profile')
    else:
        boto_profile = None

    try:
        connection = boto3.session.Session(profile_name=boto_profile).client('ec2', region, **credentials)
    except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
        if boto_profile:
            try:
                connection = boto3.session.Session(profile_name=boto_profile).client('ec2', region)
            except (botocore.exceptions.ProfileNotFound, botocore.exceptions.PartialCredentialsError) as e:
                raise AnsibleError("Insufficient credentials found.")
        else:
            raise AnsibleError("Insufficient credentials found.")
    return connection


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):

        boto_credentials = _get_credentials(**kwargs)
        region = _get_region(**kwargs)
        client = _boto3_conn(region, boto_credentials)

        attribute = kwargs.get('attribute')
        params = {'AttributeNames': []}
        check_ec2_classic = False
        if 'has-ec2-classic' == attribute:
            check_ec2_classic = True
            params['AttributeNames'] = ['supported-platforms']
        elif attribute:
            params['AttributeNames'] = [attribute]

        try:
            response = client.describe_account_attributes(**params)['AccountAttributes']
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            raise AnsibleError("Failed to describe account attributes: %s" % to_native(e))

        if check_ec2_classic:
            attr = response[0]
            if any([bool(value['AttributeValue'] == 'EC2') for value in attr['AttributeValues']]):
                return True
            return False

        if attribute:
            attr = response[0]
            return [value['AttributeValue'] for value in attr['AttributeValues']]

        return response
