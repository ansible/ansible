"""
Copyright 2019, Achintha Gunasekara <contact@achinthagunasekara.com>.
Lookup plugin to handle decrypting of items with KMS.
GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt).
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import base64
from os.path import basename
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.basic import missing_required_lib


DOCUMENTATION = """
lookup: aws_kms_decrypt
author:
    - Achintha Gunasekara (@achinthagunasekara)
version_added: "2.8"
requirements:
    - boto3
    - aws_encryption_sdk
short_description: Decrypt a given string that is encrypted using AWS KMS service.
description:
    - This lookup plugin can be used to decrypt a string with AWS KMS service,
      using a specifc key that you have access to.
    - Getting AWS Credentias will use following order.
      profile > role_arn > aws_access_key and aws_secret_key > instance IAM profile
options:
    ciphertext:
        description: Encrypted text to decrypt using AWS KMS service.
        required: True
    key_arn:
        description: AWS KMS Key's ARN to be used for decrypting the string.
        required: True
    region:
        description: AWS region to use for the KMS key.
        default: 'us-east-1'
        env:
            - name: AWS_REGION
    profile:
        description: AWS AWS credential profile to use.
        env:
            - name: AWS_PROFILE
    role_arn:
        description: ARN of the AWS IAM role to use to get credentials.
    aws_access_key:
        description: AWS access key to use. Must use together with `aws_secret_key` option.
        env:
            - name: AWS_SECRET_ACCESS_KEY
    aws_secret_key:
        description: AWS secret key to use. Must use togather with `aws_access_key` option.
        env:
            - name: AWS_SESSION_TOKEN
"""


EXAMPLES = """
vars:
    some_password: "{{ lookup('aws_kms_decrypt', ciphertext='XXXXXXXX', key_arn='arn:aws:kms:region:account-id:key/key-id') }}"

vars:
    some_password: >-
        "{{ lookup('aws_kms_decrypt', ciphertext='XXXXX
        XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        XXXX, key_arn='arn:aws:kms:region:account-id:key/key-id') }}"
"""


RETURN = """
str:
    description:
        String decrypted value of the provided encrypted string.
"""


try:
    import boto3
    BOTO_PRESENT = True
except ImportError:
    BOTO_PRESENT = False


try:
    from aws_encryption_sdk.key_providers.kms import KMSMasterKey
    from aws_encryption_sdk import KMSMasterKeyProvider, decrypt
    from aws_encryption_sdk.exceptions import AWSEncryptionSDKClientError
    AWS_ENCRYPTION_SDK_PRESENT = False
except ImportError:
    AWS_ENCRYPTION_SDK_PRESENT = False


def check_dependencies():
    """
    Ensure all required dependencies are present.
    Args:
        None.
    Return:
        None.
    """
    if not BOTO_PRESENT:
        raise AnsibleError(missing_required_lib(library='boto3'))

    if not AWS_ENCRYPTION_SDK_PRESENT:
        raise AnsibleError(missing_required_lib(library='aws_encryption_sdk'))


def role_arn_to_session(role_arn, role_session_name):
    """
    Get credentials to using a given AES role.
    Args:
        role_arn: ARN of the role to use to get credentials.
        role_session_name: A session name to use.
    Returns:
        boto3.Session: Returns a boto3.Session object.
    """
    client = boto3.client('sts')
    response = client.assume_role(
        RoleArn=role_arn,
        RoleSessionName=role_session_name
    )
    return boto3.Session(
        aws_access_key_id=response['Credentials']['AccessKeyId'],
        aws_secret_access_key=response['Credentials']['SecretAccessKey'],
        aws_session_token=response['Credentials']['SessionToken'])


def get_boto_session(region,
                     profile=None,
                     role_arn=None,
                     aws_access_key=None,
                     aws_secret_key=None):
    """
    Get boto3 session object.
    Args:
        region (str): AWS region to use.
        profile (str): AWS credential profile to use.
        role_arn (str): AWS IAM role to use to get credentials.
        aws_access_key (str): AWS access key to use.
        aws_secret_key (str): AWS secret key to use.
    Returns:
        boto3.Session: Returns a boto3.Session object.
    """
    try:
        if profile:
            return boto3.session.Session(profile_name=profile, region_name=region)
        elif role_arn:
            return role_arn_to_session(
                role_arn=role_arn,
                role_session_name=basename(role_arn)
            )
        elif aws_access_key and aws_secret_key:
            return boto3.Session(
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
            )
        return boto3.session.Session(region_name=region)
    except Exception as ex:
        raise AnsibleError("Something went wrong while creating a "
                           "boto3 session in aws_kms_plugin - {0}".format(ex))


def get_key_provider(key_arn,  # pylint: disable=too-many-arguments
                     region,
                     profile=None,
                     role_arn=None,
                     aws_access_key=None,
                     aws_secret_key=None):
    """
    Get KMS key provider object.
    Args:
        key_arn (str): AWS ARN to the KMS key.
        region (str): AWS region to use.
        profile (str): AWS credential profile to use.
        role_arn (str): AWS IAM role to use to get credentials.
        aws_access_key (str): AWS access key to use.
        aws_secret_key (str): AWS secret key to use.
    Returns:
        KMSMasterKeyProvider: KMS Master Key Provider object.
    """
    boto_session = get_boto_session(region=region,
                                    profile=profile,
                                    role_arn=role_arn,
                                    aws_access_key=aws_access_key,
                                    aws_secret_key=aws_secret_key)
    client = boto_session.client('kms')
    key_provider = KMSMasterKeyProvider()
    regional_master_key = KMSMasterKey(client=client, key_id=key_arn)
    key_provider.add_master_key_provider(regional_master_key)
    return key_provider


class LookupModule(LookupBase):
    """
    Lookup module for encrypting a value with AWS KMS.
    """

    def run(self, terms, variables, **kwargs):  # pylint: disable=signature-differs
        """
        Decrypt with KMS.
        Returns:
            str: Decrypted plain text item.
        """
        check_dependencies()
        self.set_options(var_options=variables, direct=kwargs)

        if 'region' in self._options:
            region = self._options['region']
        else:
            region = 'us-east-1'

        try:
            key_provider = get_key_provider(key_arn=self._options['key_arn'],
                                            region=region,
                                            profile=self._options['profile'],
                                            role_arn=self._options['role_arn'],
                                            aws_access_key=self._options['aws_access_key'],
                                            aws_secret_key=self._options['aws_secret_key'])
            cycled_plaintext, dummy = decrypt(
                source=base64.b64decode(self._options['ciphertext']),
                key_provider=key_provider
            )
            return cycled_plaintext.rstrip()
        except AWSEncryptionSDKClientError as kms_ex:
            raise AnsibleError("Unable to encrypt value using KMS - {0}".format(kms_ex))
