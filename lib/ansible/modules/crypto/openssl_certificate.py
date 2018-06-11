#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016-2017, Yanis Guenane <yanis+ansible@guenane.org>
# (c) 2017, Markus Teufelberger <mteufelberger+ansible@mgit.at>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: openssl_certificate
author:
  - Yanis Guenane (@Spredzy)
  - Markus Teufelberger (@MarkusTeufelberger)
version_added: "2.4"
short_description: Generate and/or check OpenSSL certificates
description:
    - "This module allows one to (re)generate OpenSSL certificates. It implements a notion
       of provider (ie. C(selfsigned), C(acme), C(assertonly)) for your certificate.
       The 'assertonly' provider is intended for use cases where one is only interested in
       checking properties of a supplied certificate.
       Many properties that can be specified in this module are for validation of an
       existing or newly generated certificate. The proper place to specify them, if you
       want to receive a certificate with these properties is a CSR (Certificate Signing Request).
       It uses the pyOpenSSL python library to interact with OpenSSL."
requirements:
    - python-pyOpenSSL >= 0.15 (if using C(selfsigned) or C(assertonly) provider)
    - acme-tiny (if using the C(acme) provider)
options:
    state:
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the certificate should exist or not, taking action if the state is different from what is stated.

    path:
        required: true
        description:
            - Remote absolute path where the generated certificate file should be created or is already located.

    provider:
        required: true
        choices: [ 'selfsigned', 'assertonly', 'acme' ]
        description:
            - Name of the provider to use to generate/retrieve the OpenSSL certificate.
              The C(assertonly) provider will not generate files and fail if the certificate file is missing.

    force:
        default: False
        type: bool
        description:
            - Generate the certificate, even if it already exists.

    csr_path:
        description:
            - Path to the Certificate Signing Request (CSR) used to generate this certificate. This is not required in C(assertonly) mode.

    privatekey_path:
        description:
            - Path to the private key to use when signing the certificate.

    privatekey_passphrase:
        description:
            - The passphrase for the I(privatekey_path).

    selfsigned_version:
        default: 3
        description:
            - Version of the C(selfsigned) certificate. Nowadays it should almost always be C(3).
        version_added: "2.5"

    selfsigned_digest:
        default: "sha256"
        description:
            - Digest algorithm to be used when self-signing the certificate

    selfsigned_not_before:
        description:
            - The timestamp at which the certificate starts being valid. The timestamp is formatted as an ASN.1 TIME.
              If this value is not specified, certificate will start being valid from now.
        aliases: [ selfsigned_notBefore ]

    selfsigned_not_after:
        description:
            - The timestamp at which the certificate stops being valid. The timestamp is formatted as an ASN.1 TIME.
              If this value is not specified, certificate will stop being valid 10 years from now.
        aliases: [ selfsigned_notAfter ]

    acme_accountkey_path:
        description:
            - Path to the accountkey for the C(acme) provider

    acme_challenge_path:
        description:
            - Path to the ACME challenge directory that is served on U(http://<HOST>:80/.well-known/acme-challenge/)

    acme_chain:
        default: True
        description:
            - Include the intermediate certificate to the generated certificate
        version_added: "2.5"

    signature_algorithms:
        description:
            - list of algorithms that you would accept the certificate to be signed with
              (e.g. ['sha256WithRSAEncryption', 'sha512WithRSAEncryption']).

    issuer:
        description:
            - Key/value pairs that must be present in the issuer name field of the certificate.
              If you need to specify more than one value with the same key, use a list as value.

    issuer_strict:
        default: False
        type: bool
        description:
            - If set to True, the I(issuer) field must contain only these values.
        version_added: "2.5"

    subject:
        description:
            - Key/value pairs that must be present in the subject name field of the certificate.
              If you need to specify more than one value with the same key, use a list as value.

    subject_strict:
        default: False
        type: bool
        description:
            - If set to True, the I(subject) field must contain only these values.
        version_added: "2.5"

    has_expired:
        default: False
        type: bool
        description:
            - Checks if the certificate is expired/not expired at the time the module is executed.

    version:
        description:
            - Version of the certificate. Nowadays it should almost always be 3.

    valid_at:
        description:
            - The certificate must be valid at this point in time. The timestamp is formatted as an ASN.1 TIME.

    invalid_at:
        description:
            - The certificate must be invalid at this point in time. The timestamp is formatted as an ASN.1 TIME.

    not_before:
        description:
            - The certificate must start to become valid at this point in time. The timestamp is formatted as an ASN.1 TIME.
        aliases: [ notBefore ]

    not_after:
        description:
            - The certificate must expire at this point in time. The timestamp is formatted as an ASN.1 TIME.
        aliases: [ notAfter ]


    valid_in:
        description:
            - The certificate must still be valid in I(valid_in) seconds from now.

    key_usage:
        description:
            - The I(key_usage) extension field must contain all these values.
        aliases: [ keyUsage ]

    key_usage_strict:
        default: False
        type: bool
        description:
            - If set to True, the I(key_usage) extension field must contain only these values.
        aliases: [ keyUsage_strict ]

    extended_key_usage:
        description:
            - The I(extended_key_usage) extension field must contain all these values.
        aliases: [ extendedKeyUsage ]

    extended_key_usage_strict:
        default: False
        type: bool
        description:
            - If set to True, the I(extended_key_usage) extension field must contain only these values.
        aliases: [ extendedKeyUsage_strict ]

    subject_alt_name:
        description:
            - The I(subject_alt_name) extension field must contain these values.
        aliases: [ subjectAltName ]

    subject_alt_name_strict:
        default: False
        type: bool
        description:
            - If set to True, the I(subject_alt_name) extension field must contain only these values.
        aliases: [ subjectAltName_strict ]
extends_documentation_fragment: files
notes:
    - All ASN.1 TIME values should be specified following the YYYYMMDDHHMMSSZ pattern.
      Date specified should be UTC. Minutes and seconds are mandatory.
'''


EXAMPLES = '''
- name: Generate a Self Signed OpenSSL certificate
  openssl_certificate:
    path: /etc/ssl/crt/ansible.com.crt
    privatekey_path: /etc/ssl/private/ansible.com.pem
    csr_path: /etc/ssl/csr/ansible.com.csr
    provider: selfsigned

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
    force: True

# Examples for some checks one could use the assertonly provider for:

# How to use the assertonly provider to implement and trigger your own custom certificate generation workflow:
- name: Check if a certificate is currently still valid, ignoring failures
  openssl_certificate:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    has_expired: False
  ignore_errors: True
  register: validity_check

- name: Run custom task(s) to get a new, valid certificate in case the initial check failed
  command: superspecialSSL recreate /etc/ssl/crt/example.com.crt
  when: validity_check.failed

- name: Check the new certificate again for validity with the same parameters, this time failing the play if it is still invalid
  openssl_certificate:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    has_expired: False
  when: validity_check.failed

# Some other checks that assertonly could be used for:
- name: Verify that an existing certificate was issued by the Let's Encrypt CA and is currently still valid
  openssl_certificate:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    issuer:
      O: Let's Encrypt
    has_expired: False

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


RETURN = '''
filename:
    description: Path to the generated Certificate
    returned: changed or success
    type: string
    sample: /etc/ssl/crt/www.ansible.com.crt
'''


from random import randint
import datetime
import os

from ansible.module_utils import crypto as crypto_utils
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native, to_bytes

try:
    import OpenSSL
    from OpenSSL import crypto
except ImportError:
    pyopenssl_found = False
else:
    pyopenssl_found = True


class CertificateError(crypto_utils.OpenSSLObjectError):
    pass


class Certificate(crypto_utils.OpenSSLObject):

    def __init__(self, module):
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
        self.module = module

    def check(self, module, perms_required=True):
        """Ensure the resource is in its desired state."""

        state_and_perms = super(Certificate, self).check(module, perms_required)

        def _validate_privatekey():
            if self.privatekey_path:
                ctx = OpenSSL.SSL.Context(OpenSSL.SSL.TLSv1_2_METHOD)
                ctx.use_privatekey(self.privatekey)
                ctx.use_certificate(self.cert)
                try:
                    ctx.check_privatekey()
                    return True
                except OpenSSL.SSL.Error:
                    return False

        if not state_and_perms:
            return False

        self.cert = crypto_utils.load_certificate(self.path)

        if self.privatekey_path:
            self.privatekey = crypto_utils.load_privatekey(
                self.privatekey_path,
                self.privatekey_passphrase
            )
            return _validate_privatekey()

        return True


class SelfSignedCertificate(Certificate):
    """Generate the self-signed certificate."""

    def __init__(self, module):
        super(SelfSignedCertificate, self).__init__(module)
        self.notBefore = module.params['selfsigned_notBefore']
        self.notAfter = module.params['selfsigned_notAfter']
        self.digest = module.params['selfsigned_digest']
        self.version = module.params['selfsigned_version']
        self.serial_number = randint(1000, 99999)
        self.csr = crypto_utils.load_certificate_request(self.csr_path)
        self.privatekey = crypto_utils.load_privatekey(
            self.privatekey_path, self.privatekey_passphrase
        )

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
            if self.notBefore:
                cert.set_notBefore(self.notBefore)
            else:
                cert.gmtime_adj_notBefore(0)
            if self.notAfter:
                cert.set_notAfter(self.notAfter)
            else:
                # If no NotAfter specified, expire in
                # 10 years. 315360000 is 10 years in seconds.
                cert.gmtime_adj_notAfter(315360000)
            cert.set_subject(self.csr.get_subject())
            cert.set_issuer(self.csr.get_subject())
            cert.set_version(self.version - 1)
            cert.set_pubkey(self.csr.get_pubkey())
            cert.add_extensions(self.csr.get_extensions())

            cert.sign(self.privatekey, self.digest)
            self.cert = cert

            try:
                with open(self.path, 'wb') as cert_file:
                    cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, self.cert))
            except EnvironmentError as exc:
                raise CertificateError(exc)

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

        if check_mode:
            now = datetime.datetime.utcnow()
            ten = now.replace(now.year + 10)
            result.update({
                'notBefore': self.notBefore if self.notBefore else now.strftime("%Y%m%d%H%M%SZ"),
                'notAfter': self.notAfter if self.notAfter else ten.strftime("%Y%m%d%H%M%SZ"),
                'serial_number': self.serial_number,
            })
        else:
            result.update({
                'notBefore': self.cert.get_notBefore(),
                'notAfter': self.cert.get_notAfter(),
                'serial_number': self.cert.get_serial_number(),
            })

        return result


