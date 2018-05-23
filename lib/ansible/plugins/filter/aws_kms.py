"""
(c) 2018, Archie Gunasekara <contact@achinthagunasekara.com>.
Module to handle encrypting and decrypting of items with AWS KMS.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import base64
from ansible.errors import AnsibleError, AnsibleFilterError


try:
    import botocore
    import aws_encryption_sdk
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False


def dependency_check():
    """
    Throw an AnsibleError if dependencies are missing.
    Args:
    Returns:
        None
    """
    if not HAS_DEPENDENCIES:
        raise AnsibleError('You need to install "botocore" and "aws_encryption_sdk"'
                           'before using aws_kms filter')


def aws_kms_encrypt(plaintext, key_arn):
    """
    Encrypt with AWS KMS.
    Args:
        plaintext (str): Plain text string to encrypt.
        key_arn (str): ARN to the AWS KMS key to use for encryption.
    Returns:
        str: Encrypted string for the plain text input.
    """
    dependency_check()
    try:
        session = botocore.session.get_session()
        kms_kwargs = {
            'key_ids': [key_arn],
            'botocore_session': session
        }
        master_key_provider = aws_encryption_sdk.KMSMasterKeyProvider(**kms_kwargs)
        ciphertext, encryptor_header = aws_encryption_sdk.encrypt(  # pylint: disable=unused-variable
            source=plaintext,
            key_provider=master_key_provider
        )
        return base64.b64encode(ciphertext)
    except aws_encryption_sdk.exceptions.NotSupportedError:
        raise AnsibleFilterError('Unable to encrypt value using KMS')


def aws_kms_decrypt(ciphertext, key_arn):
    """
    Decrypt with AWS KMS.
    Args:
        ciphertext (str): Encrypted string to decrypt.
        key_arn (str): ARN to the AWS KMS key to use for decryption.
    Returns:
        str: Plain text decrypted string.
    """
    dependency_check()
    try:
        session = botocore.session.get_session()
        kms_kwargs = {
            'key_ids': [key_arn],
            'botocore_session': session
        }
        master_key_provider = aws_encryption_sdk.KMSMasterKeyProvider(**kms_kwargs)
        cycled_plaintext, decrypted_header = aws_encryption_sdk.decrypt(  # pylint: disable=unused-variable
            source=base64.b64decode(ciphertext),
            key_provider=master_key_provider
        )
        return cycled_plaintext.rstrip()
    except aws_encryption_sdk.exceptions.NotSupportedError:
        raise AnsibleFilterError('Unable to decrypt value using KMS')


class FilterModule(object):  # pylint: disable=too-few-public-methods
    """ Filter module to provide functions """
    def filters(self):  # pylint: disable=no-self-use
        """ Filter module to provide functions """
        return {
            'aws_kms_encrypt': aws_kms_encrypt,
            'aws_kms_decrypt': aws_kms_decrypt
        }
