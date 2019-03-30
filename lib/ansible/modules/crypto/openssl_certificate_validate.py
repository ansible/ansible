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
            - Path to the Certificate Signing Request (CSR) used to generate this certificate.
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
                self.message.append(
                    'Certificate %s and private key %s do not match' %
                    (self.path, self.privatekey_path)
                )

        if self.csr_path:
            self.csr = crypto_utils.load_certificate_request(self.csr_path, backend=self.backend)
            if not self._validate_csr_signature():
                self.message.append(
                    'Certificate %s and CSR %s do not match: private key mismatch' %
                    (self.path, self.csr_path)
                )
            if not self._validate_csr_subject():
                self.message.append(
                    'Certificate %s and CSR %s do not match: subject mismatch' %
                    (self.path, self.csr_path)
                )
            if not self._validate_csr_extensions():
                self.message.append(
                    'Certificate %s and CSR %s do not match: extensions mismatch' %
                    (self.path, self.csr_path)
                )

        if self.signature_algorithms:
            wrong_alg = self._validate_signature_algorithms()
            if wrong_alg:
                self.message.append(
                    'Invalid signature algorithm (got %s, expected one of %s)' %
                    (wrong_alg, self.signature_algorithms)
                )

        if self.subject:
            self._validate_subject()

        if self.issuer:
            self._validate_issuer()

        if self.has_expired is not None:
            cert_expired = self._validate_has_expired()
            if cert_expired != self.has_expired:
                self.message.append(
                    'Certificate expiration check failed (certificate expiration is %s, expected %s)' %
                    (cert_expired, self.has_expired)
                )

        if self.version:
            cert_version = self._validate_version()
            if cert_version != self.version:
                self.message.append(
                    'Invalid certificate version number (got %s, expected %s)' %
                    (cert_version, self.version)
                )

        if self.key_usage is not None:
            self._validate_key_usage()

        if self.extended_key_usage is not None:
            self._validate_extended_key_usage()

        if self.subject_alt_name is not None:
            self._validate_subject_alt_name()

        if self.not_before:
            cert_not_valid_before = self._validate_not_before()
            if cert_not_valid_before != self.get_relative_time_option(self.not_before, 'not_before'):
                self.message.append(
                    'Invalid not_before component (got %s, expected %s to be present)' %
                    (cert_not_valid_before, self.not_before)
                )

        if self.not_after:
            cert_not_valid_after = self._validate_not_after()
            if cert_not_valid_after != self.get_relative_time_option(self.not_after, 'not_after'):
                self.message.append(
                    'Invalid not_after component (got %s, expected %s to be present)' %
                    (cert_not_valid_after, self.not_after)
                )

        if self.valid_at:
            not_before, valid_at, not_after = self._validate_valid_at()
            if not (not_before <= valid_at <= not_after):
                self.message.append(
                    'Certificate is not valid for the specified date (%s) - not_before: %s - not_after: %s' %
                    (self.valid_at, not_before, not_after)
                )

        if self.invalid_at:
            not_before, invalid_at, not_after = self._validate_invalid_at()
            if (invalid_at <= not_before) or (invalid_at >= not_after):
                self.message.append(
                    'Certificate is not invalid for the specified date (%s) - not_before: %s - not_after: %s' %
                    (self.invalid_at, not_before, not_after)
                )

        if self.valid_in:
            not_before, valid_in, not_after = self._validate_valid_in()
            if not not_before <= valid_in <= not_after:
                self.message.append(
                    'Certificate is not valid in %s from now (that would be %s) - not_before: %s - not_after: %s'
                    % (self.valid_in, valid_in, not_before, not_after))

        if len(self.message):
            module.fail_json(msg=' | '.join(self.message))

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
        if (not self.subject_strict and not all(x in cert_subject for x in expected_subject)) or \
           (self.subject_strict and not set(expected_subject) == set(cert_subject)):
            self.message.append(
                'Invalid subject component (got %s, expected all of %s to be present)' %
                (cert_subject, expected_subject)
            )

    def _validate_issuer(self):
        expected_issuer = Name([NameAttribute(oid=crypto_utils.cryptography_get_name_oid(iss[0]), value=to_text(iss[1]))
                                for iss in self.issuer])
        cert_issuer = self.cert.issuer
        if (not self.issuer_strict and not all(x in cert_issuer for x in expected_issuer)) or \
           (self.issuer_strict and not set(expected_issuer) == set(cert_issuer)):
            self.message.append(
                'Invalid issuer component (got %s, expected all of %s to be present)' % (cert_issuer, self.issuer)
            )

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
            expected_key_usage = x509.KeyUsage(**crypto_utils.cryptography_parse_key_usage_params(self.key_usage))
            test_key_usage = dict(
                digital_signature=current_key_usage.digital_signature,
                content_commitment=current_key_usage.content_commitment,
                key_encipherment=current_key_usage.key_encipherment,
                data_encipherment=current_key_usage.data_encipherment,
                key_agreement=current_key_usage.key_agreement,
                key_cert_sign=current_key_usage.key_cert_sign,
                crl_sign=current_key_usage.crl_sign,
            )
            if test_key_usage['key_agreement']:
                test_key_usage.update(dict(
                    encipher_only=current_key_usage.encipher_only,
                    decipher_only=current_key_usage.decipher_only
                ))
            else:
                test_key_usage.update(dict(
                    encipher_only=False,
                    decipher_only=False
                ))

            key_usages = crypto_utils.cryptography_parse_key_usage_params(self.key_usage)
            if (not self.key_usage_strict and not all(key_usages[x] == test_key_usage[x] for x in key_usages)) or \
                    (self.key_usage_strict and current_key_usage != expected_key_usage):
                self.message.append(
                    'Invalid key_usage components (got %s, expected all of %s to be present)' %
                    ([x for x in test_key_usage if x is True], [x for x in self.key_usage if x is True])
                )

        except cryptography.x509.ExtensionNotFound:
            self.message.append('Found no key_usage extension')

    def _validate_extended_key_usage(self):
        try:
            current_ext_keyusage = self.cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
            usages = [crypto_utils.cryptography_get_ext_keyusage(usage) for usage in self.extended_key_usage]
            expected_ext_keyusage = x509.ExtendedKeyUsage(usages)
            if (not self.extended_key_usage_strict and not all(x in expected_ext_keyusage for x in current_ext_keyusage)) or \
               (self.extended_key_usage_strict and not current_ext_keyusage == expected_ext_keyusage):
                self.message.append(
                    'Invalid extended_key_usage component (got %s, expected all of %s to be present)' % ([xku.value for xku in current_ext_keyusage],
                                                                                                         [exku.value for exku in expected_ext_keyusage])
                )

        except cryptography.x509.ExtensionNotFound:
            self.message.append('Found no extended_key_usage extension')

    def _validate_subject_alt_name(self):
        try:
            current_san = self.cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
            expected_san = [crypto_utils.cryptography_get_name(san) for san in self.subject_alt_name]
            if (not self.subject_alt_name_strict and not all(x in current_san for x in expected_san)) or \
               (self.subject_alt_name_strict and not set(current_san) == set(expected_san)):
                self.message.append(
                    'Invalid subject_alt_name component (got %s, expected all of %s to be present)' %
                    (current_san, self.subject_alt_name)
                )
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
        if not self.valid_in.startswith("+") and not self.valid_in.startswith("-"):
            try:
                int(self.valid_in)
            except ValueError:
                raise CertificateError(
                    'The supplied value for "valid_in" (%s) is not an integer or a valid timespec' % self.valid_in)
            self.valid_in = "+" + self.valid_in + "s"
        valid_in_date = self.get_relative_time_option(self.valid_in, "valid_in")
        return self.cert.not_valid_before, valid_in_date, self.cert.not_valid_after


