"""
(c) 2018, Achintha Gunasekara <contact@achinthagunasekara.com>.
Module to handle encrypting and decrypting of items with KMS.
GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt).

# Help

## Arguments

You can call `aws_kms_encrypt` and `aws_kms_encrypt` from this plugin with following variables.

Mandatory - ciphertext (str): Encrypted item to decrypt.
Mandatory - key_arn (str): AWS ARN to the KMS key.
Optional - region (str): AWS region to use.
Optional - profile (str): AWS credential profile to use.
Optional - role_arn (str): AWS IAM role to use to get credentials.
Optional - aws_access_key (str): AWS access key to use.
Optional - aws_secret_key (str): AWS secret key to use.

Getting AWS Credentias will use following order.

profile > role_arn > aws_access_key and aws_secret_key > instance IAM profile

## Example

In the inventory or role defaults.
----------------------------------

encrypted_value: >-
    {{ abcd123abcd13 abcd123abcd13abcd12abcd13
    abcd123abcd13abcd123abcd13abcd123ab1d1312
    abcd123abcd13abcd123abcd13abcd123ssdsas12
    sadsdsasd | aws_kms_decrypt(KEY_ARN) }}

In the role.
------------

- debug:
    msg: "Decrypted value is {{ encrypted_value }}"
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
from os.path import basename
from ansible.errors import AnsibleFilterError

try:
    import boto3
    from aws_encryption_sdk.key_providers.kms import KMSMasterKey
    from aws_encryption_sdk import KMSMasterKeyProvider, encrypt, decrypt
    from aws_encryption_sdk.exceptions import AWSEncryptionSDKClientError
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False


def check_dependencies():
    """
    Ensure all required dependencies are present.
    Args:
        None.
    Return:
        None.
    """
    if not HAS_DEPENDENCIES:
        raise AnsibleFilterError('You need to install "boto3" and "aws_encryption_sdk"'
                                 'before using aws_kms filter')


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


def get_boto_session(profile=None,
                     role_arn=None,
                     aws_access_key=None,
                     aws_secret_key=None):
    """
    Get boto3 session object.
    Args:
        profile (str): AWS credential profile to use.
        role_arn (str): AWS IAM role to use to get credentials.
        aws_access_key (str): AWS access key to use.
        aws_secret_key (str): AWS secret key to use.
    Returns:
        boto3.Session: Returns a boto3.Session object.
    """
    try:
        if profile:
            return boto3.session.Session(profile_name=profile)
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
        return boto3.session.Session()
    except Exception as ex:
        raise AnsibleFilterError("Something went wrong while creating a "
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
    boto_session = get_boto_session(profile=profile,
                                    role_arn=role_arn,
                                    aws_access_key=aws_access_key,
                                    aws_secret_key=aws_secret_key)
    client = boto_session.client('kms', region=region)
    key_provider = KMSMasterKeyProvider()
    regional_master_key = KMSMasterKey(client=client, key_id=key_arn)
    key_provider.add_master_key_provider(regional_master_key)
    return key_provider


def aws_kms_encrypt(plaintext,  # pylint: disable=too-many-arguments
                    key_arn,
                    region='us-east-1',
                    profile=None,
                    role_arn=None,
                    aws_access_key=None,
                    aws_secret_key=None):
    """
    Encrypt with KMS.
    Args:
        plaintext (str): Plain text item to encrypt.
        key_arn (str): AWS ARN to the KMS key.
        region (str): AWS region to use.
        profile (str): AWS credential profile to use.
        role_arn (str): AWS IAM role to use to get credentials.
        aws_access_key (str): AWS access key to use.
        aws_secret_key (str): AWS secret key to use.
    Returns:
        str: Encrypted item with KMS.
    """
    check_dependencies()
    try:
        key_provider = get_key_provider(key_arn=key_arn,
                                        region=region,
                                        profile=profile,
                                        role_arn=role_arn,
                                        aws_access_key=aws_access_key,
                                        aws_secret_key=aws_secret_key)
        ciphertext, dummy = encrypt(
            source=plaintext,
            key_provider=key_provider
        )
        return base64.b64encode(ciphertext)
    except AWSEncryptionSDKClientError as kms_ex:
        raise AnsibleFilterError("Unable to encrypt value using KMS - {0}".format(kms_ex))


def aws_kms_decrypt(ciphertext,  # pylint: disable=too-many-arguments
                    key_arn,
                    region='us-east-1',
                    profile=None,
                    role_arn=None,
                    aws_access_key=None,
                    aws_secret_key=None):
    """
    Decrypt with KMS.
    Args:
        ciphertext (str): Encrypted item to decrypt.
        key_arn (str): AWS ARN to the KMS key.
        region (str): AWS region to use.
        profile (str): AWS credential profile to use.
        role_arn (str): AWS IAM role to use to get credentials.
        aws_access_key (str): AWS access key to use.
        aws_secret_key (str): AWS secret key to use.
    Returns:
        str: Decrypted plain text item.
    """
    check_dependencies()
    try:
        key_provider = get_key_provider(key_arn=key_arn,
                                        region=region,
                                        profile=profile,
                                        role_arn=role_arn,
                                        aws_access_key=aws_access_key,
                                        aws_secret_key=aws_secret_key)
        cycled_plaintext, dummy = decrypt(
            source=base64.b64decode(ciphertext),
            key_provider=key_provider
        )
        return cycled_plaintext.rstrip()
    except AWSEncryptionSDKClientError as kms_ex:
        raise AnsibleFilterError("Unable to encrypt value using KMS - {0}".format(kms_ex))


class FilterModule(object):  # pylint: disable=too-few-public-methods
    """
    Filter module to provide functions.
    """
    def filters(self):  # pylint: disable=no-self-use
        """
        Filter module to provide functions.
        Args:
            None.
        Returns:
            dictionary: Dictionary with valid methods that can be called to use this plugin.
        """
        return {
            'aws_kms_encrypt': aws_kms_encrypt,
            'aws_kms_decrypt': aws_kms_decrypt
        }
