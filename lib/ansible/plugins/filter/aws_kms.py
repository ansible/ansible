""" Modoule to handle encrypting and decrypting of items with KMS """
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type  # pylint: disable=invalid-name
import base64
import botocore
import aws_encryption_sdk


def aws_kms_encrypt(plaintext, key_arn):
    """ Encrypt with KMS """
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
        raise Exception("Unable to decrypt vaule using KMS")


def aws_kms_decrypt(ciphertext, key_arn):
    """ Decrypt with KMS """
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
        raise Exception("Unable to decrypt vaule using KMS")


class FilterModule(object):  # pylint: disable=too-few-public-methods
    """ Filter moule to provide functions """
    def filters(self):  # pylint: disable=no-self-use
        """ Filter moule to provide functions """
        return {
            'aws_kms_encrypt': aws_kms_encrypt,
            'aws_kms_decrypt': aws_kms_decrypt
        }