class AssertOnlyCertificate(Certificate):
    """validate the supplied certificate."""

    def __init__(self, module):
        super(AssertOnlyCertificate, self).__init__(module)
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
        self.keyUsage = module.params['keyUsage']
        self.keyUsage_strict = module.params['keyUsage_strict']
        self.extendedKeyUsage = module.params['extendedKeyUsage']
        self.extendedKeyUsage_strict = module.params['extendedKeyUsage_strict']
        self.subjectAltName = module.params['subjectAltName']
        self.subjectAltName_strict = module.params['subjectAltName_strict']
        self.notBefore = module.params['notBefore']
        self.notAfter = module.params['notAfter']
        self.valid_at = module.params['valid_at']
        self.invalid_at = module.params['invalid_at']
        self.valid_in = module.params['valid_in']
        self.message = []
        self._sanitize_inputs()

    def _sanitize_inputs(self):
        """Ensure inputs are properly sanitized before comparison."""

        for param in ['signature_algorithms', 'keyUsage', 'extendedKeyUsage',
                      'subjectAltName', 'subject', 'issuer', 'notBefore',
                      'notAfter', 'valid_at', 'invalid_at']:

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

    def assertonly(self):

        self.cert = crypto_utils.load_certificate(self.path)

        def _validate_signature_algorithms():
            if self.signature_algorithms:
                if self.cert.get_signature_algorithm() not in self.signature_algorithms:
                    self.message.append(
                        'Invalid signature algorithm (got %s, expected one of %s)' % (self.cert.get_signature_algorithm(), self.signature_algorithms)
                    )

        def _validate_subject():
            if self.subject:
                expected_subject = [(OpenSSL._util.lib.OBJ_txt2nid(sub[0]), sub[1]) for sub in self.subject]
                cert_subject = self.cert.get_subject().get_components()
                current_subject = [(OpenSSL._util.lib.OBJ_txt2nid(sub[0]), sub[1]) for sub in cert_subject]
                if (not self.subject_strict and not all(x in current_subject for x in expected_subject)) or \
                   (self.subject_strict and not set(expected_subject) == set(current_subject)):
                    self.message.append(
                        'Invalid subject component (got %s, expected all of %s to be present)' % (cert_subject, self.subject)
                    )

        def _validate_issuer():
            if self.issuer:
                expected_issuer = [(OpenSSL._util.lib.OBJ_txt2nid(iss[0]), iss[1]) for iss in self.issuer]
                cert_issuer = self.cert.get_issuer().get_components()
                current_issuer = [(OpenSSL._util.lib.OBJ_txt2nid(iss[0]), iss[1]) for iss in cert_issuer]
                if (not self.issuer_strict and not all(x in current_issuer for x in expected_issuer)) or \
                   (self.issuer_strict and not set(expected_issuer) == set(current_issuer)):
                    self.message.append(
                        'Invalid issuer component (got %s, expected all of %s to be present)' % (cert_issuer, self.issuer)
                    )

        def _validate_has_expired():
            if self.has_expired:
                if self.has_expired != self.cert.has_expired():
                    self.message.append(
                        'Certificate expiration check failed (certificate expiration is %s, expected %s)' % (self.cert.has_expired(), self.has_expired)
                    )

        def _validate_version():
            if self.version:
                # Version numbers in certs are off by one:
                # v1: 0, v2: 1, v3: 2 ...
                if self.version != self.cert.get_version() + 1:
                    self.message.append(
                        'Invalid certificate version number (got %s, expected %s)' % (self.cert.get_version() + 1, self.version)
                    )

        def _validate_keyUsage():
            if self.keyUsage:
                for extension_idx in range(0, self.cert.get_extension_count()):
                    extension = self.cert.get_extension(extension_idx)
                    if extension.get_short_name() == b'keyUsage':
                        keyUsage = [OpenSSL._util.lib.OBJ_txt2nid(keyUsage) for keyUsage in self.keyUsage]
                        current_ku = [OpenSSL._util.lib.OBJ_txt2nid(usage.strip()) for usage in
                                      to_bytes(extension, errors='surrogate_or_strict').split(b',')]
                        if (not self.keyUsage_strict and not all(x in current_ku for x in keyUsage)) or \
                           (self.keyUsage_strict and not set(keyUsage) == set(current_ku)):
                            self.message.append(
                                'Invalid keyUsage component (got %s, expected all of %s to be present)' % (str(extension).split(', '), self.keyUsage)
                            )

        def _validate_extendedKeyUsage():
            if self.extendedKeyUsage:
                for extension_idx in range(0, self.cert.get_extension_count()):
                    extension = self.cert.get_extension(extension_idx)
                    if extension.get_short_name() == b'extendedKeyUsage':
                        extKeyUsage = [OpenSSL._util.lib.OBJ_txt2nid(keyUsage) for keyUsage in self.extendedKeyUsage]
                        current_xku = [OpenSSL._util.lib.OBJ_txt2nid(usage.strip()) for usage in
                                       to_bytes(extension, errors='surrogate_or_strict').split(b',')]
                        if (not self.extendedKeyUsage_strict and not all(x in current_xku for x in extKeyUsage)) or \
                           (self.extendedKeyUsage_strict and not set(extKeyUsage) == set(current_xku)):
                            self.message.append(
                                'Invalid extendedKeyUsage component (got %s, expected all of %s to be present)' % (str(extension).split(', '),
                                                                                                                   self.extendedKeyUsage)
                            )

        def _validate_subjectAltName():
            if self.subjectAltName:
                for extension_idx in range(0, self.cert.get_extension_count()):
                    extension = self.cert.get_extension(extension_idx)
                    if extension.get_short_name() == b'subjectAltName':
                        l_altnames = [altname.replace(b'IP Address', b'IP') for altname in
                                      to_bytes(extension, errors='surrogate_or_strict').split(b', ')]
                        if (not self.subjectAltName_strict and not all(x in l_altnames for x in self.subjectAltName)) or \
                           (self.subjectAltName_strict and not set(self.subjectAltName) == set(l_altnames)):
                            self.message.append(
                                'Invalid subjectAltName component (got %s, expected all of %s to be present)' % (l_altnames, self.subjectAltName)
                            )

        def _validate_notBefore():
            if self.notBefore:
                if self.cert.get_notBefore() != self.notBefore:
                    self.message.append(
                        'Invalid notBefore component (got %s, expected %s to be present)' % (self.cert.get_notBefore(), self.notBefore)
                    )

        def _validate_notAfter():
            if self.notAfter:
                if self.cert.get_notAfter() != self.notAfter:
                    self.message.append(
                        'Invalid notAfter component (got %s, expected %s to be present)' % (self.cert.get_notAfter(), self.notAfter)
                    )

        def _validate_valid_at():
            if self.valid_at:
                if not (self.cert.get_notBefore() <= self.valid_at <= self.cert.get_notAfter()):
                    self.message.append(
                        'Certificate is not valid for the specified date (%s) - notBefore: %s - notAfter: %s' % (self.valid_at,
                                                                                                                 self.cert.get_notBefore(),
                                                                                                                 self.cert.get_notAfter())
                    )

        def _validate_invalid_at():
            if self.invalid_at:
                if not (self.invalid_at <= self.cert.get_notBefore() or self.invalid_at >= self.cert.get_notAfter()):
                    self.message.append(
                        'Certificate is not invalid for the specified date (%s) - notBefore: %s - notAfter: %s' % (self.invalid_at,
                                                                                                                   self.cert.get_notBefore(),
                                                                                                                   self.cert.get_notAfter())
                    )

        def _validate_valid_in():
            if self.valid_in:
                valid_in_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=self.valid_in)
                valid_in_date = to_bytes(valid_in_date.strftime('%Y%m%d%H%M%SZ'), errors='surrogate_or_strict')
                if not (self.cert.get_notBefore() <= valid_in_date <= self.cert.get_notAfter()):
                    self.message.append(
                        'Certificate is not valid in %s seconds from now (%s) - notBefore: %s - notAfter: %s' % (self.valid_in,
                                                                                                                 valid_in_date,
                                                                                                                 self.cert.get_notBefore(),
                                                                                                                 self.cert.get_notAfter())
                    )

        for validation in ['signature_algorithms', 'subject', 'issuer',
                           'has_expired', 'version', 'keyUsage',
                           'extendedKeyUsage', 'subjectAltName',
                           'notBefore', 'notAfter', 'valid_at',
                           'invalid_at', 'valid_in']:
            f_name = locals()['_validate_%s' % validation]
            f_name()

    def generate(self, module):
        """Don't generate anything - assertonly"""

        self.assertonly()

        if self.privatekey_path and \
           not super(AssertOnlyCertificate, self).check(module, perms_required=False):
            self.message.append(
                'Certificate %s and private key %s does not match' % (self.path, self.privatekey_path)
            )

        if len(self.message):
            module.fail_json(msg=' | '.join(self.message))

    def check(self, module, perms_required=True):
        """Ensure the resource is in its desired state."""

        parent_check = super(AssertOnlyCertificate, self).check(module, perms_required)
        self.assertonly()
        assertonly_check = not len(self.message)
        self.message = []

        return parent_check and assertonly_check

    def dump(self, check_mode=False):

        result = {
            'changed': self.changed,
            'filename': self.path,
            'privatekey': self.privatekey_path,
            'csr': self.csr_path,
        }

        return result


