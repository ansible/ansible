#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Yanis Guenane <yanis+ansible@guenane.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: openssl_privatekey
version_added: "2.3"
short_description: Generate OpenSSL private keys
description:
    - This module allows one to (re)generate OpenSSL private keys.
    - One can generate L(RSA,https://en.wikipedia.org/wiki/RSA_(cryptosystem)),
      L(DSA,https://en.wikipedia.org/wiki/Digital_Signature_Algorithm),
      L(ECC,https://en.wikipedia.org/wiki/Elliptic-curve_cryptography) or
      L(EdDSA,https://en.wikipedia.org/wiki/EdDSA) private keys.
    - Keys are generated in PEM format.
    - "Please note that the module regenerates private keys if they don't match
      the module's options. In particular, if you provide another passphrase
      (or specify none), change the keysize, etc., the private key will be
      regenerated. If you are concerned that this could **overwrite your private key**,
      consider using the I(backup) option."
    - The module can use the cryptography Python library, or the pyOpenSSL Python
      library. By default, it tries to detect which one is available. This can be
      overridden with the I(select_crypto_backend) option."
requirements:
    - Either cryptography >= 1.2.3 (older versions might work as well)
    - Or pyOpenSSL
author:
    - Yanis Guenane (@Spredzy)
    - Felix Fontein (@felixfontein)
options:
    state:
        description:
            - Whether the private key should exist or not, taking action if the state is different from what is stated.
        type: str
        default: present
        choices: [ absent, present ]
    size:
        description:
            - Size (in bits) of the TLS/SSL key to generate.
        type: int
        default: 4096
    type:
        description:
            - The algorithm used to generate the TLS/SSL private key.
            - Note that C(ECC), C(X25519), C(X448), C(Ed25519) and C(Ed448) require the C(cryptography) backend.
              C(X25519) needs cryptography 2.5 or newer, while C(X448), C(Ed25519) and C(Ed448) require
              cryptography 2.6 or newer. For C(ECC), the minimal cryptography version required depends on the
              I(curve) option.
        type: str
        default: RSA
        choices: [ DSA, ECC, Ed25519, Ed448, RSA, X25519, X448 ]
    curve:
        description:
            - Note that not all curves are supported by all versions of C(cryptography).
            - For maximal interoperability, C(secp384r1) or C(secp256r1) should be used.
            - We use the curve names as defined in the
              L(IANA registry for TLS,https://www.iana.org/assignments/tls-parameters/tls-parameters.xhtml#tls-parameters-8).
        type: str
        choices:
            - secp384r1
            - secp521r1
            - secp224r1
            - secp192r1
            - secp256r1
            - secp256k1
            - brainpoolP256r1
            - brainpoolP384r1
            - brainpoolP512r1
            - sect571k1
            - sect409k1
            - sect283k1
            - sect233k1
            - sect163k1
            - sect571r1
            - sect409r1
            - sect283r1
            - sect233r1
            - sect163r2
        version_added: "2.8"
    force:
        description:
            - Should the key be regenerated even if it already exists.
        type: bool
        default: no
    path:
        description:
            - Name of the file in which the generated TLS/SSL private key will be written. It will have 0600 mode.
        type: path
        required: true
    passphrase:
        description:
            - The passphrase for the private key.
        type: str
        version_added: "2.4"
    cipher:
        description:
            - The cipher to encrypt the private key. (Valid values can be found by
              running `openssl list -cipher-algorithms` or `openssl list-cipher-algorithms`,
              depending on your OpenSSL version.)
            - When using the C(cryptography) backend, use C(auto).
        type: str
        version_added: "2.4"
    select_crypto_backend:
        description:
            - Determines which crypto backend to use.
            - The default choice is C(auto), which tries to use C(cryptography) if available, and falls back to C(pyopenssl).
            - If set to C(pyopenssl), will try to use the L(pyOpenSSL,https://pypi.org/project/pyOpenSSL/) library.
            - If set to C(cryptography), will try to use the L(cryptography,https://cryptography.io/) library.
        type: str
        default: auto
        choices: [ auto, cryptography, pyopenssl ]
        version_added: "2.8"
    backup:
        description:
            - Create a backup file including a timestamp so you can get
              the original private key back if you overwrote it with a new one by accident.
        type: bool
        default: no
        version_added: "2.8"
extends_documentation_fragment:
- files
seealso:
- module: openssl_certificate
- module: openssl_csr
- module: openssl_dhparam
- module: openssl_pkcs12
- module: openssl_publickey
'''

EXAMPLES = r'''
- name: Generate an OpenSSL private key with the default values (4096 bits, RSA)
  openssl_privatekey:
    path: /etc/ssl/private/ansible.com.pem

- name: Generate an OpenSSL private key with the default values (4096 bits, RSA) and a passphrase
  openssl_privatekey:
    path: /etc/ssl/private/ansible.com.pem
    passphrase: ansible
    cipher: aes256

- name: Generate an OpenSSL private key with a different size (2048 bits)
  openssl_privatekey:
    path: /etc/ssl/private/ansible.com.pem
    size: 2048

- name: Force regenerate an OpenSSL private key if it already exists
  openssl_privatekey:
    path: /etc/ssl/private/ansible.com.pem
    force: yes

- name: Generate an OpenSSL private key with a different algorithm (DSA)
  openssl_privatekey:
    path: /etc/ssl/private/ansible.com.pem
    type: DSA
'''

RETURN = r'''
size:
    description: Size (in bits) of the TLS/SSL private key.
    returned: changed or success
    type: int
    sample: 4096
type:
    description: Algorithm used to generate the TLS/SSL private key.
    returned: changed or success
    type: str
    sample: RSA
curve:
    description: Elliptic curve used to generate the TLS/SSL private key.
    returned: changed or success, and I(type) is C(ECC)
    type: str
    sample: secp256r1
filename:
    description: Path to the generated TLS/SSL private key file.
    returned: changed or success
    type: str
    sample: /etc/ssl/private/ansible.com.pem
fingerprint:
    description:
    - The fingerprint of the public key. Fingerprint will be generated for each C(hashlib.algorithms) available.
    - The PyOpenSSL backend requires PyOpenSSL >= 16.0 for meaningful output.
    returned: changed or success
    type: dict
    sample:
      md5: "84:75:71:72:8d:04:b5:6c:4d:37:6d:66:83:f5:4c:29"
      sha1: "51:cc:7c:68:5d:eb:41:43:88:7e:1a:ae:c7:f8:24:72:ee:71:f6:10"
      sha224: "b1:19:a6:6c:14:ac:33:1d:ed:18:50:d3:06:5c:b2:32:91:f1:f1:52:8c:cb:d5:75:e9:f5:9b:46"
      sha256: "41:ab:c7:cb:d5:5f:30:60:46:99:ac:d4:00:70:cf:a1:76:4f:24:5d:10:24:57:5d:51:6e:09:97:df:2f:de:c7"
      sha384: "85:39:50:4e:de:d9:19:33:40:70:ae:10:ab:59:24:19:51:c3:a2:e4:0b:1c:b1:6e:dd:b3:0c:d9:9e:6a:46:af:da:18:f8:ef:ae:2e:c0:9a:75:2c:9b:b3:0f:3a:5f:3d"
      sha512: "fd:ed:5e:39:48:5f:9f:fe:7f:25:06:3f:79:08:cd:ee:a5:e7:b3:3d:13:82:87:1f:84:e1:f5:c7:28:77:53:94:86:56:38:69:f0:d9:35:22:01:1e:a6:60:...:0f:9b"
backup_file:
    description: Name of backup file created.
    returned: changed and if I(backup) is C(yes)
    type: str
    sample: /path/to/privatekey.pem.2019-03-09@11:22~
'''

import abc
import os
import traceback
from distutils.version import LooseVersion

MINIMAL_PYOPENSSL_VERSION = '0.6'
MINIMAL_CRYPTOGRAPHY_VERSION = '1.2.3'

PYOPENSSL_IMP_ERR = None
try:
    import OpenSSL
    from OpenSSL import crypto
    PYOPENSSL_VERSION = LooseVersion(OpenSSL.__version__)
except ImportError:
    PYOPENSSL_IMP_ERR = traceback.format_exc()
    PYOPENSSL_FOUND = False
else:
    PYOPENSSL_FOUND = True

CRYPTOGRAPHY_IMP_ERR = None
try:
    import cryptography
    import cryptography.exceptions
    import cryptography.hazmat.backends
    import cryptography.hazmat.primitives.serialization
    import cryptography.hazmat.primitives.asymmetric.rsa
    import cryptography.hazmat.primitives.asymmetric.dsa
    import cryptography.hazmat.primitives.asymmetric.ec
    import cryptography.hazmat.primitives.asymmetric.utils
    CRYPTOGRAPHY_VERSION = LooseVersion(cryptography.__version__)
except ImportError:
    CRYPTOGRAPHY_IMP_ERR = traceback.format_exc()
    CRYPTOGRAPHY_FOUND = False
else:
    CRYPTOGRAPHY_FOUND = True

from ansible.module_utils.crypto import (
    CRYPTOGRAPHY_HAS_X25519,
    CRYPTOGRAPHY_HAS_X25519_FULL,
    CRYPTOGRAPHY_HAS_X448,
    CRYPTOGRAPHY_HAS_ED25519,
    CRYPTOGRAPHY_HAS_ED448,
)

from ansible.module_utils import crypto as crypto_utils
from ansible.module_utils._text import to_native, to_bytes
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.six import string_types


class PrivateKeyError(crypto_utils.OpenSSLObjectError):
    pass


class PrivateKeyBase(crypto_utils.OpenSSLObject):

    def __init__(self, module):
        super(PrivateKeyBase, self).__init__(
            module.params['path'],
            module.params['state'],
            module.params['force'],
            module.check_mode
        )
        self.size = module.params['size']
        self.passphrase = module.params['passphrase']
        self.cipher = module.params['cipher']
        self.privatekey = None
        self.fingerprint = {}

        self.backup = module.params['backup']
        self.backup_file = None

        if module.params['mode'] is None:
            module.params['mode'] = '0600'

    @abc.abstractmethod
    def _generate_private_key_data(self):
        pass

    @abc.abstractmethod
    def _get_fingerprint(self):
        pass

    def generate(self, module):
        """Generate a keypair."""

        if not self.check(module, perms_required=False) or self.force:
            if self.backup:
                self.backup_file = module.backup_local(self.path)
            privatekey_data = self._generate_private_key_data()
            crypto_utils.write_file(module, privatekey_data, 0o600)
            self.changed = True

        self.fingerprint = self._get_fingerprint()
        file_args = module.load_file_common_arguments(module.params)
        if module.set_fs_attributes_if_different(file_args, False):
            self.changed = True

    def remove(self, module):
        if self.backup:
            self.backup_file = module.backup_local(self.path)
        super(PrivateKeyBase, self).remove(module)

    @abc.abstractmethod
    def _check_passphrase(self):
        pass

    @abc.abstractmethod
    def _check_size_and_type(self):
        pass

    def check(self, module, perms_required=True):
        """Ensure the resource is in its desired state."""

        state_and_perms = super(PrivateKeyBase, self).check(module, perms_required)

        if not state_and_perms or not self._check_passphrase():
            return False

        return self._check_size_and_type()

    def dump(self):
        """Serialize the object into a dictionary."""

        result = {
            'size': self.size,
            'filename': self.path,
            'changed': self.changed,
            'fingerprint': self.fingerprint,
        }
        if self.backup_file:
            result['backup_file'] = self.backup_file

        return result


# Implementation with using pyOpenSSL
class PrivateKeyPyOpenSSL(PrivateKeyBase):

    def __init__(self, module):
        super(PrivateKeyPyOpenSSL, self).__init__(module)

        if module.params['type'] == 'RSA':
            self.type = crypto.TYPE_RSA
        elif module.params['type'] == 'DSA':
            self.type = crypto.TYPE_DSA
        else:
            module.fail_json(msg="PyOpenSSL backend only supports RSA and DSA keys.")

    def _generate_private_key_data(self):
        self.privatekey = crypto.PKey()

        try:
            self.privatekey.generate_key(self.type, self.size)
        except (TypeError, ValueError) as exc:
            raise PrivateKeyError(exc)

        if self.cipher and self.passphrase:
            return crypto.dump_privatekey(crypto.FILETYPE_PEM, self.privatekey,
                                          self.cipher, to_bytes(self.passphrase))
        else:
            return crypto.dump_privatekey(crypto.FILETYPE_PEM, self.privatekey)

    def _get_fingerprint(self):
        return crypto_utils.get_fingerprint(self.path, self.passphrase)

    def _check_passphrase(self):
        try:
            crypto_utils.load_privatekey(self.path, self.passphrase)
            return True
        except Exception as dummy:
            return False

    def _check_size_and_type(self):
        def _check_size(privatekey):
            return self.size == privatekey.bits()

        def _check_type(privatekey):
            return self.type == privatekey.type()

        try:
            privatekey = crypto_utils.load_privatekey(self.path, self.passphrase)
        except crypto_utils.OpenSSLBadPassphraseError as exc:
            raise PrivateKeyError(exc)

        return _check_size(privatekey) and _check_type(privatekey)

    def dump(self):
        """Serialize the object into a dictionary."""

        result = super(PrivateKeyPyOpenSSL, self).dump()

        if self.type == crypto.TYPE_RSA:
            result['type'] = 'RSA'
        else:
            result['type'] = 'DSA'

        return result


# Implementation with using cryptography
class PrivateKeyCryptography(PrivateKeyBase):

    def _get_ec_class(self, ectype):
        ecclass = cryptography.hazmat.primitives.asymmetric.ec.__dict__.get(ectype)
        if ecclass is None:
            self.module.fail_json(msg='Your cryptography version does not support {0}'.format(ectype))
        return ecclass

    def _add_curve(self, name, ectype, deprecated=False):
        def create(size):
            ecclass = self._get_ec_class(ectype)
            return ecclass()

        def verify(privatekey):
            ecclass = self._get_ec_class(ectype)
            return isinstance(privatekey.private_numbers().public_numbers.curve, ecclass)

        self.curves[name] = {
            'create': create,
            'verify': verify,
            'deprecated': deprecated,
        }

    def __init__(self, module):
        super(PrivateKeyCryptography, self).__init__(module)

        self.curves = dict()
        self._add_curve('secp384r1', 'SECP384R1')
        self._add_curve('secp521r1', 'SECP521R1')
        self._add_curve('secp224r1', 'SECP224R1')
        self._add_curve('secp192r1', 'SECP192R1')
        self._add_curve('secp256r1', 'SECP256R1')
        self._add_curve('secp256k1', 'SECP256K1')
        self._add_curve('brainpoolP256r1', 'BrainpoolP256R1', deprecated=True)
        self._add_curve('brainpoolP384r1', 'BrainpoolP384R1', deprecated=True)
        self._add_curve('brainpoolP512r1', 'BrainpoolP512R1', deprecated=True)
        self._add_curve('sect571k1', 'SECT571K1', deprecated=True)
        self._add_curve('sect409k1', 'SECT409K1', deprecated=True)
        self._add_curve('sect283k1', 'SECT283K1', deprecated=True)
        self._add_curve('sect233k1', 'SECT233K1', deprecated=True)
        self._add_curve('sect163k1', 'SECT163K1', deprecated=True)
        self._add_curve('sect571r1', 'SECT571R1', deprecated=True)
        self._add_curve('sect409r1', 'SECT409R1', deprecated=True)
        self._add_curve('sect283r1', 'SECT283R1', deprecated=True)
        self._add_curve('sect233r1', 'SECT233R1', deprecated=True)
        self._add_curve('sect163r2', 'SECT163R2', deprecated=True)

        self.module = module
        self.cryptography_backend = cryptography.hazmat.backends.default_backend()

        self.type = module.params['type']
        self.curve = module.params['curve']
        if not CRYPTOGRAPHY_HAS_X25519 and self.type == 'X25519':
            self.module.fail_json(msg='Your cryptography version does not support X25519')
        if not CRYPTOGRAPHY_HAS_X25519_FULL and self.type == 'X25519':
            self.module.fail_json(msg='Your cryptography version does not support X25519 serialization')
        if not CRYPTOGRAPHY_HAS_X448 and self.type == 'X448':
            self.module.fail_json(msg='Your cryptography version does not support X448')
        if not CRYPTOGRAPHY_HAS_ED25519 and self.type == 'Ed25519':
            self.module.fail_json(msg='Your cryptography version does not support Ed25519')
        if not CRYPTOGRAPHY_HAS_ED448 and self.type == 'Ed448':
            self.module.fail_json(msg='Your cryptography version does not support Ed448')

    def _generate_private_key_data(self):
        format = cryptography.hazmat.primitives.serialization.PrivateFormat.TraditionalOpenSSL
        try:
            if self.type == 'RSA':
                self.privatekey = cryptography.hazmat.primitives.asymmetric.rsa.generate_private_key(
                    public_exponent=65537,  # OpenSSL always uses this
                    key_size=self.size,
                    backend=self.cryptography_backend
                )
            if self.type == 'DSA':
                self.privatekey = cryptography.hazmat.primitives.asymmetric.dsa.generate_private_key(
                    key_size=self.size,
                    backend=self.cryptography_backend
                )
            if CRYPTOGRAPHY_HAS_X25519_FULL and self.type == 'X25519':
                self.privatekey = cryptography.hazmat.primitives.asymmetric.x25519.X25519PrivateKey.generate()
                format = cryptography.hazmat.primitives.serialization.PrivateFormat.PKCS8
            if CRYPTOGRAPHY_HAS_X448 and self.type == 'X448':
                self.privatekey = cryptography.hazmat.primitives.asymmetric.x448.X448PrivateKey.generate()
                format = cryptography.hazmat.primitives.serialization.PrivateFormat.PKCS8
            if CRYPTOGRAPHY_HAS_ED25519 and self.type == 'Ed25519':
                self.privatekey = cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PrivateKey.generate()
                format = cryptography.hazmat.primitives.serialization.PrivateFormat.PKCS8
            if CRYPTOGRAPHY_HAS_ED448 and self.type == 'Ed448':
                self.privatekey = cryptography.hazmat.primitives.asymmetric.ed448.Ed448PrivateKey.generate()
                format = cryptography.hazmat.primitives.serialization.PrivateFormat.PKCS8
            if self.type == 'ECC' and self.curve in self.curves:
                if self.curves[self.curve]['deprecated']:
                    self.module.warn('Elliptic curves of type {0} should not be used for new keys!'.format(self.curve))
                self.privatekey = cryptography.hazmat.primitives.asymmetric.ec.generate_private_key(
                    curve=self.curves[self.curve]['create'](self.size),
                    backend=self.cryptography_backend
                )
        except cryptography.exceptions.UnsupportedAlgorithm as e:
            self.module.fail_json(msg='Cryptography backend does not support the algorithm required for {0}'.format(self.type))

        # Select key encryption
        encryption_algorithm = cryptography.hazmat.primitives.serialization.NoEncryption()
        if self.cipher and self.passphrase:
            if self.cipher == 'auto':
                encryption_algorithm = cryptography.hazmat.primitives.serialization.BestAvailableEncryption(to_bytes(self.passphrase))
            else:
                self.module.fail_json(msg='Cryptography backend can only use "auto" for cipher option.')

        # Serialize key
        return self.privatekey.private_bytes(
            encoding=cryptography.hazmat.primitives.serialization.Encoding.PEM,
            format=format,
            encryption_algorithm=encryption_algorithm
        )

    def _load_privatekey(self):
        try:
            with open(self.path, 'rb') as f:
                return cryptography.hazmat.primitives.serialization.load_pem_private_key(
                    f.read(),
                    None if self.passphrase is None else to_bytes(self.passphrase),
                    backend=self.cryptography_backend
                )
        except Exception as e:
            raise PrivateKeyError(e)

    def _get_fingerprint(self):
        # Get bytes of public key
        private_key = self._load_privatekey()
        public_key = private_key.public_key()
        public_key_bytes = public_key.public_bytes(
            cryptography.hazmat.primitives.serialization.Encoding.DER,
            cryptography.hazmat.primitives.serialization.PublicFormat.SubjectPublicKeyInfo
        )
        # Get fingerprints of public_key_bytes
        return crypto_utils.get_fingerprint_of_bytes(public_key_bytes)

    def _check_passphrase(self):
        try:
            with open(self.path, 'rb') as f:
                return cryptography.hazmat.primitives.serialization.load_pem_private_key(
                    f.read(),
                    None if self.passphrase is None else to_bytes(self.passphrase),
                    backend=self.cryptography_backend
                )
            return True
        except Exception as dummy:
            return False

    def _check_size_and_type(self):
        privatekey = self._load_privatekey()

        if isinstance(privatekey, cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey):
            return self.type == 'RSA' and self.size == privatekey.key_size
        if isinstance(privatekey, cryptography.hazmat.primitives.asymmetric.dsa.DSAPrivateKey):
            return self.type == 'DSA' and self.size == privatekey.key_size
        if CRYPTOGRAPHY_HAS_X25519 and isinstance(privatekey, cryptography.hazmat.primitives.asymmetric.x25519.X25519PrivateKey):
            return self.type == 'X25519'
        if CRYPTOGRAPHY_HAS_X448 and isinstance(privatekey, cryptography.hazmat.primitives.asymmetric.x448.X448PrivateKey):
            return self.type == 'X448'
        if CRYPTOGRAPHY_HAS_ED25519 and isinstance(privatekey, cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PrivateKey):
            return self.type == 'Ed25519'
        if CRYPTOGRAPHY_HAS_ED448 and isinstance(privatekey, cryptography.hazmat.primitives.asymmetric.ed448.Ed448PrivateKey):
            return self.type == 'Ed448'
        if isinstance(privatekey, cryptography.hazmat.primitives.asymmetric.ec.EllipticCurvePrivateKey):
            if self.type != 'ECC':
                return False
            if self.curve not in self.curves:
                return False
            return self.curves[self.curve]['verify'](privatekey)

        return False

    def dump(self):
        """Serialize the object into a dictionary."""
        result = super(PrivateKeyCryptography, self).dump()
        result['type'] = self.type
        if self.type == 'ECC':
            result['curve'] = self.curve
        return result


def main():

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            size=dict(type='int', default=4096),
            type=dict(type='str', default='RSA', choices=[
                'DSA', 'ECC', 'Ed25519', 'Ed448', 'RSA', 'X25519', 'X448'
            ]),
            curve=dict(type='str', choices=[
                'secp384r1', 'secp521r1', 'secp224r1', 'secp192r1', 'secp256r1',
                'secp256k1', 'brainpoolP256r1', 'brainpoolP384r1', 'brainpoolP512r1',
                'sect571k1', 'sect409k1', 'sect283k1', 'sect233k1', 'sect163k1',
                'sect571r1', 'sect409r1', 'sect283r1', 'sect233r1', 'sect163r2',
            ]),
            force=dict(type='bool', default=False),
            path=dict(type='path', required=True),
            passphrase=dict(type='str', no_log=True),
            cipher=dict(type='str'),
            backup=dict(type='bool', default=False),
            select_crypto_backend=dict(type='str', choices=['auto', 'pyopenssl', 'cryptography'], default='auto'),
        ),
        supports_check_mode=True,
        add_file_common_args=True,
        required_together=[
            ['cipher', 'passphrase']
        ],
        required_if=[
            ['type', 'ECC', ['curve']],
        ],
    )

    base_dir = os.path.dirname(module.params['path']) or '.'
    if not os.path.isdir(base_dir):
        module.fail_json(
            name=base_dir,
            msg='The directory %s does not exist or the file is not a directory' % base_dir
        )

    backend = module.params['select_crypto_backend']
    if backend == 'auto':
        # Detection what is possible
        can_use_cryptography = CRYPTOGRAPHY_FOUND and CRYPTOGRAPHY_VERSION >= LooseVersion(MINIMAL_CRYPTOGRAPHY_VERSION)
        can_use_pyopenssl = PYOPENSSL_FOUND and PYOPENSSL_VERSION >= LooseVersion(MINIMAL_PYOPENSSL_VERSION)

        # Decision
        if module.params['cipher'] and module.params['passphrase'] and module.params['cipher'] != 'auto':
            # First try pyOpenSSL, then cryptography
            if can_use_pyopenssl:
                backend = 'pyopenssl'
            elif can_use_cryptography:
                backend = 'cryptography'
        else:
            # First try cryptography, then pyOpenSSL
            if can_use_cryptography:
                backend = 'cryptography'
            elif can_use_pyopenssl:
                backend = 'pyopenssl'

        # Success?
        if backend == 'auto':
            module.fail_json(msg=("Can't detect any of the required Python libraries "
                                  "cryptography (>= {0}) or PyOpenSSL (>= {1})").format(
                                      MINIMAL_CRYPTOGRAPHY_VERSION,
                                      MINIMAL_PYOPENSSL_VERSION))
    try:
        if backend == 'pyopenssl':
            if not PYOPENSSL_FOUND:
                module.fail_json(msg=missing_required_lib('pyOpenSSL >= {0}'.format(MINIMAL_PYOPENSSL_VERSION)),
                                 exception=PYOPENSSL_IMP_ERR)
            private_key = PrivateKeyPyOpenSSL(module)
        elif backend == 'cryptography':
            if not CRYPTOGRAPHY_FOUND:
                module.fail_json(msg=missing_required_lib('cryptography >= {0}'.format(MINIMAL_CRYPTOGRAPHY_VERSION)),
                                 exception=CRYPTOGRAPHY_IMP_ERR)
            private_key = PrivateKeyCryptography(module)

        if private_key.state == 'present':
            if module.check_mode:
                result = private_key.dump()
                result['changed'] = module.params['force'] or not private_key.check(module)
                module.exit_json(**result)

            private_key.generate(module)
        else:
            if module.check_mode:
                result = private_key.dump()
                result['changed'] = os.path.exists(module.params['path'])
                module.exit_json(**result)

            private_key.remove(module)

        result = private_key.dump()
        module.exit_json(**result)
    except crypto_utils.OpenSSLObjectError as exc:
        module.fail_json(msg=to_native(exc))


if __name__ == '__main__':
    main()
