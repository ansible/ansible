#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016-2017, Yanis Guenane <yanis+ansible@guenane.org>
# Copyright: (c) 2017, Markus Teufelberger <mteufelberger+ansible@mgit.at>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: openssl_privatekey_info
version_added: '2.8'
short_description: Provide information for OpenSSL private keys
description:
    - This module allows one to query information on OpenSSL private keys.
    - It uses the pyOpenSSL or cryptography python library to interact with OpenSSL. If both the
      cryptography and PyOpenSSL libraries are available (and meet the minimum version requirements)
      cryptography will be preferred as a backend over PyOpenSSL (unless the backend is forced with
      C(select_crypto_backend))
requirements:
    - PyOpenSSL >= 0.15 or cryptography >= 1.2.3
author:
  - Felix Fontein (@felixfontein)
  - Yanis Guenane (@Spredzy)
options:
    path:
        description:
            - Remote absolute path where the private key file is loaded from.
        type: path
        required: true
    passphrase:
        description:
            - The passphrase for the private key.
        type: str
    return_private_key_data:
        description:
            - Whether to return private key data.
            - Set this to C(yes) if you do want any private information about this key
              leave the remote machine.
            - "WARNING: you have to make sure that private key data isn't accidentally logged!"
        type: bool
        default: no

    select_crypto_backend:
        description:
            - Determines which crypto backend to use.
            - The default choice is C(auto), which tries to use C(cryptography) if available, and falls back to C(pyopenssl).
            - If set to C(pyopenssl), will try to use the L(pyOpenSSL,https://pypi.org/project/pyOpenSSL/) library.
            - If set to C(cryptography), will try to use the L(cryptography,https://cryptography.io/) library.
        type: str
        default: auto
        choices: [ auto, cryptography, pyopenssl ]

seealso:
- module: openssl_privatekey
'''

EXAMPLES = r'''
- name: Generate an OpenSSL private key with the default values (4096 bits, RSA)
  openssl_privatekey:
    path: /etc/ssl/private/ansible.com.pem

- name: Get information on generated key
  openssl_privatekey_info:
    path: /etc/ssl/private/ansible.com.pem
  register: result

- name: Dump information
  debug:
    var: result
'''

RETURN = r'''
can_load_key:
    description: Whether the module was able to load the private key from disk
    returned: always
    type: bool
can_parse_key:
    description: Whether the module was able to parse the private key
    returned: always
    type: bool
public_key:
    description: Private key's public key in PEM format
    returned: success
    type: str
    sample: "-----BEGIN PUBLIC KEY-----\nMIICIjANBgkqhkiG9w0BAQEFAAOCAg8A..."
public_key_fingerprints:
    description:
        - Fingerprints of private key's public key.
        - For every hash algorithm available, the fingerprint is computed.
    returned: success
    type: dict
type:
    description:
        - The key's type.
        - One of C(RSA), C(DSA), C(ECC), C(X25519) or C(X448).
        - Will start with C(unknown) if the key type cannot be determined.
    returned: success
    type: str
    sample: RSA
public_data:
    description:
        - Public key data. Depends on key type.
    returned: success
    type: dict
private_data:
    description:
        - Private key data. Depends on key type.
    returned: success and when I(return_private_key_data) is set to C(yes)
    type: dict
'''


import abc
import datetime
import os
import traceback
from distutils.version import LooseVersion

from ansible.module_utils import crypto as crypto_utils
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native, to_text, to_bytes

MINIMAL_CRYPTOGRAPHY_VERSION = '1.2.3'
MINIMAL_PYOPENSSL_VERSION = '0.15'

PYOPENSSL_IMP_ERR = None
try:
    import OpenSSL
    from OpenSSL import crypto
    import ipaddress
    PYOPENSSL_VERSION = LooseVersion(OpenSSL.__version__)
except ImportError:
    PYOPENSSL_IMP_ERR = traceback.format_exc()
    PYOPENSSL_FOUND = False
else:
    PYOPENSSL_FOUND = True

CRYPTOGRAPHY_IMP_ERR = None
try:
    import cryptography
    from cryptography import x509
    from cryptography.hazmat.primitives import serialization
    CRYPTOGRAPHY_VERSION = LooseVersion(cryptography.__version__)
    try:
        import cryptography.hazmat.primitives.asymmetric.x25519
        CRYPTOGRAPHY_HAS_X25519 = True
    except ImportError:
        CRYPTOGRAPHY_HAS_X25519 = False
    try:
        import cryptography.hazmat.primitives.asymmetric.x448
        CRYPTOGRAPHY_HAS_X448 = True
    except ImportError:
        CRYPTOGRAPHY_HAS_X448 = False
except ImportError:
    CRYPTOGRAPHY_IMP_ERR = traceback.format_exc()
    CRYPTOGRAPHY_FOUND = False
else:
    CRYPTOGRAPHY_FOUND = True


def _get_cryptography_key_info(key):
    key_public_data = dict()
    key_private_data = dict()
    if isinstance(key, cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey):
        key_type = 'RSA'
        key_public_data['size'] = key.key_size
        key_public_data['modulus'] = key.public_key().public_numbers().n
        key_public_data['exponent'] = key.public_key().public_numbers().e
        key_private_data['p'] = key.private_numbers().p
        key_private_data['q'] = key.private_numbers().q
        key_private_data['exponent'] = key.private_numbers().d
    elif isinstance(key, cryptography.hazmat.primitives.asymmetric.dsa.DSAPrivateKey):
        key_type = 'DSA'
        key_public_data['size'] = key.key_size
        key_public_data['p'] = key.parameters().parameter_numbers().p
        key_public_data['q'] = key.parameters().parameter_numbers().q
        key_public_data['g'] = key.parameters().parameter_numbers().g
        key_public_data['y'] = key.public_key().public_numbers().y
        key_private_data['x'] = key.private_numbers().x
    elif CRYPTOGRAPHY_HAS_X25519 and isinstance(key, cryptography.hazmat.primitives.asymmetric.x25519.X25519PrivateKey):
        key_type = 'X25519'
    elif CRYPTOGRAPHY_HAS_X448 and isinstance(key, cryptography.hazmat.primitives.asymmetric.x448.X448PrivateKey):
        key_type = 'X448'
    elif isinstance(key, cryptography.hazmat.primitives.asymmetric.ec.EllipticCurvePrivateKey):
        key_type = 'ECC'
        key_public_data['curve'] = key.public_key().curve.name
        key_public_data['x'] = key.public_key().public_numbers().x
        key_public_data['y'] = key.public_key().public_numbers().y
        key_public_data['exponent_size'] = key.public_key().curve.key_size
        key_private_data['multiplier'] = key.private_numbers().private_value
    else:
        key_type = 'unknown ({0})'.format(type(key))
    return key_type, key_public_data, key_private_data


class PrivateKeyInfo(crypto_utils.OpenSSLObject):
    def __init__(self, module, backend):
        super(PrivateKeyInfo, self).__init__(
            module.params['path'],
            'present',
            False,
            module.check_mode,
        )
        self.backend = backend
        self.module = module

        self.passphrase = module.params['passphrase']
        self.return_private_key_data = module.params['return_private_key_data']

    def generate(self):
        # Empty method because crypto_utils.OpenSSLObject wants this
        pass

    def dump(self):
        # Empty method because crypto_utils.OpenSSLObject wants this
        pass

    @abc.abstractmethod
    def _get_public_key(self, binary):
        pass

    @abc.abstractmethod
    def _get_key_info(self):
        pass

    def get_info(self):
        result = dict(
            can_load_key=False,
            can_parse_key=False,
        )
        try:
            with open(self.path, 'rb') as b_priv_key_fh:
                priv_key_detail = b_priv_key_fh.read()
            result['can_load_key'] = True
        except (IOError, OSError) as exc:
            self.module.fail_json(msg=to_native(exc), **result)
        try:
            self.key = crypto_utils.load_privatekey(
                path=None,
                path_content=priv_key_detail,
                passphrase=to_bytes(self.passphrase) if self.passphrase is not None else self.passphrase,
                backend=self.backend
            )
            result['can_parse_key'] = True
        except crypto_utils.OpenSSLObjectError as exc:
            self.module.fail_json(msg=to_native(exc), **result)

        result['public_key'] = self._get_public_key(binary=False)
        result['public_key_fingerprints'] = crypto_utils.get_fingerprint_of_bytes(self._get_public_key(binary=True))

        key_type, key_public_data, key_private_data = self._get_key_info()
        result['type'] = key_type
        result['public_data'] = key_public_data
        if self.return_private_key_data:
            result['private_data'] = key_private_data

        return result


class PrivateKeyInfoCryptography(PrivateKeyInfo):
    """Validate the supplied private key, using the cryptography backend"""
    def __init__(self, module):
        super(PrivateKeyInfoCryptography, self).__init__(module, 'cryptography')

    def _get_public_key(self, binary):
        return self.key.public_key().public_bytes(
            serialization.Encoding.DER if binary else serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def _get_key_info(self):
        return _get_cryptography_key_info(self.key)


class PrivateKeyInfoPyOpenSSL(PrivateKeyInfo):
    """validate the supplied private key."""

    def __init__(self, module):
        super(PrivateKeyInfoPyOpenSSL, self).__init__(module, 'pyopenssl')

    def _get_public_key(self, binary):
        try:
            return crypto.dump_publickey(
                crypto.FILETYPE_ASN1 if binary else crypto.FILETYPE_PEM,
                self.key
            )
        except AttributeError:
            self.module.warn('Your pyOpenSSL version does not support dumping public keys. '
                             'Please upgrade to version 16.0 or newer, or use the cryptography backend.')

    def _get_key_info(self):
        if PYOPENSSL_VERSION >= LooseVersion('16.1.0') and CRYPTOGRAPHY_FOUND:
            return _get_cryptography_key_info(self.key.to_cryptography_key())
        key_public_data = dict()
        key_private_data = dict()
        openssl_key_type = self.key.type()
        if crypto.TYPE_RSA == openssl_key_type:
            key_type = 'RSA'
            key_public_data['size'] = self.key.bits()
        elif crypto.TYPE_DSA == openssl_key_type:
            key_type = 'DSA'
            key_public_data['size'] = self.key.bits()
        else:
            key_type = 'unknown ({0})'.format(self.key.type())
        return key_type, key_public_data, key_private_data


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True),
            passphrase=dict(type='str', no_log=True),
            return_private_key_data=dict(type='bool', default=False),
            select_crypto_backend=dict(type='str', default='auto', choices=['auto', 'cryptography', 'pyopenssl']),
        ),
        supports_check_mode=True,
    )

    try:
        base_dir = os.path.dirname(module.params['path']) or '.'
        if not os.path.isdir(base_dir):
            module.fail_json(
                name=base_dir,
                msg='The directory %s does not exist or the file is not a directory' % base_dir
            )

        backend = module.params['select_crypto_backend']
        if backend == 'auto':
            # Detect what backend we can use
            can_use_cryptography = CRYPTOGRAPHY_FOUND and CRYPTOGRAPHY_VERSION >= LooseVersion(MINIMAL_CRYPTOGRAPHY_VERSION)
            can_use_pyopenssl = PYOPENSSL_FOUND and PYOPENSSL_VERSION >= LooseVersion(MINIMAL_PYOPENSSL_VERSION)

            # If cryptography is available we'll use it
            if can_use_cryptography:
                backend = 'cryptography'
            elif can_use_pyopenssl:
                backend = 'pyopenssl'

            # Fail if no backend has been found
            if backend == 'auto':
                module.fail_json(msg=("Can't detect none of the required Python libraries "
                                      "cryptography (>= {0}) or PyOpenSSL (>= {1})").format(
                                          MINIMAL_CRYPTOGRAPHY_VERSION,
                                          MINIMAL_PYOPENSSL_VERSION))

        if backend == 'pyopenssl':
            if not PYOPENSSL_FOUND:
                module.fail_json(msg=missing_required_lib('pyOpenSSL'), exception=PYOPENSSL_IMP_ERR)
            privatekey = PrivateKeyInfoPyOpenSSL(module)
        elif backend == 'cryptography':
            if not CRYPTOGRAPHY_FOUND:
                module.fail_json(msg=missing_required_lib('cryptography'), exception=CRYPTOGRAPHY_IMP_ERR)
            privatekey = PrivateKeyInfoCryptography(module)

        result = privatekey.get_info()
        module.exit_json(**result)
    except crypto_utils.OpenSSLObjectError as exc:
        module.fail_json(msg=to_native(exc))


if __name__ == "__main__":
    main()