class AcmeCertificate(Certificate):
    """Retrieve a certificate using the ACME protocol."""

    def __init__(self, module):
        super(AcmeCertificate, self).__init__(module)
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
            chain = ''
            if self.use_chain:
                chain = '--chain'

            try:
                crt = module.run_command("%s %s --account-key %s --csr %s "
                                         "--acme-dir %s" % (acme_tiny_path, chain,
                                                            self.accountkey_path,
                                                            self.csr_path,
                                                            self.challenge_path),
                                         check_rc=True)[1]
                with open(self.path, 'wb') as certfile:
                    certfile.write(to_bytes(crt))
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

        return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            path=dict(type='path', required=True),
            provider=dict(type='str', choices=['selfsigned', 'assertonly', 'acme']),
            force=dict(type='bool', default=False,),
            csr_path=dict(type='path'),

            # General properties of a certificate
            privatekey_path=dict(type='path'),
            privatekey_passphrase=dict(type='str', no_log=True),
            signature_algorithms=dict(type='list'),
            subject=dict(type='dict'),
            subject_strict=dict(type='bool', default=False),
            issuer=dict(type='dict'),
            issuer_strict=dict(type='bool', default=False),
            has_expired=dict(type='bool', default=False),
            version=dict(type='int'),
            keyUsage=dict(type='list', aliases=['key_usage']),
            keyUsage_strict=dict(type='bool', default=False, aliases=['key_usage_strict']),
            extendedKeyUsage=dict(type='list', aliases=['extended_key_usage'], ),
            extendedKeyUsage_strict=dict(type='bool', default=False, aliases=['extended_key_usage_strict']),
            subjectAltName=dict(type='list', aliases=['subject_alt_name']),
            subjectAltName_strict=dict(type='bool', default=False, aliases=['subject_alt_name_strict']),
            notBefore=dict(type='str', aliases=['not_before']),
            notAfter=dict(type='str', aliases=['not_after']),
            valid_at=dict(type='str'),
            invalid_at=dict(type='str'),
            valid_in=dict(type='int'),

            # provider: selfsigned
            selfsigned_version=dict(type='int', default='3'),
            selfsigned_digest=dict(type='str', default='sha256'),
            selfsigned_notBefore=dict(type='str', aliases=['selfsigned_not_before']),
            selfsigned_notAfter=dict(type='str', aliases=['selfsigned_not_after']),

            # provider: acme
            acme_accountkey_path=dict(type='path'),
            acme_challenge_path=dict(type='path'),
            acme_chain=dict(type='bool', default=True),
        ),
        supports_check_mode=True,
        add_file_common_args=True,
    )

    if not pyopenssl_found:
        module.fail_json(msg='The python pyOpenSSL library is required')
    if module.params['provider'] in ['selfsigned', 'assertonly']:
        try:
            getattr(crypto.X509Req, 'get_extensions')
        except AttributeError:
            module.fail_json(msg='You need to have PyOpenSSL>=0.15')

    base_dir = os.path.dirname(module.params['path'])
    if not os.path.isdir(base_dir):
        module.fail_json(
            name=base_dir,
            msg='The directory %s does not exist or the file is not a directory' % base_dir
        )

    provider = module.params['provider']

    if provider == 'selfsigned':
        certificate = SelfSignedCertificate(module)
    elif provider == 'acme':
        certificate = AcmeCertificate(module)
    else:
        certificate = AssertOnlyCertificate(module)

    if module.params['state'] == 'present':

        if module.check_mode:
            result = certificate.dump(check_mode=True)
            result['changed'] = module.params['force'] or not certificate.check(module)
            module.exit_json(**result)

        try:
            certificate.generate(module)
        except CertificateError as exc:
            module.fail_json(msg=to_native(exc))
    else:

        if module.check_mode:
            result = certificate.dump(check_mode=True)
            result['changed'] = os.path.exists(module.params['path'])
            module.exit_json(**result)

        try:
            certificate.remove()
        except CertificateError as exc:
            module.fail_json(msg=to_native(exc))

    result = certificate.dump()

    module.exit_json(**result)


if __name__ == "__main__":
    main()
