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
module: openssl_certificate_validate
version_added: "2.8"
short_description: Check OpenSSL certificates
description:
    - This module allows to verify conditions on OpenSSL certificates.
    - It uses the pyOpenSSL or cryptography python library to interact with OpenSSL.
    - If both the cryptography and PyOpenSSL libraries are available (and meet the minimum version requirements)
      cryptography will be preferred as a backend over PyOpenSSL (unless the backend is forced with I(select_crypto_backend)).
requirements:
    - PyOpenSSL >= 0.15 or cryptography >= 1.6
author:
    - Yanis Guenane (@Spredzy)
    - Markus Teufelberger (@MarkusTeufelberger)
    - Felix Fontein (@felixfontein)
options:
    path:
        description:
            - Remote absolute path where the certificate file is located.
        type: path
        required: yes

    csr_path:
        description:
            - Path to a Certificate Signing Request (CSR).
            - Will check whether the CSR data corresponds to this certificate.
        type: path

    privatekey_path:
        description:
            - Path to a private key file.
            - Will check whether the certificate's public key is the public key to this private key.
        type: path

    privatekey_passphrase:
        description:
            - The passphrase for the I(privatekey_path).
            - This is required if the private key is password protected.
        type: str

    signature_algorithms:
        description:
            - A list of algorithms that you would accept the certificate to be signed with
              (e.g. ['sha256WithRSAEncryption', 'sha512WithRSAEncryption']).
        type: list

    issuer:
        description:
            - The key/value pairs that must be present in the issuer name field of the certificate.
            - If you need to specify more than one value with the same key, use a list as value.
        type: dict

    issuer_strict:
        description:
            - If set to C(yes), the I(issuer) field must contain only these values.
        type: bool
        default: no

    subject:
        description:
            - The key/value pairs that must be present in the subject name field of the certificate.
            - If you need to specify more than one value with the same key, use a list as value.
        type: dict

    subject_strict:
        description:
            - If set to C(yes), the I(subject) field must contain only these values.
        type: bool
        default: no

    has_expired:
        description:
            - Checks if the certificate is expired/not expired at the time the module is executed.
        type: bool

    version:
        description:
            - The version of the certificate.
            - Nowadays it should almost always be 3.
        type: int

    valid_at:
        description:
            - The certificate must be valid at this point in time.
            - The timestamp is formatted as an ASN.1 TIME.
        type: str

    invalid_at:
        description:
            - The certificate must be invalid at this point in time.
            - The timestamp is formatted as an ASN.1 TIME.
        type: str

    not_before:
        description:
            - The certificate must start to become valid at this point in time.
            - The timestamp is formatted as an ASN.1 TIME.
        type: str

    not_after:
        description:
            - The certificate must expire at this point in time.
            - The timestamp is formatted as an ASN.1 TIME.
        type: str

    valid_in:
        description:
            - The certificate must still be valid at this relative time offset from now.
            - Valid format is C([+-]timespec | number_of_seconds) where timespec can be an integer
              + C([w | d | h | m | s]) (e.g. C(+32w1d2h).
            - Note that if using this parameter, this module is NOT idempotent.
        type: str

    key_usage:
        description:
            - The I(key_usage) extension field must contain all these values.
        type: list

    key_usage_strict:
        description:
            - If set to C(yes), the I(key_usage) extension field must contain only these values.
        type: bool
        default: no

    extended_key_usage:
        description:
            - The I(extended_key_usage) extension field must contain all these values.
        type: list

    extended_key_usage_strict:
        description:
            - If set to C(yes), the I(extended_key_usage) extension field must contain only these values.
        type: bool
        default: no

    subject_alt_name:
        description:
            - The I(subject_alt_name) extension field must contain these values.
        type: list

    subject_alt_name_strict:
        description:
            - If set to C(yes), the I(subject_alt_name) extension field must contain only these values.
        type: bool
        default: no

    fail_when_validation_failed:
        description:
            - By default, the module fails when at least one of the conditions is not satisfied.
            - If set to C(no), the module will not fail in this case. The user is responsible to
              check the return values herself.
            - Note that the module will still fail if it cannot read the certificate, or the
              private key or the CSR when provided.
        type: bool
        default: yes

    select_crypto_backend:
        description:
            - Determines which crypto backend to use.
            - The default choice is C(auto), which tries to use C(cryptography) if available, and falls back to C(pyopenssl).
            - If set to C(pyopenssl), will try to use the L(pyOpenSSL,https://pypi.org/project/pyOpenSSL/) library.
            - If set to C(cryptography), will try to use the L(cryptography,https://cryptography.io/) library.
        type: str
        default: auto
        choices: [ auto, cryptography, pyopenssl ]

notes:
    - All ASN.1 TIME values should be specified following the YYYYMMDDHHMMSSZ pattern.
    - Date specified should be UTC. Minutes and seconds are mandatory.
seealso:
- module: openssl_certificate
'''

EXAMPLES = r'''
# How to use the module to implement and trigger your own custom certificate generation workflow:
- name: Check if a certificate is currently still valid, ignoring failures
  openssl_certificate_validate:
    path: /etc/ssl/crt/example.com.crt
    has_expired: no
  ignore_errors: yes
  register: validity_check

- name: Run custom task(s) to get a new, valid certificate in case the initial check failed
  command: superspecialSSL recreate /etc/ssl/crt/example.com.crt
  when: validity_check.failed

- name: Check the new certificate again for validity with the same parameters, this time failing the play if it is still invalid
  openssl_certificate_validate:
    path: /etc/ssl/crt/example.com.crt
    has_expired: no
  when: validity_check.failed

# Some other checks that assertonly could be used for:
- name: Verify that an existing certificate was issued by the Let's Encrypt CA and is currently still valid
  openssl_certificate_validate:
    path: /etc/ssl/crt/example.com.crt
    issuer:
      O: Let's Encrypt
    has_expired: no

- name: Ensure that a certificate uses a modern signature algorithm (no SHA1, MD5 or DSA)
  openssl_certificate_validate:
    path: /etc/ssl/crt/example.com.crt
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
  openssl_certificate_validate:
    path: /etc/ssl/crt/example.com.crt
    privatekey_path: /etc/ssl/private/example.com.pem

- name: Ensure that the existing certificate is still valid at the winter solstice 2017
  openssl_certificate_validate:
    path: /etc/ssl/crt/example.com.crt
    valid_at: 20171221162800Z

- name: Ensure that the existing certificate is still valid 2 weeks (1209600 seconds) from now
  openssl_certificate_validate:
    path: /etc/ssl/crt/example.com.crt
    valid_in: 1209600

- name: Ensure that the existing certificate is only used for digital signatures and encrypting other keys
  openssl_certificate_validate:
    path: /etc/ssl/crt/example.com.crt
    key_usage:
      - digitalSignature
      - keyEncipherment
    key_usage_strict: true

- name: Ensure that the existing certificate can be used for client authentication
  openssl_certificate_validate:
    path: /etc/ssl/crt/example.com.crt
    extended_key_usage:
      - clientAuth

- name: Ensure that the existing certificate can only be used for client authentication and time stamping
  openssl_certificate_validate:
    path: /etc/ssl/crt/example.com.crt
    extended_key_usage:
      - clientAuth
      - 1.3.6.1.5.5.7.3.8
    extended_key_usage_strict: true

- name: Ensure that the existing certificate has a certain domain in its subjectAltName
  openssl_certificate_validate:
    path: /etc/ssl/crt/example.com.crt
    subject_alt_name:
      - www.example.com
      - test.example.com
'''

RETURN = r'''
private_key_matches:
    description: Whether private key matches.
    returned: data could be loaded and I(privatekey_path) is set
    type: bool
csr_signature_matches:
    description: Whether the CSR's signature is valid and the public key equals the certificate's public key.
    returned: data could be loaded and I(csr_path) is set
    type: bool
csr_subject_match:
    description: Whether the CSR's subject equals the certificate's subject matches.
    returned: data could be loaded and I(csr_path) is set
    type: bool
csr_extensions_match:
    description: Whether the CSR's extensions equal the certificate's extensions matches.
    returned: data could be loaded and I(csr_path) is set
    type: bool
signature_algorithm_matches:
    description: Whether the signature algorithm used for the certificate is contained in the provided list.
    returned: data could be loaded and I(signature_algorithms) is set
    type: bool
subject_matches:
    description: Whether the subject of the certificate matches I(subject).
    returned: data could be loaded and I(subject) is set
    type: bool
issuer_matches:
    description: Whether the issuer of the certificate matches I(issuer).
    returned: data could be loaded and I(issuer) is set
    type: bool
has_expired_matches:
    description: Whether the certificate's expiration corresponds to I(has_expired).
    returned: data could be loaded and I(has_expired) is set
    type: bool
version_matches:
    description: Whether the version of the certificate matches I(version).
    returned: data could be loaded and I(version) is set
    type: bool
key_usage_matches:
    description: Whether the key usages of the certificate match I(key_usage).
    returned: data could be loaded and I(key_usage) is set
    type: bool
extended_key_usage_matches:
    description: Whether the extended key usages of the certificate match I(extended_key_usage).
    returned: data could be loaded and I(extended_key_usage) is set
    type: bool
subject_alt_name_matches:
    description: Whether subject alternative names of the certificate match I(subject_alt_name).
    returned: data could be loaded and I(subject_alt_name) is set
    type: bool
not_before_matches:
    description: Whether the not before date of the certificate matches I(not_before).
    returned: data could be loaded and I(not_before) is set
    type: bool
not_after_matches:
    description: Whether the not after date of the certificate matches I(not_after).
    returned: data could be loaded and I(not_after) is set
    type: bool
valid_at:
    description: Whether the certificate is valid at I(valid_at).
    returned: data could be loaded and I(valid_at) is set
    type: bool
invalid_at:
    description: Whether the certificate is invalid at I(invalid_at).
    returned: data could be loaded and I(invalid_at) is set
    type: bool
invalid_in:
    description: Whether the certificate is invalid in I(invalid_in).
    returned: data could be loaded and I(invalid_in) is set
    type: bool
'''

import abc
import datetime
import traceback
from distutils.version import LooseVersion

from ansible.module_utils import crypto as crypto_utils
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native, to_bytes, to_text

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
    from cryptography.x509 import NameAttribute, Name
    CRYPTOGRAPHY_VERSION = LooseVersion(cryptography.__version__)
except ImportError:
    CRYPTOGRAPHY_IMP_ERR = traceback.format_exc()
    CRYPTOGRAPHY_FOUND = False
else:
    CRYPTOGRAPHY_FOUND = True


class CertificateError(crypto_utils.OpenSSLObjectError):
    pass


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


class Certificate(object):

    def __init__(self, module, backend):
        self.path = module.params['path']
        self.privatekey_path = module.params['privatekey_path']
        self.privatekey_passphrase = module.params['privatekey_passphrase']
        self.csr_path = module.params['csr_path']
        self.cert = None
        self.privatekey = None
        self.csr = None
        self.backend = backend
        self.module = module
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
        self.fail_when_validation_failed = module.params['fail_when_validation_failed']
        self.message = []

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

    def validate(self, module):
        result = dict()
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
            result['private_key_matches'] = True
            if not self._validate_privatekey():
                self.message.append(
                    'Certificate %s and private key %s do not match' %
                    (self.path, self.privatekey_path)
                )
                result['private_key_matches'] = False

        if self.csr_path is not None:
            self.csr = crypto_utils.load_certificate_request(self.csr_path, backend=self.backend)
            result['csr_signature_matches'] = True
            result['csr_subject_match'] = True
            result['csr_extensions_match'] = True
            if not self._validate_csr_signature():
                self.message.append(
                    'Certificate %s and CSR %s do not match: private key mismatch' %
                    (self.path, self.csr_path)
                )
                result['csr_signature_matches'] = False
            if not self._validate_csr_subject():
                self.message.append(
                    'Certificate %s and CSR %s do not match: subject mismatch' %
                    (self.path, self.csr_path)
                )
                result['csr_subject_match'] = False
            if not self._validate_csr_extensions():
                self.message.append(
                    'Certificate %s and CSR %s do not match: extensions mismatch' %
                    (self.path, self.csr_path)
                )
                result['csr_extensions_match'] = False

        if self.signature_algorithms is not None:
            result['signature_algorithm_matches'] = True
            wrong_alg = self._validate_signature_algorithms()
            if wrong_alg:
                self.message.append(
                    'Invalid signature algorithm (got %s, expected one of %s)' %
                    (wrong_alg, self.signature_algorithms)
                )
                result['signature_algorithm_matches'] = False

        if self.subject is not None:
            result['subject_matches'] = True
            failure = self._validate_subject()
            if failure:
                dummy, cert_subject = failure
                self.message.append(
                    'Invalid subject component (got %s, expected all of %s to be present)' %
                    (cert_subject, self.subject)
                )
                result['subject_matches'] = False

        if self.issuer is not None:
            result['issuer_matches'] = True
            failure = self._validate_issuer()
            if failure:
                dummy, cert_issuer = failure
                self.message.append(
                    'Invalid issuer component (got %s, expected all of %s to be present)' % (cert_issuer, self.issuer)
                )
                result['issuer_matches'] = False

        if self.has_expired is not None:
            result['has_expired_matches'] = True
            cert_expired = self._validate_has_expired()
            if cert_expired != self.has_expired:
                self.message.append(
                    'Certificate expiration check failed (certificate expiration is %s, expected %s)' %
                    (cert_expired, self.has_expired)
                )
                result['has_expired_matches'] = False

        if self.version is not None:
            result['version_matches'] = True
            cert_version = self._validate_version()
            if cert_version != self.version:
                self.message.append(
                    'Invalid certificate version number (got %s, expected %s)' %
                    (cert_version, self.version)
                )
                result['version_matches'] = False

        if self.key_usage is not None:
            result['key_usage_matches'] = True
            failure = self._validate_key_usage()
            if failure == NO_EXTENSION:
                self.message.append('Found no key_usage extension')
                result['key_usage_matches'] = False
            elif failure:
                dummy, cert_key_usage = failure
                self.message.append(
                    'Invalid key_usage components (got %s, expected all of %s to be present)' %
                    (cert_key_usage, self.key_usage)
                )
                result['key_usage_matches'] = False

        if self.extended_key_usage is not None:
            result['extended_key_usage_matches'] = True
            failure = self._validate_extended_key_usage()
            if failure == NO_EXTENSION:
                self.message.append('Found no extended_key_usage extension')
                result['extended_key_usage_matches'] = False
            elif failure:
                dummy, ext_cert_key_usage = failure
                self.message.append(
                    'Invalid extended_key_usage component (got %s, expected all of %s to be present)' % (ext_cert_key_usage, self.extended_key_usage)
                )
                result['extended_key_usage_matches'] = False

        if self.subject_alt_name is not None:
            result['subject_alt_name_matches'] = True
            failure = self._validate_subject_alt_name()
            if failure == NO_EXTENSION:
                self.message.append('Found no subject_alt_name extension')
                result['subject_alt_name_matches'] = False
            elif failure:
                dummy, cert_san = failure
                self.message.append(
                    'Invalid subject_alt_name component (got %s, expected all of %s to be present)' %
                    (cert_san, self.subject_alt_name)
                )
                result['subject_alt_name_matches'] = False

        if self.not_before is not None:
            result['not_before_matches'] = True
            cert_not_valid_before = self._validate_not_before()
            if cert_not_valid_before != self.get_relative_time_option(self.not_before, 'not_before'):
                self.message.append(
                    'Invalid not_before component (got %s, expected %s to be present)' %
                    (cert_not_valid_before, self.not_before)
                )
                result['not_before_matches'] = False

        if self.not_after is not None:
            result['not_after_matches'] = True
            cert_not_valid_after = self._validate_not_after()
            if cert_not_valid_after != self.get_relative_time_option(self.not_after, 'not_after'):
                self.message.append(
                    'Invalid not_after component (got %s, expected %s to be present)' %
                    (cert_not_valid_after, self.not_after)
                )
                result['not_after_matches'] = True

        if self.valid_at is not None:
            result['valid_at'] = True
            not_before, valid_at, not_after = self._validate_valid_at()
            if not (not_before <= valid_at <= not_after):
                self.message.append(
                    'Certificate is not valid for the specified date (%s) - not_before: %s - not_after: %s' %
                    (self.valid_at, not_before, not_after)
                )
                result['valid_at'] = False

        if self.invalid_at is not None:
            result['invalid_at'] = True
            not_before, invalid_at, not_after = self._validate_invalid_at()
            if (invalid_at <= not_before) or (invalid_at >= not_after):
                self.message.append(
                    'Certificate is not invalid for the specified date (%s) - not_before: %s - not_after: %s' %
                    (self.invalid_at, not_before, not_after)
                )
                result['invalid_at'] = False

        if self.valid_in is not None:
            result['invalid_in'] = True
            not_before, valid_in, not_after = self._validate_valid_in()
            if not not_before <= valid_in <= not_after:
                self.message.append(
                    'Certificate is not valid in %s from now (that would be %s) - not_before: %s - not_after: %s' %
                    (self.valid_in, valid_in, not_before, not_after)
                )
                result['invalid_in'] = False

        if self.fail_when_validation_failed and len(self.message):
            module.fail_json(msg=' | '.join(self.message), **result)

        return result


class AssertOnlyCertificateCryptography(Certificate):
    """Validate the supplied cert, using the cryptography backend"""
    def __init__(self, module):
        super(AssertOnlyCertificateCryptography, self).__init__(module, 'cryptography')

    def _validate_privatekey(self):
        return self.cert.public_key().public_numbers() == self.privatekey.public_key().public_numbers()

    def _validate_csr_signature(self):
        if not self.csr.is_signature_valid:
            return False
        if self.csr.public_key().public_numbers() != self.cert.public_key().public_numbers():
            return False

    def _validate_csr_subject(self):
        if self.csr.subject != self.cert.subject:
            return False

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
        expected_subject = Name([NameAttribute(oid=crypto_utils.cryptography_get_name_oid(sub[0]), value=to_text(sub[1]))
                                 for sub in self.subject])
        cert_subject = self.cert.subject
        if not compare_sets(expected_subject, cert_subject, self.subject_strict):
            return expected_subject, cert_subject

    def _validate_issuer(self):
        expected_issuer = Name([NameAttribute(oid=crypto_utils.cryptography_get_name_oid(iss[0]), value=to_text(iss[1]))
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
            return NO_EXTENSION

    def _validate_extended_key_usage(self):
        try:
            current_ext_keyusage = self.cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
            usages = [crypto_utils.cryptography_get_ext_keyusage(usage) for usage in self.extended_key_usage]
            expected_ext_keyusage = x509.ExtendedKeyUsage(usages)
            if not compare_sets(expected_ext_keyusage, current_ext_keyusage, self.extended_key_usage_strict):
                return [eku.value for eku in expected_ext_keyusage], [eku.value for eku in current_ext_keyusage]

        except cryptography.x509.ExtensionNotFound:
            self.message.append('Found no extended_key_usage extension')

    def _validate_subject_alt_name(self):
        try:
            current_san = self.cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
            expected_san = [crypto_utils.cryptography_get_name(san) for san in self.subject_alt_name]
            if not compare_sets(expected_san, current_san, self.subject_alt_name_strict):
                return self.subject_alt_name, current_san
        except cryptography.x509.ExtensionNotFound:
            self.message.append('Found no subject_alt_name extension')

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


class AssertOnlyCertificate(Certificate):
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
            return NO_EXTENSION

    def _validate_subject_alt_name(self):
        found = False
        for extension_idx in range(0, self.cert.get_extension_count()):
            extension = self.cert.get_extension(extension_idx)
            if extension.get_short_name() == b'subjectAltName':
                found = True
                l_altnames = [altname.replace(b'IP Address', b'IP') for altname in
                              to_bytes(extension, errors='surrogate_or_strict').split(b', ')]
                if not compare_sets(self.subject_alt_name, l_altnames, self.subject_alt_name_strict):
                    return self.subject_alt_name, l_altnames
        if not found:
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


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True),
            select_crypto_backend=dict(type='str', default='auto', choices=['auto', 'cryptography', 'pyopenssl']),
            privatekey_path=dict(type='path'),
            privatekey_passphrase=dict(type='str', no_log=True),
            csr_path=dict(type='path'),
            signature_algorithms=dict(type='list', elements='str'),
            subject=dict(type='dict'),
            subject_strict=dict(type='bool', default=False),
            issuer=dict(type='dict'),
            issuer_strict=dict(type='bool', default=False),
            has_expired=dict(type='bool'),
            version=dict(type='int'),
            key_usage=dict(type='list', elements='str'),
            key_usage_strict=dict(type='bool', default=False),
            extended_key_usage=dict(type='list', elements='str'),
            extended_key_usage_strict=dict(type='bool', default=False),
            subject_alt_name=dict(type='list', elements='str'),
            subject_alt_name_strict=dict(type='bool', default=False),
            not_before=dict(type='str'),
            not_after=dict(type='str'),
            valid_at=dict(type='str'),
            invalid_at=dict(type='str'),
            valid_in=dict(type='str'),
            fail_when_validation_failed=dict(type='bool', default=True),
        ),
        supports_check_mode=True,
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

        if module.params['selfsigned_version'] == 2 or module.params['ownca_version'] == 2:
            module.warn('crypto backend forced to pyopenssl. The cryptography library does not support v2 certificates')
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
        try:
            getattr(crypto.X509Req, 'get_extensions')
        except AttributeError:
            module.fail_json(msg='You need to have PyOpenSSL>=0.15')
        certificate = AssertOnlyCertificate(module)
    elif backend == 'cryptography':
        if not CRYPTOGRAPHY_FOUND:
            module.fail_json(msg=missing_required_lib('cryptography'), exception=CRYPTOGRAPHY_IMP_ERR)
        certificate = AssertOnlyCertificateCryptography(module)

    try:
        result = certificate.validate(module)
        module.exit_json(changed=False, **result)
    except crypto_utils.OpenSSLObjectError as e:
        module.fail_json(msg=to_native(e))


if __name__ == "__main__":
    main()