class AssertOnlyCertificate(Certificate):
    """validate the supplied certificate."""

    def __init__(self, module):
        super(AssertOnlyCertificate, self).__init__(module, 'pyopenssl')
        self._sanitize_inputs()

    def _sanitize_inputs(self):
        """Ensure inputs are properly sanitized before comparison."""

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
        if (not self.subject_strict and not all(x in current_subject for x in expected_subject)) or \
           (self.subject_strict and not set(expected_subject) == set(current_subject)):
            self.message.append(
                'Invalid subject component (got %s, expected all of %s to be present)' % (cert_subject, self.subject)
            )

    def _validate_issuer(self):
        expected_issuer = [(OpenSSL._util.lib.OBJ_txt2nid(iss[0]), iss[1]) for iss in self.issuer]
        cert_issuer = self.cert.get_issuer().get_components()
        current_issuer = [(OpenSSL._util.lib.OBJ_txt2nid(iss[0]), iss[1]) for iss in cert_issuer]
        if (not self.issuer_strict and not all(x in current_issuer for x in expected_issuer)) or \
           (self.issuer_strict and not set(expected_issuer) == set(current_issuer)):
            self.message.append(
                'Invalid issuer component (got %s, expected all of %s to be present)' % (cert_issuer, self.issuer)
            )

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
                if (not self.key_usage_strict and not all(x in current_ku for x in key_usage)) or \
                   (self.key_usage_strict and not set(key_usage) == set(current_ku)):
                    self.message.append(
                        'Invalid key_usage component (got %s, expected all of %s to be present)' % (str(extension).split(', '), self.key_usage)
                    )
        if not found:
            self.message.append('Found no key_usage extension')

    def _validate_extended_key_usage(self):
        found = False
        for extension_idx in range(0, self.cert.get_extension_count()):
            extension = self.cert.get_extension(extension_idx)
            if extension.get_short_name() == b'extendedKeyUsage':
                found = True
                extKeyUsage = [OpenSSL._util.lib.OBJ_txt2nid(keyUsage) for keyUsage in self.extended_key_usage]
                current_xku = [OpenSSL._util.lib.OBJ_txt2nid(usage.strip()) for usage in
                               to_bytes(extension, errors='surrogate_or_strict').split(b',')]
                if (not self.extended_key_usage_strict and not all(x in current_xku for x in extKeyUsage)) or \
                   (self.extended_key_usage_strict and not set(extKeyUsage) == set(current_xku)):
                    self.message.append(
                        'Invalid extended_key_usage component (got %s, expected all of %s to be present)' % (str(extension).split(', '),
                                                                                                             self.extended_key_usage)
                    )
        if not found:
            self.message.append('Found no extended_key_usage extension')

    def _validate_subject_alt_name(self):
        found = False
        for extension_idx in range(0, self.cert.get_extension_count()):
            extension = self.cert.get_extension(extension_idx)
            if extension.get_short_name() == b'subjectAltName':
                found = True
                l_altnames = [altname.replace(b'IP Address', b'IP') for altname in
                              to_bytes(extension, errors='surrogate_or_strict').split(b', ')]
                if (not self.subject_alt_name_strict and not all(x in l_altnames for x in self.subject_alt_name)) or \
                   (self.subject_alt_name_strict and not set(self.subject_alt_name) == set(l_altnames)):
                    self.message.append(
                        'Invalid subject_alt_name component (got %s, expected all of %s to be present)' % (l_altnames, self.subject_alt_name)
                    )
        if not found:
            self.message.append('Found no subject_alt_name extension')

    def _validate_not_before(self):
        return self.cert.get_notBefore()

    def _validate_not_after(self):
        return self.cert.get_notAfter()

    def _validate_valid_at(self):
        return self.cert.get_notBefore(), self.valid_at, self.cert.get_notAfter()

    def _validate_invalid_at(self):
        return self.cert.get_notBefore(), self.valid_at, self.cert.get_notAfter()

    def _validate_valid_in(self):
        if not self.valid_in.startswith("+") and not self.valid_in.startswith("-"):
            try:
                int(self.valid_in)
            except ValueError:
                raise CertificateError(
                    'The supplied value for "valid_in" (%s) is not an integer or a valid timespec' % self.valid_in)
            self.valid_in = "+" + self.valid_in + "s"
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
