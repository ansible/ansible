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
module: openssl_certificate
version_added: "2.4"
short_description: Generate and/or check OpenSSL certificates
description:
    - This module allows one to (re)generate OpenSSL certificates.
    - It implements a notion of provider (ie. C(selfsigned), C(ownca), C(acme), C(assertonly))
      for your certificate.
    - The C(assertonly) provider is intended for use cases where one is only interested in
      checking properties of a supplied certificate.
    - The C(ownca) provider is intended for generating OpenSSL certificate signed with your own
      CA (Certificate Authority) certificate (self-signed certificate).
    - Many properties that can be specified in this module are for validation of an
      existing or newly generated certificate. The proper place to specify them, if you
      want to receive a certificate with these properties is a CSR (Certificate Signing Request).
    - "Please note that the module regenerates existing certificate if it doesn't match the module's
      options, or if it seems to be corrupt. If you are concerned that this could overwrite
      your existing certificate, consider using the I(backup) option."
    - It uses the pyOpenSSL or cryptography python library to interact with OpenSSL.
    - If both the cryptography and PyOpenSSL libraries are available (and meet the minimum version requirements)
      cryptography will be preferred as a backend over PyOpenSSL (unless the backend is forced with C(select_crypto_backend))
requirements:
    - PyOpenSSL >= 0.15 or cryptography >= 1.6 (if using C(selfsigned) or C(assertonly) provider)
    - acme-tiny (if using the C(acme) provider)
author:
  - Yanis Guenane (@Spredzy)
  - Markus Teufelberger (@MarkusTeufelberger)
