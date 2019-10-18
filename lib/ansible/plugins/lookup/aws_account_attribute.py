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
extends_documentation_fragment:
  - aws_credentials
  - aws_region
short_description: Look up AWS account attributes.
description:
  - Describes attributes of your AWS account. You can specify one of the listed
    attribute choices or omit it to see all attributes.
options:
  attribute:
    description: The attribute for which to get the value(s).
    choices:
      - supported-platforms
      - default-vpc
      - max-instances
      - vpc-max-security-groups-per-interface
      - max-elastic-ips
      - vpc-max-elastic-ips
      - has-ec2-classic
"""

EXAMPLES = """
vars:
  has_ec2_classic: "{{ lookup('aws_account_attribute', attribute='has-ec2-classic') }}"
  # true | false

  default_vpc_id: "{{ lookup('aws_account_attribute', attribute='default-vpc') }}"
  # vpc-xxxxxxxx | none

  account_details: "{{ lookup('aws_account_attribute', wantlist='true') }}"
  # {'default-vpc': ['vpc-xxxxxxxx'], 'max-elastic-ips': ['5'], 'max-instances': ['20'],
  #  'supported-platforms': ['VPC', 'EC2'], 'vpc-max-elastic-ips': ['5'], 'vpc-max-security-groups-per-interface': ['5']}

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


def _boto3_conn(region, credentials):
    boto_profile = credentials.pop('aws_profile', None)

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


def _get_credentials(options):
    credentials = {}
    credentials['aws_profile'] = options['aws_profile']
    credentials['aws_secret_access_key'] = options['aws_secret_key']
    credentials['aws_access_key_id'] = options['aws_access_key']
    credentials['aws_session_token'] = options['aws_security_token']

    return credentials


class LookupModule(LookupBase):
    def run(self, terms, variables, **kwargs):

        self.set_options(var_options=variables, direct=kwargs)
        boto_credentials = _get_credentials(self._options)

        region = self._options['region']
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
            return any(value['AttributeValue'] == 'EC2' for value in attr['AttributeValues'])

        if attribute:
            attr = response[0]
            return [value['AttributeValue'] for value in attr['AttributeValues']]

        flattened = {}
        for k_v_dict in response:
            flattened[k_v_dict['AttributeName']] = [value['AttributeValue'] for value in k_v_dict['AttributeValues']]
        return flattened
