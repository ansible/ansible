""" Modoule to handle encrypting and decrypting of items with KMS """

import base64
import botocore
import aws_encryption_sdk

def aws_kms_decrypt(key_arn, ciphertext):
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
            'aws_kms_decrypt': aws_kms_decrypt
        }