options:
    state:
        description:
            - Whether the certificate should exist or not, taking action if the state is different from what is stated.
        type: str
        default: present
        choices: [ absent, present ]

    path:
        description:
            - Remote absolute path where the generated certificate file should be created or is already located.
        type: path
        required: true

    provider:
        description:
            - Name of the provider to use to generate/retrieve the OpenSSL certificate.
            - The C(assertonly) provider will not generate files and fail if the certificate file is missing.
        type: str
        required: true
        choices: [ acme, assertonly, ownca, selfsigned ]

    force:
        description:
            - Generate the certificate, even if it already exists.
        type: bool
        default: no

    csr_path:
        description:
            - Path to the Certificate Signing Request (CSR) used to generate this certificate.
            - This is not required in C(assertonly) mode.
        type: path

    privatekey_path:
        description:
            - Path to the private key to use when signing the certificate.
        type: path

    privatekey_passphrase:
        description:
            - The passphrase for the I(privatekey_path).
            - This is required if the private key is password protected.
        type: str

    selfsigned_version:
        description:
            - Version of the C(selfsigned) certificate.
            - Nowadays it should almost always be C(3).
            - This is only used by the C(selfsigned) provider.
        type: int
        default: 3
        version_added: "2.5"

    selfsigned_digest:
        description:
            - Digest algorithm to be used when self-signing the certificate.
            - This is only used by the C(selfsigned) provider.
        type: str
        default: sha256

    selfsigned_not_before:
        description:
            - The point in time the certificate is valid from.
            - Time can be specified either as relative time or as absolute timestamp.
            - Time will always be interpreted as UTC.
            - Valid format is C([+-]timespec | ASN.1 TIME) where timespec can be an integer
              + C([w | d | h | m | s]) (e.g. C(+32w1d2h).
            - Note that if using relative time this module is NOT idempotent.
            - If this value is not specified, the certificate will start being valid from now.
            - This is only used by the C(selfsigned) provider.
        type: str
        default: +0s
        aliases: [ selfsigned_notBefore ]

    selfsigned_not_after:
        description:
            - The point in time at which the certificate stops being valid.
            - Time can be specified either as relative time or as absolute timestamp.
            - Time will always be interpreted as UTC.
            - Valid format is C([+-]timespec | ASN.1 TIME) where timespec can be an integer
              + C([w | d | h | m | s]) (e.g. C(+32w1d2h).
            - Note that if using relative time this module is NOT idempotent.
            - If this value is not specified, the certificate will stop being valid 10 years from now.
            - This is only used by the C(selfsigned) provider.
        type: str
        default: +3650d
        aliases: [ selfsigned_notAfter ]

    ownca_path:
        description:
            - Remote absolute path of the CA (Certificate Authority) certificate.
            - This is only used by the C(ownca) provider.
        type: path
        version_added: "2.7"

    ownca_privatekey_path:
        description:
            - Path to the CA (Certificate Authority) private key to use when signing the certificate.
            - This is only used by the C(ownca) provider.
        type: path
        version_added: "2.7"

    ownca_privatekey_passphrase:
        description:
            - The passphrase for the I(ownca_privatekey_path).
            - This is only used by the C(ownca) provider.
        type: str
        version_added: "2.7"

    ownca_digest:
        description:
            - The digest algorithm to be used for the C(ownca) certificate.
            - This is only used by the C(ownca) provider.
        type: str
        default: sha256
        version_added: "2.7"

    ownca_version:
        description:
            - The version of the C(ownca) certificate.
            - Nowadays it should almost always be C(3).
            - This is only used by the C(ownca) provider.
        type: int
        default: 3
        version_added: "2.7"

    ownca_not_before:
        description:
            - The point in time the certificate is valid from.
            - Time can be specified either as relative time or as absolute timestamp.
            - Time will always be interpreted as UTC.
            - Valid format is C([+-]timespec | ASN.1 TIME) where timespec can be an integer
              + C([w | d | h | m | s]) (e.g. C(+32w1d2h).
            - Note that if using relative time this module is NOT idempotent.
            - If this value is not specified, the certificate will start being valid from now.
            - This is only used by the C(ownca) provider.
        type: str
        default: +0s
        version_added: "2.7"

    ownca_not_after:
        description:
            - The point in time at which the certificate stops being valid.
            - Time can be specified either as relative time or as absolute timestamp.
            - Time will always be interpreted as UTC.
            - Valid format is C([+-]timespec | ASN.1 TIME) where timespec can be an integer
              + C([w | d | h | m | s]) (e.g. C(+32w1d2h).
            - Note that if using relative time this module is NOT idempotent.
            - If this value is not specified, the certificate will stop being valid 10 years from now.
            - This is only used by the C(ownca) provider.
        type: str
        default: +3650d
        version_added: "2.7"

    acme_accountkey_path:
        description:
            - The path to the accountkey for the C(acme) provider.
            - This is only used by the C(acme) provider.
        type: path

    acme_challenge_path:
        description:
            - The path to the ACME challenge directory that is served on U(http://<HOST>:80/.well-known/acme-challenge/)
            - This is only used by the C(acme) provider.
        type: path

    acme_chain:
        description:
            - Include the intermediate certificate to the generated certificate
            - This is only used by the C(acme) provider.
            - Note that this is only available for older versions of C(acme-tiny).
              New versions include the chain automatically, and setting I(acme_chain) to C(yes) results in an error.
        type: bool
        default: no
        version_added: "2.5"

    signature_algorithms:
        description:
            - A list of algorithms that you would accept the certificate to be signed with
              (e.g. ['sha256WithRSAEncryption', 'sha512WithRSAEncryption']).
            - This is only used by the C(assertonly) provider.
        type: list

    issuer:
        description:
            - The key/value pairs that must be present in the issuer name field of the certificate.
            - If you need to specify more than one value with the same key, use a list as value.
            - This is only used by the C(assertonly) provider.
        type: dict

    issuer_strict:
        description:
            - If set to C(yes), the I(issuer) field must contain only these values.
            - This is only used by the C(assertonly) provider.
        type: bool
        default: no
        version_added: "2.5"

    subject:
        description:
            - The key/value pairs that must be present in the subject name field of the certificate.
            - If you need to specify more than one value with the same key, use a list as value.
            - This is only used by the C(assertonly) provider.
        type: dict

    subject_strict:
        description:
            - If set to C(yes), the I(subject) field must contain only these values.
            - This is only used by the C(assertonly) provider.
        type: bool
        default: no
        version_added: "2.5"

    has_expired:
        description:
            - Checks if the certificate is expired/not expired at the time the module is executed.
            - This is only used by the C(assertonly) provider.
        type: bool
        default: no

    version:
        description:
            - The version of the certificate.
            - Nowadays it should almost always be 3.
            - This is only used by the C(assertonly) provider.
        type: int

    valid_at:
        description:
            - The certificate must be valid at this point in time.
            - The timestamp is formatted as an ASN.1 TIME.
            - This is only used by the C(assertonly) provider.
        type: str

    invalid_at:
        description:
            - The certificate must be invalid at this point in time.
            - The timestamp is formatted as an ASN.1 TIME.
            - This is only used by the C(assertonly) provider.
        type: str

    not_before:
        description:
            - The certificate must start to become valid at this point in time.
            - The timestamp is formatted as an ASN.1 TIME.
            - This is only used by the C(assertonly) provider.
        type: str
        aliases: [ notBefore ]

    not_after:
        description:
            - The certificate must expire at this point in time.
            - The timestamp is formatted as an ASN.1 TIME.
            - This is only used by the C(assertonly) provider.
        type: str
        aliases: [ notAfter ]


    valid_in:
        description:
            - The certificate must still be valid at this relative time offset from now.
            - Valid format is C([+-]timespec | number_of_seconds) where timespec can be an integer
              + C([w | d | h | m | s]) (e.g. C(+32w1d2h).
            - Note that if using this parameter, this module is NOT idempotent.
            - This is only used by the C(assertonly) provider.
        type: str

    key_usage:
        description:
            - The I(key_usage) extension field must contain all these values.
            - This is only used by the C(assertonly) provider.
        type: list
        aliases: [ keyUsage ]

    key_usage_strict:
        description:
            - If set to C(yes), the I(key_usage) extension field must contain only these values.
            - This is only used by the C(assertonly) provider.
        type: bool
        default: no
        aliases: [ keyUsage_strict ]

    extended_key_usage:
        description:
            - The I(extended_key_usage) extension field must contain all these values.
            - This is only used by the C(assertonly) provider.
        type: list
        aliases: [ extendedKeyUsage ]

    extended_key_usage_strict:
        description:
            - If set to C(yes), the I(extended_key_usage) extension field must contain only these values.
            - This is only used by the C(assertonly) provider.
        type: bool
        default: no
        aliases: [ extendedKeyUsage_strict ]

    subject_alt_name:
        description:
            - The I(subject_alt_name) extension field must contain these values.
            - This is only used by the C(assertonly) provider.
        type: list
        aliases: [ subjectAltName ]

    subject_alt_name_strict:
        description:
            - If set to C(yes), the I(subject_alt_name) extension field must contain only these values.
            - This is only used by the C(assertonly) provider.
        type: bool
        default: no
        aliases: [ subjectAltName_strict ]

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
            - Create a backup file including a timestamp so you can get the original
              certificate back if you overwrote it with a new one by accident.
            - This is not used by the C(assertonly) provider.
        type: bool
        default: no
        version_added: "2.8"

extends_documentation_fragment: files
notes:
    - All ASN.1 TIME values should be specified following the YYYYMMDDHHMMSSZ pattern.
    - Date specified should be UTC. Minutes and seconds are mandatory.
    - For security reason, when you use C(ownca) provider, you should NOT run M(openssl_certificate) on
      a target machine, but on a dedicated CA machine. It is recommended not to store the CA private key
      on the target machine. Once signed, the certificate can be moved to the target machine.
seealso:
- module: openssl_csr
- module: openssl_dhparam
- module: openssl_pkcs12
- module: openssl_privatekey
- module: openssl_publickey
'''

EXAMPLES = r'''
- name: Generate a Self Signed OpenSSL certificate
  openssl_certificate:
    path: /etc/ssl/crt/ansible.com.crt
    privatekey_path: /etc/ssl/private/ansible.com.pem
    csr_path: /etc/ssl/csr/ansible.com.csr
    provider: selfsigned

- name: Generate an OpenSSL certificate signed with your own CA certificate
  openssl_certificate:
    path: /etc/ssl/crt/ansible.com.crt
    csr_path: /etc/ssl/csr/ansible.com.csr
    ownca_path: /etc/ssl/crt/ansible_CA.crt
    ownca_privatekey_path: /etc/ssl/private/ansible_CA.pem
    provider: ownca

- name: Generate a Let's Encrypt Certificate
  openssl_certificate:
    path: /etc/ssl/crt/ansible.com.crt
    csr_path: /etc/ssl/csr/ansible.com.csr
    provider: acme
    acme_accountkey_path: /etc/ssl/private/ansible.com.pem
    acme_challenge_path: /etc/ssl/challenges/ansible.com/

- name: Force (re-)generate a new Let's Encrypt Certificate
  openssl_certificate:
    path: /etc/ssl/crt/ansible.com.crt
    csr_path: /etc/ssl/csr/ansible.com.csr
    provider: acme
    acme_accountkey_path: /etc/ssl/private/ansible.com.pem
    acme_challenge_path: /etc/ssl/challenges/ansible.com/
    force: yes

# Examples for some checks one could use the assertonly provider for:

# How to use the assertonly provider to implement and trigger your own custom certificate generation workflow:
- name: Check if a certificate is currently still valid, ignoring failures
  openssl_certificate:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    has_expired: no
  ignore_errors: yes
  register: validity_check

- name: Run custom task(s) to get a new, valid certificate in case the initial check failed
  command: superspecialSSL recreate /etc/ssl/crt/example.com.crt
  when: validity_check.failed

- name: Check the new certificate again for validity with the same parameters, this time failing the play if it is still invalid
  openssl_certificate:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    has_expired: no
  when: validity_check.failed

# Some other checks that assertonly could be used for:
- name: Verify that an existing certificate was issued by the Let's Encrypt CA and is currently still valid
  openssl_certificate:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    issuer:
      O: Let's Encrypt
    has_expired: no

- name: Ensure that a certificate uses a modern signature algorithm (no SHA1, MD5 or DSA)
  openssl_certificate:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    signature_algorithms:
      - sha224WithRSAEncryption
      - sha256WithRSAEncryption
      - sha384WithRSAEncryption
      - sha512WithRSAEncryption
      - sha224WithECDSAEncryption
      - sha256WithECDSAEncryption
      - sha384WithECDSAEncryption
      - sha512WithECDSAEncryption

- name: Ensure that the existing certificate belongs to the specified private key
  openssl_certificate:
    path: /etc/ssl/crt/example.com.crt
    privatekey_path: /etc/ssl/private/example.com.pem
    provider: assertonly

- name: Ensure that the existing certificate is still valid at the winter solstice 2017
  openssl_certificate:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    valid_at: 20171221162800Z

- name: Ensure that the existing certificate is still valid 2 weeks (1209600 seconds) from now
  openssl_certificate:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    valid_in: 1209600

- name: Ensure that the existing certificate is only used for digital signatures and encrypting other keys
  openssl_certificate:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    key_usage:
      - digitalSignature
      - keyEncipherment
    key_usage_strict: true

- name: Ensure that the existing certificate can be used for client authentication
  openssl_certificate:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    extended_key_usage:
      - clientAuth

- name: Ensure that the existing certificate can only be used for client authentication and time stamping
  openssl_certificate:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    extended_key_usage:
      - clientAuth
      - 1.3.6.1.5.5.7.3.8
    extended_key_usage_strict: true

- name: Ensure that the existing certificate has a certain domain in its subjectAltName
  openssl_certificate:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    subject_alt_name:
      - www.example.com
      - test.example.com
'''

RETURN = r'''
filename:
    description: Path to the generated Certificate
    returned: changed or success
    type: str
    sample: /etc/ssl/crt/www.ansible.com.crt
backup_file:
    description: Name of backup file created.
    returned: changed and if I(backup) is C(yes)
    type: str
    sample: /path/to/www.ansible.com.crt.2019-03-09@11:22~
'''


from random import randint
import abc
import datetime
import os
import traceback
from distutils.version import LooseVersion

from ansible.module_utils import crypto as crypto_utils
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native, to_bytes, to_text
from ansible.module_utils.compat import ipaddress as compat_ipaddress

MINIMAL_CRYPTOGRAPHY_VERSION = '1.6'
MINIMAL_PYOPENSSL_VERSION = '0.15'

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
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.serialization import Encoding
    from cryptography.x509 import NameAttribute, Name
    CRYPTOGRAPHY_VERSION = LooseVersion(cryptography.__version__)
except ImportError:
    CRYPTOGRAPHY_IMP_ERR = traceback.format_exc()
    CRYPTOGRAPHY_FOUND = False
else:
    CRYPTOGRAPHY_FOUND = True


class CertificateError(crypto_utils.OpenSSLObjectError):
    pass


class Certificate(crypto_utils.OpenSSLObject):

    def __init__(self, module, backend):
        super(Certificate, self).__init__(
            module.params['path'],
            module.params['state'],
            module.params['force'],
            module.check_mode
        )

        self.provider = module.params['provider']
        self.privatekey_path = module.params['privatekey_path']
        self.privatekey_passphrase = module.params['privatekey_passphrase']
        self.csr_path = module.params['csr_path']
        self.cert = None
        self.privatekey = None
        self.csr = None
        self.backend = backend
        self.module = module

        self.backup = module.params['backup']
        self.backup_file = None

    def get_relative_time_option(self, input_string, input_name):
        """Return an ASN1 formatted string if a relative timespec
           or an ASN1 formatted string is provided."""
        result = input_string
        if result.startswith("+") or result.startswith("-"):
            result_datetime = crypto_utils.convert_relative_to_datetime(
                result)
            if self.backend == 'pyopenssl':
                return result_datetime.strftime("%Y%m%d%H%M%SZ")
            elif self.backend == 'cryptography':
                return result_datetime
        if result is None:
            raise CertificateError(
                'The timespec "%s" for %s is not valid' %
                input_string, input_name)
        if self.backend == 'cryptography':
            for date_fmt in ['%Y%m%d%H%M%SZ', '%Y%m%d%H%MZ', '%Y%m%d%H%M%S%z', '%Y%m%d%H%M%z']:
                try:
                    result = datetime.datetime.strptime(input_string, date_fmt)
                    break
                except ValueError:
                    pass

            if not isinstance(result, datetime.datetime):
                raise CertificateError(
                    'The time spec "%s" for %s is invalid' %
                    (input_string, input_name)
                )
        return result

    def _validate_privatekey(self):
        if self.backend == 'pyopenssl':
            ctx = OpenSSL.SSL.Context(OpenSSL.SSL.TLSv1_2_METHOD)
            ctx.use_privatekey(self.privatekey)
            ctx.use_certificate(self.cert)
            try:
                ctx.check_privatekey()
                return True
            except OpenSSL.SSL.Error:
                return False
        elif self.backend == 'cryptography':
            return crypto_utils.cryptography_compare_public_keys(self.cert.public_key(), self.privatekey.public_key())

    def _validate_csr(self):
        if self.backend == 'pyopenssl':
            # Verify that CSR is signed by certificate's private key
            try:
                self.csr.verify(self.cert.get_pubkey())
            except OpenSSL.crypto.Error:
                return False
            # Check subject
            if self.csr.get_subject() != self.cert.get_subject():
                return False
            # Check extensions
            csr_extensions = self.csr.get_extensions()
            cert_extension_count = self.cert.get_extension_count()
            if len(csr_extensions) != cert_extension_count:
                return False
            for extension_number in range(0, cert_extension_count):
                cert_extension = self.cert.get_extension(extension_number)
                csr_extension = filter(lambda extension: extension.get_short_name() == cert_extension.get_short_name(), csr_extensions)
                if cert_extension.get_data() != list(csr_extension)[0].get_data():
                    return False
            return True
        elif self.backend == 'cryptography':
            # Verify that CSR is signed by certificate's private key
            if not self.csr.is_signature_valid:
                return False
            if not crypto_utils.cryptography_compare_public_keys(self.csr.public_key(), self.cert.public_key()):
                return False
            # Check subject
            if self.csr.subject != self.cert.subject:
                return False
            # Check extensions
            cert_exts = self.cert.extensions
            csr_exts = self.csr.extensions
            if len(cert_exts) != len(csr_exts):
                return False
            for cert_ext in cert_exts:
                try:
                    csr_ext = csr_exts.get_extension_for_oid(cert_ext.oid)
                    if cert_ext != csr_ext:
                        return False
                except cryptography.x509.ExtensionNotFound as dummy:
                    return False
            return True

    def remove(self, module):
        if self.backup:
            self.backup_file = module.backup_local(self.path)
        super(Certificate, self).remove(module)

    def check(self, module, perms_required=True):
        """Ensure the resource is in its desired state."""

        state_and_perms = super(Certificate, self).check(module, perms_required)

        if not state_and_perms:
            return False

        try:
            self.cert = crypto_utils.load_certificate(self.path, backend=self.backend)
        except Exception as dummy:
            return False

        if self.privatekey_path:
            try:
                self.privatekey = crypto_utils.load_privatekey(
                    self.privatekey_path,
                    self.privatekey_passphrase,
                    backend=self.backend
                )
            except crypto_utils.OpenSSLBadPassphraseError as exc:
                raise CertificateError(exc)
            if not self._validate_privatekey():
                return False

        if self.csr_path:
            self.csr = crypto_utils.load_certificate_request(self.csr_path, backend=self.backend)
            if not self._validate_csr():
                return False

        return True


class CertificateAbsent(Certificate):
    def __init__(self, module):
        super(CertificateAbsent, self).__init__(module, 'cryptography')  # backend doesn't matter

    def generate(self, module):
        pass

    def dump(self, check_mode=False):
        # Use only for absent

        result = {
            'changed': self.changed,
            'filename': self.path,
            'privatekey': self.privatekey_path,
            'csr': self.csr_path
        }
        if self.backup_file:
            result['backup_file'] = self.backup_file

        return result


class SelfSignedCertificateCryptography(Certificate):
    """Generate the self-signed certificate, using the cryptography backend"""
    def __init__(self, module):
        super(SelfSignedCertificateCryptography, self).__init__(module, 'cryptography')
        self.notBefore = self.get_relative_time_option(module.params['selfsigned_not_before'], 'selfsigned_not_before')
        self.notAfter = self.get_relative_time_option(module.params['selfsigned_not_after'], 'selfsigned_not_after')
        self.digest = crypto_utils.select_message_digest(module.params['selfsigned_digest'])
        self.version = module.params['selfsigned_version']
        self.serial_number = x509.random_serial_number()
        self.csr = crypto_utils.load_certificate_request(self.csr_path, backend=self.backend)
        self._module = module

        try:
            self.privatekey = crypto_utils.load_privatekey(
                self.privatekey_path, self.privatekey_passphrase, backend=self.backend
            )
        except crypto_utils.OpenSSLBadPassphraseError as exc:
            module.fail_json(msg=to_native(exc))

        if crypto_utils.cryptography_key_needs_digest_for_signing(self.privatekey):
            if self.digest is None:
                raise CertificateError(
                    'The digest %s is not supported with the cryptography backend' % module.params['selfsigned_digest']
                )
        else:
            self.digest = None

    def generate(self, module):
        if not os.path.exists(self.privatekey_path):
            raise CertificateError(
                'The private key %s does not exist' % self.privatekey_path
            )
        if not os.path.exists(self.csr_path):
            raise CertificateError(
                'The certificate signing request file %s does not exist' % self.csr_path
            )
        if not self.check(module, perms_required=False) or self.force:
            try:
                cert_builder = x509.CertificateBuilder()
                cert_builder = cert_builder.subject_name(self.csr.subject)
                cert_builder = cert_builder.issuer_name(self.csr.subject)
                cert_builder = cert_builder.serial_number(self.serial_number)
                cert_builder = cert_builder.not_valid_before(self.notBefore)
                cert_builder = cert_builder.not_valid_after(self.notAfter)
                cert_builder = cert_builder.public_key(self.privatekey.public_key())
                for extension in self.csr.extensions:
                    cert_builder = cert_builder.add_extension(extension.value, critical=extension.critical)
            except ValueError as e:
                raise CertificateError(str(e))

            try:
                certificate = cert_builder.sign(
                    private_key=self.privatekey, algorithm=self.digest,
                    backend=default_backend()
                )
            except TypeError as e:
                if str(e) == 'Algorithm must be a registered hash algorithm.' and self.digest is None:
                    module.fail_json(msg='Signing with Ed25519 and Ed448 keys requires cryptography 2.8 or newer.')
                raise

            self.cert = certificate

            if self.backup:
                self.backup_file = module.backup_local(self.path)
            crypto_utils.write_file(module, certificate.public_bytes(Encoding.PEM))
            self.changed = True
        else:
            self.cert = crypto_utils.load_certificate(self.path, backend=self.backend)

        file_args = module.load_file_common_arguments(module.params)
        if module.set_fs_attributes_if_different(file_args, False):
            self.changed = True

    def dump(self, check_mode=False):

        result = {
            'changed': self.changed,
            'filename': self.path,
            'privatekey': self.privatekey_path,
            'csr': self.csr_path
        }
        if self.backup_file:
            result['backup_file'] = self.backup_file

        if check_mode:
            result.update({
                'notBefore': self.notBefore.strftime("%Y%m%d%H%M%SZ"),
                'notAfter': self.notAfter.strftime("%Y%m%d%H%M%SZ"),
                'serial_number': self.serial_number,
            })
        else:
            result.update({
                'notBefore': self.cert.not_valid_before.strftime("%Y%m%d%H%M%SZ"),
                'notAfter': self.cert.not_valid_after.strftime("%Y%m%d%H%M%SZ"),
                'serial_number': self.cert.serial_number,
            })

        return result


class SelfSignedCertificate(Certificate):
    """Generate the self-signed certificate."""

    def __init__(self, module):
        super(SelfSignedCertificate, self).__init__(module, 'pyopenssl')
        self.notBefore = self.get_relative_time_option(module.params['selfsigned_not_before'], 'selfsigned_not_before')
        self.notAfter = self.get_relative_time_option(module.params['selfsigned_not_after'], 'selfsigned_not_after')
        self.digest = module.params['selfsigned_digest']
        self.version = module.params['selfsigned_version']
        self.serial_number = randint(1000, 99999)
        self.csr = crypto_utils.load_certificate_request(self.csr_path)
        try:
            self.privatekey = crypto_utils.load_privatekey(
                self.privatekey_path, self.privatekey_passphrase
            )
        except crypto_utils.OpenSSLBadPassphraseError as exc:
            module.fail_json(msg=str(exc))

    def generate(self, module):

        if not os.path.exists(self.privatekey_path):
            raise CertificateError(
                'The private key %s does not exist' % self.privatekey_path
            )

        if not os.path.exists(self.csr_path):
            raise CertificateError(
                'The certificate signing request file %s does not exist' % self.csr_path
            )

        if not self.check(module, perms_required=False) or self.force:
            cert = crypto.X509()
            cert.set_serial_number(self.serial_number)
            cert.set_notBefore(to_bytes(self.notBefore))
            cert.set_notAfter(to_bytes(self.notAfter))
            cert.set_subject(self.csr.get_subject())
            cert.set_issuer(self.csr.get_subject())
            cert.set_version(self.version - 1)
            cert.set_pubkey(self.csr.get_pubkey())
            cert.add_extensions(self.csr.get_extensions())

            cert.sign(self.privatekey, self.digest)
            self.cert = cert

            if self.backup:
                self.backup_file = module.backup_local(self.path)
            crypto_utils.write_file(module, crypto.dump_certificate(crypto.FILETYPE_PEM, self.cert))
            self.changed = True

        file_args = module.load_file_common_arguments(module.params)
        if module.set_fs_attributes_if_different(file_args, False):
            self.changed = True

    def dump(self, check_mode=False):

        result = {
            'changed': self.changed,
            'filename': self.path,
            'privatekey': self.privatekey_path,
            'csr': self.csr_path
        }
        if self.backup_file:
            result['backup_file'] = self.backup_file

        if check_mode:
            result.update({
                'notBefore': self.notBefore,
                'notAfter': self.notAfter,
                'serial_number': self.serial_number,
            })
        else:
            result.update({
                'notBefore': self.cert.get_notBefore(),
                'notAfter': self.cert.get_notAfter(),
                'serial_number': self.cert.get_serial_number(),
            })

        return result


class OwnCACertificateCryptography(Certificate):
    """Generate the own CA certificate. Using the cryptography backend"""
    def __init__(self, module):
        super(OwnCACertificateCryptography, self).__init__(module, 'cryptography')
        self.notBefore = self.get_relative_time_option(module.params['ownca_not_before'], 'ownca_not_before')
        self.notAfter = self.get_relative_time_option(module.params['ownca_not_after'], 'ownca_not_after')
        self.digest = crypto_utils.select_message_digest(module.params['ownca_digest'])
        self.version = module.params['ownca_version']
        self.serial_number = x509.random_serial_number()
        self.ca_cert_path = module.params['ownca_path']
        self.ca_privatekey_path = module.params['ownca_privatekey_path']
        self.ca_privatekey_passphrase = module.params['ownca_privatekey_passphrase']
        self.csr = crypto_utils.load_certificate_request(self.csr_path, backend=self.backend)
        self.ca_cert = crypto_utils.load_certificate(self.ca_cert_path, backend=self.backend)
        try:
            self.ca_private_key = crypto_utils.load_privatekey(
                self.ca_privatekey_path, self.ca_privatekey_passphrase, backend=self.backend
            )
        except crypto_utils.OpenSSLBadPassphraseError as exc:
            module.fail_json(msg=str(exc))

        if crypto_utils.cryptography_key_needs_digest_for_signing(self.ca_private_key):
            if self.digest is None:
                raise CertificateError(
                    'The digest %s is not supported with the cryptography backend' % module.params['ownca_digest']
                )
        else:
            self.digest = None

    def generate(self, module):

        if not os.path.exists(self.ca_cert_path):
            raise CertificateError(
                'The CA certificate %s does not exist' % self.ca_cert_path
            )

        if not os.path.exists(self.ca_privatekey_path):
            raise CertificateError(
                'The CA private key %s does not exist' % self.ca_privatekey_path
            )

        if not os.path.exists(self.csr_path):
            raise CertificateError(
                'The certificate signing request file %s does not exist' % self.csr_path
            )

        if not self.check(module, perms_required=False) or self.force:
            cert_builder = x509.CertificateBuilder()
            cert_builder = cert_builder.subject_name(self.csr.subject)
            cert_builder = cert_builder.issuer_name(self.ca_cert.subject)
            cert_builder = cert_builder.serial_number(self.serial_number)
            cert_builder = cert_builder.not_valid_before(self.notBefore)
            cert_builder = cert_builder.not_valid_after(self.notAfter)
            cert_builder = cert_builder.public_key(self.csr.public_key())
            for extension in self.csr.extensions:
                cert_builder = cert_builder.add_extension(extension.value, critical=extension.critical)

            try:
                certificate = cert_builder.sign(
                    private_key=self.ca_private_key, algorithm=self.digest,
                    backend=default_backend()
                )
            except TypeError as e:
                if str(e) == 'Algorithm must be a registered hash algorithm.' and self.digest is None:
                    module.fail_json(msg='Signing with Ed25519 and Ed448 keys requires cryptography 2.8 or newer.')
                raise

            self.cert = certificate

            if self.backup:
                self.backup_file = module.backup_local(self.path)
            crypto_utils.write_file(module, certificate.public_bytes(Encoding.PEM))
            self.changed = True
        else:
            self.cert = crypto_utils.load_certificate(self.path, backend=self.backend)

        file_args = module.load_file_common_arguments(module.params)
        if module.set_fs_attributes_if_different(file_args, False):
            self.changed = True

    def dump(self, check_mode=False):

        result = {
            'changed': self.changed,
            'filename': self.path,
            'privatekey': self.privatekey_path,
            'csr': self.csr_path,
            'ca_cert': self.ca_cert_path,
            'ca_privatekey': self.ca_privatekey_path
        }
        if self.backup_file:
            result['backup_file'] = self.backup_file

        if check_mode:
            result.update({
                'notBefore': self.notBefore.strftime("%Y%m%d%H%M%SZ"),
                'notAfter': self.notAfter.strftime("%Y%m%d%H%M%SZ"),
                'serial_number': self.serial_number,
            })
        else:
            result.update({
                'notBefore': self.cert.not_valid_before.strftime("%Y%m%d%H%M%SZ"),
                'notAfter': self.cert.not_valid_after.strftime("%Y%m%d%H%M%SZ"),
                'serial_number': self.cert.serial_number,
            })

        return result


class OwnCACertificate(Certificate):
    """Generate the own CA certificate."""

    def __init__(self, module):
        super(OwnCACertificate, self).__init__(module, 'pyopenssl')
        self.notBefore = self.get_relative_time_option(module.params['ownca_not_before'], 'ownca_not_before')
        self.notAfter = self.get_relative_time_option(module.params['ownca_not_after'], 'ownca_not_after')
        self.digest = module.params['ownca_digest']
        self.version = module.params['ownca_version']
        self.serial_number = randint(1000, 99999)
        self.ca_cert_path = module.params['ownca_path']
        self.ca_privatekey_path = module.params['ownca_privatekey_path']
        self.ca_privatekey_passphrase = module.params['ownca_privatekey_passphrase']
        self.csr = crypto_utils.load_certificate_request(self.csr_path)
        self.ca_cert = crypto_utils.load_certificate(self.ca_cert_path)
        try:
            self.ca_privatekey = crypto_utils.load_privatekey(
                self.ca_privatekey_path, self.ca_privatekey_passphrase
            )
        except crypto_utils.OpenSSLBadPassphraseError as exc:
            module.fail_json(msg=str(exc))

    def generate(self, module):

        if not os.path.exists(self.ca_cert_path):
            raise CertificateError(
                'The CA certificate %s does not exist' % self.ca_cert_path
            )

        if not os.path.exists(self.ca_privatekey_path):
            raise CertificateError(
                'The CA private key %s does not exist' % self.ca_privatekey_path
            )

        if not os.path.exists(self.csr_path):
            raise CertificateError(
                'The certificate signing request file %s does not exist' % self.csr_path
            )

        if not self.check(module, perms_required=False) or self.force:
            cert = crypto.X509()
            cert.set_serial_number(self.serial_number)
            cert.set_notBefore(to_bytes(self.notBefore))
            cert.set_notAfter(to_bytes(self.notAfter))
            cert.set_subject(self.csr.get_subject())
            cert.set_issuer(self.ca_cert.get_subject())
            cert.set_version(self.version - 1)
            cert.set_pubkey(self.csr.get_pubkey())
            cert.add_extensions(self.csr.get_extensions())

            cert.sign(self.ca_privatekey, self.digest)
            self.cert = cert

            if self.backup:
                self.backup_file = module.backup_local(self.path)
            crypto_utils.write_file(module, crypto.dump_certificate(crypto.FILETYPE_PEM, self.cert))
            self.changed = True

        file_args = module.load_file_common_arguments(module.params)
        if module.set_fs_attributes_if_different(file_args, False):
            self.changed = True

    def dump(self, check_mode=False):

        result = {
            'changed': self.changed,
            'filename': self.path,
            'privatekey': self.privatekey_path,
            'csr': self.csr_path,
            'ca_cert': self.ca_cert_path,
            'ca_privatekey': self.ca_privatekey_path
        }
        if self.backup_file:
            result['backup_file'] = self.backup_file

        if check_mode:
            result.update({
                'notBefore': self.notBefore,
                'notAfter': self.notAfter,
                'serial_number': self.serial_number,
            })
        else:
            result.update({
                'notBefore': self.cert.get_notBefore(),
                'notAfter': self.cert.get_notAfter(),
                'serial_number': self.cert.get_serial_number(),
            })

        return result


def compare_sets(subset, superset, equality=False):
    if equality:
        return set(subset) == set(superset)
    else:
        return all(x in superset for x in subset)


def compare_dicts(subset, superset, equality=False):
    if equality:
        return subset == superset
    else:
        return all(superset.get(x) == v for x, v in subset.items())


NO_EXTENSION = 'no extension'


class AssertOnlyCertificateBase(Certificate):

    def __init__(self, module, backend):
        super(AssertOnlyCertificateBase, self).__init__(module, backend)

        self.signature_algorithms = module.params['signature_algorithms']
        if module.params['subject']:
            self.subject = crypto_utils.parse_name_field(module.params['subject'])
        else:
            self.subject = []
        self.subject_strict = module.params['subject_strict']
        if module.params['issuer']:
            self.issuer = crypto_utils.parse_name_field(module.params['issuer'])
        else:
            self.issuer = []
        self.issuer_strict = module.params['issuer_strict']
        self.has_expired = module.params['has_expired']
        self.version = module.params['version']
        self.key_usage = module.params['key_usage']
        self.key_usage_strict = module.params['key_usage_strict']
        self.extended_key_usage = module.params['extended_key_usage']
        self.extended_key_usage_strict = module.params['extended_key_usage_strict']
        self.subject_alt_name = module.params['subject_alt_name']
        self.subject_alt_name_strict = module.params['subject_alt_name_strict']
        self.not_before = module.params['not_before']
        self.not_after = module.params['not_after']
        self.valid_at = module.params['valid_at']
        self.invalid_at = module.params['invalid_at']
        self.valid_in = module.params['valid_in']
        if self.valid_in and not self.valid_in.startswith("+") and not self.valid_in.startswith("-"):
            try:
                int(self.valid_in)
            except ValueError:
                module.fail_json(msg='The supplied value for "valid_in" (%s) is not an integer or a valid timespec' % self.valid_in)
            self.valid_in = "+" + self.valid_in + "s"

        # Load objects
        self.cert = crypto_utils.load_certificate(self.path, backend=self.backend)
        if self.privatekey_path is not None:
            try:
                self.privatekey = crypto_utils.load_privatekey(
                    self.privatekey_path,
                    self.privatekey_passphrase,
                    backend=self.backend
                )
            except crypto_utils.OpenSSLBadPassphraseError as exc:
                raise CertificateError(exc)
        if self.csr_path is not None:
            self.csr = crypto_utils.load_certificate_request(self.csr_path, backend=self.backend)

    @abc.abstractmethod
    def _validate_privatekey(self):
        pass

    @abc.abstractmethod
    def _validate_csr_signature(self):
        pass

    @abc.abstractmethod
    def _validate_csr_subject(self):
        pass

    @abc.abstractmethod
    def _validate_csr_extensions(self):
        pass

    @abc.abstractmethod
    def _validate_signature_algorithms(self):
        pass

    @abc.abstractmethod
    def _validate_subject(self):
        pass

    @abc.abstractmethod
    def _validate_issuer(self):
        pass

    @abc.abstractmethod
    def _validate_has_expired(self):
        pass

    @abc.abstractmethod
    def _validate_version(self):
        pass

    @abc.abstractmethod
    def _validate_key_usage(self):
        pass

    @abc.abstractmethod
    def _validate_extended_key_usage(self):
        pass

    @abc.abstractmethod
    def _validate_subject_alt_name(self):
        pass

    @abc.abstractmethod
    def _validate_not_before(self):
        pass

    @abc.abstractmethod
    def _validate_not_after(self):
        pass

    @abc.abstractmethod
    def _validate_valid_at(self):
        pass

    @abc.abstractmethod
    def _validate_invalid_at(self):
        pass

    @abc.abstractmethod
    def _validate_valid_in(self):
        pass

    def assertonly(self, module):
        messages = []
        if self.privatekey_path is not None:
            if not self._validate_privatekey():
                messages.append(
                    'Certificate %s and private key %s do not match' %
                    (self.path, self.privatekey_path)
                )

        if self.csr_path is not None:
            if not self._validate_csr_signature():
                messages.append(
                    'Certificate %s and CSR %s do not match: private key mismatch' %
                    (self.path, self.csr_path)
                )
            if not self._validate_csr_subject():
                messages.append(
                    'Certificate %s and CSR %s do not match: subject mismatch' %
                    (self.path, self.csr_path)
                )
            if not self._validate_csr_extensions():
                messages.append(
                    'Certificate %s and CSR %s do not match: extensions mismatch' %
                    (self.path, self.csr_path)
                )

        if self.signature_algorithms is not None:
            wrong_alg = self._validate_signature_algorithms()
            if wrong_alg:
                messages.append(
                    'Invalid signature algorithm (got %s, expected one of %s)' %
                    (wrong_alg, self.signature_algorithms)
                )

        if self.subject is not None:
            failure = self._validate_subject()
            if failure:
                dummy, cert_subject = failure
                messages.append(
                    'Invalid subject component (got %s, expected all of %s to be present)' %
                    (cert_subject, self.subject)
                )

        if self.issuer is not None:
            failure = self._validate_issuer()
            if failure:
                dummy, cert_issuer = failure
                messages.append(
                    'Invalid issuer component (got %s, expected all of %s to be present)' % (cert_issuer, self.issuer)
                )

        if self.has_expired is not None:
            cert_expired = self._validate_has_expired()
            if cert_expired != self.has_expired:
                messages.append(
                    'Certificate expiration check failed (certificate expiration is %s, expected %s)' %
                    (cert_expired, self.has_expired)
                )

        if self.version is not None:
            cert_version = self._validate_version()
            if cert_version != self.version:
                messages.append(
                    'Invalid certificate version number (got %s, expected %s)' %
                    (cert_version, self.version)
                )

        if self.key_usage is not None:
            failure = self._validate_key_usage()
            if failure == NO_EXTENSION:
                messages.append('Found no keyUsage extension')
            elif failure:
                dummy, cert_key_usage = failure
                messages.append(
                    'Invalid keyUsage components (got %s, expected all of %s to be present)' %
                    (cert_key_usage, self.key_usage)
                )

        if self.extended_key_usage is not None:
            failure = self._validate_extended_key_usage()
            if failure == NO_EXTENSION:
                messages.append('Found no extendedKeyUsage extension')
            elif failure:
                dummy, ext_cert_key_usage = failure
                messages.append(
                    'Invalid extendedKeyUsage component (got %s, expected all of %s to be present)' % (ext_cert_key_usage, self.extended_key_usage)
                )

        if self.subject_alt_name is not None:
            failure = self._validate_subject_alt_name()
            if failure == NO_EXTENSION:
                messages.append('Found no subjectAltName extension')
            elif failure:
                dummy, cert_san = failure
                messages.append(
                    'Invalid subjectAltName component (got %s, expected all of %s to be present)' %
                    (cert_san, self.subject_alt_name)
                )

        if self.not_before is not None:
            cert_not_valid_before = self._validate_not_before()
            if cert_not_valid_before != self.get_relative_time_option(self.not_before, 'not_before'):
                messages.append(
                    'Invalid not_before component (got %s, expected %s to be present)' %
                    (cert_not_valid_before, self.not_before)
                )

        if self.not_after is not None:
            cert_not_valid_after = self._validate_not_after()
            if cert_not_valid_after != self.get_relative_time_option(self.not_after, 'not_after'):
                messages.append(
                    'Invalid not_after component (got %s, expected %s to be present)' %
                    (cert_not_valid_after, self.not_after)
                )

        if self.valid_at is not None:
            not_before, valid_at, not_after = self._validate_valid_at()
            if not (not_before <= valid_at <= not_after):
                messages.append(
                    'Certificate is not valid for the specified date (%s) - not_before: %s - not_after: %s' %
                    (self.valid_at, not_before, not_after)
                )

        if self.invalid_at is not None:
            not_before, invalid_at, not_after = self._validate_invalid_at()
            if (invalid_at <= not_before) or (invalid_at >= not_after):
                messages.append(
                    'Certificate is not invalid for the specified date (%s) - not_before: %s - not_after: %s' %
                    (self.invalid_at, not_before, not_after)
                )

        if self.valid_in is not None:
            not_before, valid_in, not_after = self._validate_valid_in()
            if not not_before <= valid_in <= not_after:
                messages.append(
                    'Certificate is not valid in %s from now (that would be %s) - not_before: %s - not_after: %s' %
                    (self.valid_in, valid_in, not_before, not_after)
                )
        return messages

    def generate(self, module):
        """Don't generate anything - only assert"""
        messages = self.assertonly(module)
        if messages:
            module.fail_json(msg=' | '.join(messages))

    def check(self, module, perms_required=False):
        """Ensure the resource is in its desired state."""
        messages = self.assertonly(module)
        return len(messages) == 0

    def dump(self, check_mode=False):
        result = {
            'changed': self.changed,
            'filename': self.path,
            'privatekey': self.privatekey_path,
            'csr': self.csr_path,
        }
        return result


class AssertOnlyCertificateCryptography(AssertOnlyCertificateBase):
    """Validate the supplied cert, using the cryptography backend"""
    def __init__(self, module):
        super(AssertOnlyCertificateCryptography, self).__init__(module, 'cryptography')

    def _validate_privatekey(self):
        return crypto_utils.cryptography_compare_public_keys(self.cert.public_key(), self.privatekey.public_key())

    def _validate_csr_signature(self):
        if not self.csr.is_signature_valid:
            return False
        return crypto_utils.cryptography_compare_public_keys(self.csr.public_key(), self.cert.public_key())

    def _validate_csr_subject(self):
        return self.csr.subject == self.cert.subject

    def _validate_csr_extensions(self):
        cert_exts = self.cert.extensions
        csr_exts = self.csr.extensions
        if len(cert_exts) != len(csr_exts):
            return False
        for cert_ext in cert_exts:
            try:
                csr_ext = csr_exts.get_extension_for_oid(cert_ext.oid)
                if cert_ext != csr_ext:
                    return False
            except cryptography.x509.ExtensionNotFound as dummy:
                return False
        return True

    def _validate_signature_algorithms(self):
        if self.cert.signature_algorithm_oid._name not in self.signature_algorithms:
            return self.cert.signature_algorithm_oid._name

    def _validate_subject(self):
        expected_subject = Name([NameAttribute(oid=crypto_utils.cryptography_name_to_oid(sub[0]), value=to_text(sub[1]))
                                 for sub in self.subject])
        cert_subject = self.cert.subject
        if not compare_sets(expected_subject, cert_subject, self.subject_strict):
            return expected_subject, cert_subject

    def _validate_issuer(self):
        expected_issuer = Name([NameAttribute(oid=crypto_utils.cryptography_name_to_oid(iss[0]), value=to_text(iss[1]))
                                for iss in self.issuer])
        cert_issuer = self.cert.issuer
        if not compare_sets(expected_issuer, cert_issuer, self.issuer_strict):
            return self.issuer, cert_issuer

    def _validate_has_expired(self):
        cert_not_after = self.cert.not_valid_after
        cert_expired = cert_not_after < datetime.datetime.utcnow()
        return cert_expired

    def _validate_version(self):
        if self.cert.version == x509.Version.v1:
            return 1
        if self.cert.version == x509.Version.v3:
            return 3
        return "unknown"

    def _validate_key_usage(self):
        try:
            current_key_usage = self.cert.extensions.get_extension_for_class(x509.KeyUsage).value
            test_key_usage = dict(
                digital_signature=current_key_usage.digital_signature,
                content_commitment=current_key_usage.content_commitment,
                key_encipherment=current_key_usage.key_encipherment,
                data_encipherment=current_key_usage.data_encipherment,
                key_agreement=current_key_usage.key_agreement,
                key_cert_sign=current_key_usage.key_cert_sign,
                crl_sign=current_key_usage.crl_sign,
                encipher_only=False,
                decipher_only=False
            )
            if test_key_usage['key_agreement']:
                test_key_usage.update(dict(
                    encipher_only=current_key_usage.encipher_only,
                    decipher_only=current_key_usage.decipher_only
                ))

            key_usages = crypto_utils.cryptography_parse_key_usage_params(self.key_usage)
            if not compare_dicts(key_usages, test_key_usage, self.key_usage_strict):
                return self.key_usage, [x for x in test_key_usage if x is True]

        except cryptography.x509.ExtensionNotFound:
            # This is only bad if the user specified a non-empty list
            if self.key_usage:
                return NO_EXTENSION

    def _validate_extended_key_usage(self):
        try:
            current_ext_keyusage = self.cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
            usages = [crypto_utils.cryptography_name_to_oid(usage) for usage in self.extended_key_usage]
            expected_ext_keyusage = x509.ExtendedKeyUsage(usages)
            if not compare_sets(expected_ext_keyusage, current_ext_keyusage, self.extended_key_usage_strict):
                return [eku.value for eku in expected_ext_keyusage], [eku.value for eku in current_ext_keyusage]

        except cryptography.x509.ExtensionNotFound:
            # This is only bad if the user specified a non-empty list
            if self.extended_key_usage:
                return NO_EXTENSION

    def _validate_subject_alt_name(self):
        try:
            current_san = self.cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
            expected_san = [crypto_utils.cryptography_get_name(san) for san in self.subject_alt_name]
            if not compare_sets(expected_san, current_san, self.subject_alt_name_strict):
                return self.subject_alt_name, current_san
        except cryptography.x509.ExtensionNotFound:
            # This is only bad if the user specified a non-empty list
            if self.subject_alt_name:
                return NO_EXTENSION

    def _validate_not_before(self):
        return self.cert.not_valid_before

    def _validate_not_after(self):
        return self.cert.not_valid_after

    def _validate_valid_at(self):
        rt = self.get_relative_time_option(self.valid_at, 'valid_at')
        return self.cert.not_valid_before, rt, self.cert.not_valid_after

    def _validate_invalid_at(self):
        rt = self.get_relative_time_option(self.valid_at, 'valid_at')
        return self.cert.not_valid_before, rt, self.cert.not_valid_after

    def _validate_valid_in(self):
        valid_in_date = self.get_relative_time_option(self.valid_in, "valid_in")
        return self.cert.not_valid_before, valid_in_date, self.cert.not_valid_after


class AssertOnlyCertificate(AssertOnlyCertificateBase):
    """validate the supplied certificate."""

    def __init__(self, module):
        super(AssertOnlyCertificate, self).__init__(module, 'pyopenssl')

        # Ensure inputs are properly sanitized before comparison.
        for param in ['signature_algorithms', 'key_usage', 'extended_key_usage',
                      'subject_alt_name', 'subject', 'issuer', 'not_before',
                      'not_after', 'valid_at', 'invalid_at']:
            attr = getattr(self, param)
            if isinstance(attr, list) and attr:
                if isinstance(attr[0], str):
                    setattr(self, param, [to_bytes(item) for item in attr])
                elif isinstance(attr[0], tuple):
                    setattr(self, param, [(to_bytes(item[0]), to_bytes(item[1])) for item in attr])
            elif isinstance(attr, tuple):
                setattr(self, param, dict((to_bytes(k), to_bytes(v)) for (k, v) in attr.items()))
            elif isinstance(attr, dict):
                setattr(self, param, dict((to_bytes(k), to_bytes(v)) for (k, v) in attr.items()))
            elif isinstance(attr, str):
                setattr(self, param, to_bytes(attr))

    def _validate_privatekey(self):
        ctx = OpenSSL.SSL.Context(OpenSSL.SSL.TLSv1_2_METHOD)
        ctx.use_privatekey(self.privatekey)
        ctx.use_certificate(self.cert)
        try:
            ctx.check_privatekey()
            return True
        except OpenSSL.SSL.Error:
            return False

    def _validate_csr_signature(self):
        try:
            self.csr.verify(self.cert.get_pubkey())
        except OpenSSL.crypto.Error:
            return False

    def _validate_csr_subject(self):
        if self.csr.get_subject() != self.cert.get_subject():
            return False

    def _validate_csr_extensions(self):
        csr_extensions = self.csr.get_extensions()
        cert_extension_count = self.cert.get_extension_count()
        if len(csr_extensions) != cert_extension_count:
            return False
        for extension_number in range(0, cert_extension_count):
            cert_extension = self.cert.get_extension(extension_number)
            csr_extension = filter(lambda extension: extension.get_short_name() == cert_extension.get_short_name(), csr_extensions)
            if cert_extension.get_data() != list(csr_extension)[0].get_data():
                return False
        return True

    def _validate_signature_algorithms(self):
        if self.cert.get_signature_algorithm() not in self.signature_algorithms:
            return self.cert.get_signature_algorithm()

    def _validate_subject(self):
        expected_subject = [(OpenSSL._util.lib.OBJ_txt2nid(sub[0]), sub[1]) for sub in self.subject]
        cert_subject = self.cert.get_subject().get_components()
        current_subject = [(OpenSSL._util.lib.OBJ_txt2nid(sub[0]), sub[1]) for sub in cert_subject]
        if not compare_sets(expected_subject, current_subject, self.subject_strict):
            return expected_subject, current_subject

    def _validate_issuer(self):
        expected_issuer = [(OpenSSL._util.lib.OBJ_txt2nid(iss[0]), iss[1]) for iss in self.issuer]
        cert_issuer = self.cert.get_issuer().get_components()
        current_issuer = [(OpenSSL._util.lib.OBJ_txt2nid(iss[0]), iss[1]) for iss in cert_issuer]
        if not compare_sets(expected_issuer, current_issuer, self.issuer_strict):
            return self.issuer, cert_issuer

    def _validate_has_expired(self):
        # The following 3 lines are the same as the current PyOpenSSL code for cert.has_expired().
        # Older version of PyOpenSSL have a buggy implementation,
        # to avoid issues with those we added the code from a more recent release here.

        time_string = to_native(self.cert.get_notAfter())
        not_after = datetime.datetime.strptime(time_string, "%Y%m%d%H%M%SZ")
        cert_expired = not_after < datetime.datetime.utcnow()
        return cert_expired

    def _validate_version(self):
        # Version numbers in certs are off by one:
        # v1: 0, v2: 1, v3: 2 ...
        return self.cert.get_version() + 1

    def _validate_key_usage(self):
        found = False
        for extension_idx in range(0, self.cert.get_extension_count()):
            extension = self.cert.get_extension(extension_idx)
            if extension.get_short_name() == b'keyUsage':
                found = True
                key_usage = [OpenSSL._util.lib.OBJ_txt2nid(key_usage) for key_usage in self.key_usage]
                current_ku = [OpenSSL._util.lib.OBJ_txt2nid(usage.strip()) for usage in
                              to_bytes(extension, errors='surrogate_or_strict').split(b',')]
                if not compare_sets(key_usage, current_ku, self.key_usage_strict):
                    return self.key_usage, str(extension).split(', ')
        if not found:
            # This is only bad if the user specified a non-empty list
            if self.key_usage:
                return NO_EXTENSION

    def _validate_extended_key_usage(self):
        found = False
        for extension_idx in range(0, self.cert.get_extension_count()):
            extension = self.cert.get_extension(extension_idx)
            if extension.get_short_name() == b'extendedKeyUsage':
                found = True
                extKeyUsage = [OpenSSL._util.lib.OBJ_txt2nid(keyUsage) for keyUsage in self.extended_key_usage]
                current_xku = [OpenSSL._util.lib.OBJ_txt2nid(usage.strip()) for usage in
                               to_bytes(extension, errors='surrogate_or_strict').split(b',')]
                if not compare_sets(extKeyUsage, current_xku, self.extended_key_usage_strict):
                    return self.extended_key_usage, str(extension).split(', ')
        if not found:
            # This is only bad if the user specified a non-empty list
            if self.extended_key_usage:
                return NO_EXTENSION

    def _normalize_san(self, san):
        # Apparently OpenSSL returns 'IP address' not 'IP' as specifier when converting the subjectAltName to string
        # although it won't accept this specifier when generating the CSR. (https://github.com/openssl/openssl/issues/4004)
        if san.startswith('IP Address:'):
            san = 'IP:' + san[len('IP Address:'):]
        if san.startswith('IP:'):
            ip = compat_ipaddress.ip_address(san[3:])
            san = 'IP:{0}'.format(ip.compressed)
        return san

    def _validate_subject_alt_name(self):
        found = False
        for extension_idx in range(0, self.cert.get_extension_count()):
            extension = self.cert.get_extension(extension_idx)
            if extension.get_short_name() == b'subjectAltName':
                found = True
                l_altnames = [self._normalize_san(altname.strip()) for altname in
                              to_text(extension, errors='surrogate_or_strict').split(', ')]
                sans = [self._normalize_san(to_text(san, errors='surrogate_or_strict')) for san in self.subject_alt_name]
                if not compare_sets(sans, l_altnames, self.subject_alt_name_strict):
                    return self.subject_alt_name, l_altnames
        if not found:
            # This is only bad if the user specified a non-empty list
            if self.subject_alt_name:
                return NO_EXTENSION

    def _validate_not_before(self):
        return self.cert.get_notBefore()

    def _validate_not_after(self):
        return self.cert.get_notAfter()

    def _validate_valid_at(self):
        return self.cert.get_notBefore(), self.valid_at, self.cert.get_notAfter()

    def _validate_invalid_at(self):
        return self.cert.get_notBefore(), self.valid_at, self.cert.get_notAfter()

    def _validate_valid_in(self):
        valid_in_asn1 = self.get_relative_time_option(self.valid_in, "valid_in")
        valid_in_date = to_bytes(valid_in_asn1, errors='surrogate_or_strict')
        return self.cert.get_notBefore(), valid_in_date, self.cert.get_notAfter()


class AcmeCertificate(Certificate):
    """Retrieve a certificate using the ACME protocol."""

    # Since there's no real use of the backend,
    # other than the 'self.check' function, we just pass the backend to the constructor

    def __init__(self, module, backend):
        super(AcmeCertificate, self).__init__(module, backend)
        self.accountkey_path = module.params['acme_accountkey_path']
        self.challenge_path = module.params['acme_challenge_path']
        self.use_chain = module.params['acme_chain']

    def generate(self, module):

        if not os.path.exists(self.privatekey_path):
            raise CertificateError(
                'The private key %s does not exist' % self.privatekey_path
            )

        if not os.path.exists(self.csr_path):
            raise CertificateError(
                'The certificate signing request file %s does not exist' % self.csr_path
            )

        if not os.path.exists(self.accountkey_path):
            raise CertificateError(
                'The account key %s does not exist' % self.accountkey_path
            )

        if not os.path.exists(self.challenge_path):
            raise CertificateError(
                'The challenge path %s does not exist' % self.challenge_path
            )

        if not self.check(module, perms_required=False) or self.force:
            acme_tiny_path = self.module.get_bin_path('acme-tiny', required=True)
            command = [acme_tiny_path]
            if self.use_chain:
                command.append('--chain')
            command.extend(['--account-key', self.accountkey_path])
            command.extend(['--csr', self.csr_path])
            command.extend(['--acme-dir', self.challenge_path])

            try:
                crt = module.run_command(command, check_rc=True)[1]
                if self.backup:
                    self.backup_file = module.backup_local(self.path)
                crypto_utils.write_file(module, to_bytes(crt))
                self.changed = True
            except OSError as exc:
                raise CertificateError(exc)

        file_args = module.load_file_common_arguments(module.params)
        if module.set_fs_attributes_if_different(file_args, False):
            self.changed = True

    def dump(self, check_mode=False):

        result = {
            'changed': self.changed,
            'filename': self.path,
            'privatekey': self.privatekey_path,
            'accountkey': self.accountkey_path,
            'csr': self.csr_path,
        }
        if self.backup_file:
            result['backup_file'] = self.backup_file

        return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            path=dict(type='path', required=True),
            provider=dict(type='str', choices=['acme', 'assertonly', 'ownca', 'selfsigned']),
            force=dict(type='bool', default=False,),
            csr_path=dict(type='path'),
            backup=dict(type='bool', default=False),
            select_crypto_backend=dict(type='str', default='auto', choices=['auto', 'cryptography', 'pyopenssl']),

            # General properties of a certificate
            privatekey_path=dict(type='path'),
            privatekey_passphrase=dict(type='str', no_log=True),

            # provider: assertonly
            signature_algorithms=dict(type='list', elements='str'),
            subject=dict(type='dict'),
            subject_strict=dict(type='bool', default=False),
            issuer=dict(type='dict'),
            issuer_strict=dict(type='bool', default=False),
            has_expired=dict(type='bool', default=False),
            version=dict(type='int'),
            key_usage=dict(type='list', elements='str', aliases=['keyUsage']),
            key_usage_strict=dict(type='bool', default=False, aliases=['keyUsage_strict']),
            extended_key_usage=dict(type='list', elements='str', aliases=['extendedKeyUsage']),
            extended_key_usage_strict=dict(type='bool', default=False, aliases=['extendedKeyUsage_strict']),
            subject_alt_name=dict(type='list', elements='str', aliases=['subjectAltName']),
            subject_alt_name_strict=dict(type='bool', default=False, aliases=['subjectAltName_strict']),
            not_before=dict(type='str', aliases=['notBefore']),
            not_after=dict(type='str', aliases=['notAfter']),
            valid_at=dict(type='str'),
            invalid_at=dict(type='str'),
            valid_in=dict(type='str'),

            # provider: selfsigned
            selfsigned_version=dict(type='int', default=3),
            selfsigned_digest=dict(type='str', default='sha256'),
            selfsigned_not_before=dict(type='str', default='+0s', aliases=['selfsigned_notBefore']),
            selfsigned_not_after=dict(type='str', default='+3650d', aliases=['selfsigned_notAfter']),

            # provider: ownca
            ownca_path=dict(type='path'),
            ownca_privatekey_path=dict(type='path'),
            ownca_privatekey_passphrase=dict(type='str', no_log=True),
            ownca_digest=dict(type='str', default='sha256'),
            ownca_version=dict(type='int', default=3),
            ownca_not_before=dict(type='str', default='+0s'),
            ownca_not_after=dict(type='str', default='+3650d'),

            # provider: acme
            acme_accountkey_path=dict(type='path'),
            acme_challenge_path=dict(type='path'),
            acme_chain=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
        add_file_common_args=True,
    )

    try:
        if module.params['state'] == 'absent':
            certificate = CertificateAbsent(module)

        else:
            if module.params['provider'] != 'assertonly' and module.params['csr_path'] is None:
                module.fail_json(msg='csr_path is required when provider is not assertonly')

            base_dir = os.path.dirname(module.params['path']) or '.'
            if not os.path.isdir(base_dir):
                module.fail_json(
                    name=base_dir,
                    msg='The directory %s does not exist or the file is not a directory' % base_dir
                )

            provider = module.params['provider']

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

                if module.params['selfsigned_version'] == 2 or module.params['ownca_version'] == 2:
                    module.warn('crypto backend forced to pyopenssl. The cryptography library does not support v2 certificates')
                    backend = 'pyopenssl'

                # Fail if no backend has been found
                if backend == 'auto':
                    module.fail_json(msg=("Can't detect any of the required Python libraries "
                                          "cryptography (>= {0}) or PyOpenSSL (>= {1})").format(
                                              MINIMAL_CRYPTOGRAPHY_VERSION,
                                              MINIMAL_PYOPENSSL_VERSION))

            if backend == 'pyopenssl':
                if not PYOPENSSL_FOUND:
                    module.fail_json(msg=missing_required_lib('pyOpenSSL >= {0}'.format(MINIMAL_PYOPENSSL_VERSION)),
                                     exception=PYOPENSSL_IMP_ERR)
                if module.params['provider'] in ['selfsigned', 'ownca', 'assertonly']:
                    try:
                        getattr(crypto.X509Req, 'get_extensions')
                    except AttributeError:
                        module.fail_json(msg='You need to have PyOpenSSL>=0.15')

                if provider == 'selfsigned':
                    certificate = SelfSignedCertificate(module)
                elif provider == 'acme':
                    certificate = AcmeCertificate(module, 'pyopenssl')
                elif provider == 'ownca':
                    certificate = OwnCACertificate(module)
                else:
                    certificate = AssertOnlyCertificate(module)
            elif backend == 'cryptography':
                if not CRYPTOGRAPHY_FOUND:
                    module.fail_json(msg=missing_required_lib('cryptography >= {0}'.format(MINIMAL_CRYPTOGRAPHY_VERSION)),
                                     exception=CRYPTOGRAPHY_IMP_ERR)
                if module.params['selfsigned_version'] == 2 or module.params['ownca_version'] == 2:
                    module.fail_json(msg='The cryptography backend does not support v2 certificates, '
                                         'use select_crypto_backend=pyopenssl for v2 certificates')
                if provider == 'selfsigned':
                    certificate = SelfSignedCertificateCryptography(module)
                elif provider == 'acme':
                    certificate = AcmeCertificate(module, 'cryptography')
                elif provider == 'ownca':
                    certificate = OwnCACertificateCryptography(module)
                else:
                    certificate = AssertOnlyCertificateCryptography(module)

        if module.params['state'] == 'present':
            if module.check_mode:
                result = certificate.dump(check_mode=True)
                result['changed'] = module.params['force'] or not certificate.check(module)
                module.exit_json(**result)

            certificate.generate(module)
        else:
            if module.check_mode:
                result = certificate.dump(check_mode=True)
                result['changed'] = os.path.exists(module.params['path'])
                module.exit_json(**result)

            certificate.remove(module)

        result = certificate.dump()
        module.exit_json(**result)
    except crypto_utils.OpenSSLObjectError as exc:
        module.fail_json(msg=to_native(exc))


if __name__ == "__main__":
    main()
