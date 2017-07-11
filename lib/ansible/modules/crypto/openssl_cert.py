#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Yanis Guenane <yanis+ansible@guenane.org>
# (c) 2017, Markus Teufelberger <mteufelberger+ansible@mgit.at>
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: openssl_cert
author: "Yanis Guenane (@Spredzy) + Markus Teufelberger"
version_added: "2.4"
short_description: Generate and/or check OpenSSL certificates
description:
    - "This module allows one to (re)generate OpenSSL certificates. It implements a notion
       of provider (ie. 'selfsigned', 'letsencrypt') for your certificate.
       The 'assertonly' provider is intended for use cases where one is only interested in
       checking properties of a supplied certificate.
       Many properties that can be specified in this module are for validation of an
       existing or newly generated certificate. The proper place to specify them, if you
       want to receive a certificate with these properties is a CSR (Certificate Signing Request).
       It uses the pyOpenSSL python library to interact with OpenSSL."
requirements:
    - "python-pyOpenSSL >= 0.15"
    - python-cryptography
    - acme-tiny (if using the letsencrypt provider)
options:
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the certificate should exist or not, taking action if the state is different from what is stated.
    path:
        required: true
        default: null
        aliases: [ 'dest', 'destfile' ]
        description:
            - Remote absolute path where the generated certificate file should be created or is already located.
    provider:
        required: true
        choices: [ 'selfsigned', 'assertonly', 'letsencrypt' ]
        description:
            - Name of the provider to use to generate/retrieve the OpenSSL certificate.
              The 'assertonly' provider will not generate files and fail if the certificate file is missing.
    force:
        required: false
        default: False
        choices: [ True, False ]
        description:
            - Generate the certificate, even if it already exists.
    backup:
        required: false
        default: False
        choices: [ True, False ]
        description:
            - Create a backup file including timestamp information in case you were overwriting an existing certificate.
    csr_path:
        required: false
        description:
            - Path to the Certificate Signing Request (CSR) used to generate this certificate. This is not required in 'assertonly' mode.

    signature_algorithms:
        required: false
        description:
            - list of algorithms that you would accept the certificate to be signed with
              (e.g. ['sha256WithRSAEncryption', 'sha512WithRSAEncryption']).
    privatekey_path:
        required: false
        description:
            - Path to the private key to use when signing the certificate.
              It will be checked if the certificate and the private key have the same public key.
    issuer:
        required: false
        description:
            - Key/value pairs that must be present in the issuer name field of the certificate
    subject:
        required: false
        description:
            - Key/value pairs that must be present in the subject name field of the certificate
    has_expired:
        required: false
        choices: [ True, False ]
        description:
            - Checks if the certificate is expired/not expired at the time the module is executed.
    version:
        required: false
        description:
            - Version of the certificate. Nowadays it should almost always be 3.
    valid_at:
        required: false
        description:
            - The certificate must be valid at this point in time.
              The value must be ISO-8601 format, a UTC timezone must be specified and sub-second precision is not allowed, e.g. `2012-12-21T21:12:23Z`
    invalid_at:
        required: false
        description:
            - The certificate must be invalid at this point in time.
              The value must be ISO-8601 format, a UTC timezone must be specified and sub-second precision is not allowed, e.g. `2012-12-21T21:12:23Z`
    starts_at:
        required: false
        description:
            - The certificate must start to become valid at this point in time.
              The value must be ISO-8601 format, a UTC timezone must be specified and sub-second precision is not allowed, e.g. `2012-12-21T21:12:23Z`
    expires_at:
        required: false
        description:
            - The certificate must expire at this point in time.
              The value must be ISO-8601 format, a UTC timezone must be specified and sub-second precision is not allowed, e.g. `2012-12-21T21:12:23Z`
    valid_in:
        required: false
        description:
            - The certificate must still be valid in `valid_in` seconds from now.

    keyUsage_contains:
        required: false
        description:
            - The keyUsage extension field must contain these values, any unspecified values can be True or False.
              Field names are either the ones used by OpenSSL (e.g. `keyCertSign`) or the ones used by crptography (e.g. `key_cert_sign`)
    keyUsage_only:
        required: false
        description:
            - The keyUsage extension field must contain these values, any unspecified values must be False or not specified.
    extendedKeyUsage_contains:
        required: false
        description:
            - The extendedKeyUsage extension field must contain these entries, unspecified entries are allowed to exist.
              You can specify a list of the key usages to permit by OID or by name.
    extendedKeyUsage_only:
        required: false
        description:
            - The extendedKeyUsage extension field must contain these entries, any unspecified entries raise an error.
              You can specify a list of the key usages to permit by OID or by name.
    subjectAltName_contains:
        required: false
        description:
            - The subjectAltName extension field must contain these entries, unspecified entries are allowed to exist.
    subjectAltName_only:
        required: false
        description:
            - The subjectAltName extension field must contain these entries, any unspecified entries raise an error.
    warn:
        required: false
        default: True
        choices: [ True, False ]
        description:
            - Return warnings if some checks couldn't be performed, usually due to old library versions.

    selfsigned_digest:
        required: false
        default: "sha256"
        description:
            - Digest algorithm to be used when self-signing the certificate
    selfsigned_notBefore:
        required: false
        default: 0
        description:
            - Number of seconds from now which the self-signed certificate will be valid from.
    selfsigned_notAfter:
        required: false
        default: 315360000 (3650 days)
        description:
            - Number of seconds from now which the self-signed certificate will be expired.

    letsencrypt_accountkey:
        required: false
        description:
            - Path to the accountkey for the 'letsencrypt' provider
    letsencrypt_challenge_path:
        required: false
        description:
            - Path to the ACME challenge directory that is served on http://<HOST>:80/.well-known/acme-challenge/

notes:
    - "Features/checks that will be skipped with a warning if the version of pyOpenSSL is below a certain version:
      Check if public key of certificate and public key of private key are equal: requires pyOpenSSL >= 0.16.1"

    - "Features/checks that will be silently skipped if the installed version of cryptography is below a certain version:
      Expiration checks (except has_expired, which is done with pyOpenSSL): requires cryptography >= 0.7
      keyUsage_contains and keyUsage_only: requires cryptography >= 0.9
      extendedKeyUsage_contains and extendedKeyUsage_only: requires cryptography >= 0.9
      subjectAltName_contains and subjectAltName_only: requires cryptography >= 0.9"

    - The [keyUsage, extendedKeyUsage, subjectAltName]_contains and [keyUsage, extendedKeyUsage, subjectAltName]_only parameters are mutually exclusive.
'''


EXAMPLES = '''
- name: Generate a Self Signed OpenSSL certificate
  openssl_cert:
    path: /etc/ssl/crt/ansible.com.crt
    privatekey_path: /etc/ssl/private/ansible.com.pem
    csr_path: /etc/ssl/csr/ansible.com.csr
    provider: selfsigned

- name: Generate a Let's Encrypt Certificate
  openssl_cert:
    path: /etc/ssl/crt/ansible.com.crt
    csr_path: /etc/ssl/csr/ansible.com.csr
    provider: letsencrypt
    letsencrypt_accountkey: /etc/ssl/private/ansible.com.pem
    letsencrypt_challenge_path: /etc/ssl/challenges/ansible.com/

- name: Force (re-)generate a new Let's Encrypt Certificate
  openssl_cert:
    path: /etc/ssl/crt/ansible.com.crt
    csr_path: /etc/ssl/csr/ansible.com.csr
    provider: letsencrypt
    letsencrypt_accountkey: /etc/ssl/private/ansible.com.pem
    letsencrypt_challenge_path: /etc/ssl/challenges/ansible.com/
    force: True

# Examples for some checks one could use the assertonly provider for:
- name: Verify that an existing certificate was issued by the Let's Encrypt CA and is currently still valid
  openssl_cert:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    issuer:
      O: Let's Encrypt
    has_expired: False

- name: Ensure that a certificate uses a modern signature algorithm (no SHA1, MD5 or DSA)
  openssl_cert:
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
  openssl_cert:
    path: /etc/ssl/crt/example.com.crt
    privatekey_path: /etc/ssl/private/example.com.pem
    provider: assertonly

- name: Ensure that the existing certificate is still valid at the winter solstice 2017
  openssl_cert:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    valid_at: 2017-12-21T16:28:00Z

- name: Ensure that the existing certificate is still valid 2 weeks (1209600 seconds) from now
  openssl_cert:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    valid_in: 1209600

- name: Ensure that the existing certificate does not use Diffie-Hellman
  openssl_cert:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    keyUsage_contains:
      - key_agreement: False

- name: Ensure that the existing certificate is only used for digital signatures and encrypting other keys
  openssl_cert:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    keyUsage_only:
      - digital_signature: True
      - key_encipherment: True

- name: Ensure that the existing certificate can be used for client authentication
  openssl_cert:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    extendedKeyUsage_contains:
      - clientAuth

- name: Ensure that the existing certificate can only be used for client authentication and time stamping
  openssl_cert:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    extendedKeyUsage_only:
      - clientAuth
      - 1.3.6.1.5.5.7.3.8

- name: Ensure that the existing certificate has a certain domain in its subjectAltName
  openssl_cert:
    path: /etc/ssl/crt/example.com.crt
    provider: assertonly
    subjectAltName_contains:
      - www.example.com
      - test.example.com
'''


RETURN = '''
cert_path:
    description: Path to the generated Certificate
    returned: changed or success
    type: string
    sample: /etc/ssl/crt/www.ansible.com.crt
'''


import datetime
from random import randint
import re
import os

try:
    from OpenSSL import crypto
    from OpenSSL import __version__ as opensslversion
except ImportError:
    pyopenssl_found = False
else:
    pyopenssl_found = True

try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from OpenSSL import __version__ as cryptographyversion
except ImportError:
    cryptography_found = False
else:
    cryptography_found = True


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


class CertificateError(Exception):
    pass


class Certificate(object):

    def __init__(self, module):
        self.state = module.params['state']
        self.path = module.params['path']
        self.force = module.params['force']
        self.provider = module.params['provider']
        self.signature_algorithms = module.params['signature_algorithms']
        self.privatekey_path = module.params['privatekey_path']
        self.issuer = module.params['issuer']
        self.subject = module.params['subject']
        self.has_expired = module.params['has_expired']
        self.version = module.params['version']
        self.csr_path = module.params['csr_path']
        self.module = module
        self.changed = True
        self.warnings = []

    def generate(self):
        '''Generate the certificate signing request.'''
        # Implemented in child classes
        pass

    def remove(self):
        '''Remove the certificate'''

        try:
            os.remove(self.path)
        except OSError:
            self.changed = False

    def dump(self):
        '''Serialize the object into a dictionary.'''
        # Implemented in child classes
        pass

    def check(self):
        '''Check properties of the generated certificate.'''

        if not os.path.exists(self.path):
            self.module.fail_json(msg='The certificate at %s does not exist' % self.path)

        # pyOpenSSL checks:
        try:
            with open(self.path, "r") as certfile:
                cert = crypto.load_certificate(crypto.FILETYPE_PEM, certfile.read())
        except EnvironmentError:
            self.module.fail_json(msg='Could not read file at %s' % self.path)

        if self.signature_algorithms is not None:
            if cert.get_signature_algorithm() not in self.signature_algorithms:
                self.module.fail_json(
                    msg='Invalid signature algorithm (got %s, expected one of %s)' % (cert.get_signature_algorithm(), self.signature_algorithms))

        if self.subject is not None:
            cert_subject = cert.get_subject().get_components()
            for entry in self.subject:
                if (entry, self.subject[entry]) not in cert_subject:
                    self.module.fail_json(
                        msg='Invalid subject component (got %s, expected all of %s to be present)' % (cert_subject, self.subject))

        if self.issuer is not None:
            cert_issuer = cert.get_issuer().get_components()
            for entry in self.issuer:
                if (entry, self.issuer[entry]) not in cert_issuer:
                    self.module.fail_json(
                        msg='Invalid issuer component (got %s, expected all of %s to be present)' % (cert_issuer, self.issuer))

        if self.has_expired is not None:
            expired_check = cert.has_expired()
            if self.has_expired != expired_check:
                self.module.fail_json(
                    msg='Certificate expiration check failed (certificate expiration is %s, expected %s)' % (expired_check, self.has_expired))

        if self.version is not None:
            # Version numbers in certs are off by one:
            # v1: 0, v2: 1, v3: 2 ...
            cert_version = cert.get_version() + 1
            if self.version != cert_version:
                self.module.fail_json(
                    msg='Invalid certificate version number (got %s, expected %s)' % (cert_version, self.version))

        if self.privatekey_path is not None:
            try:
                with open(self.privatekey_path, "r") as private_key_file:
                    privkey = crypto.load_privatekey(crypto.FILETYPE_PEM, private_key_file.read())
            except EnvironmentError:
                self.module.fail_json(msg='Could not read file at %s' % self.privatekey_path)
            try:
                pubkey_e = privkey.to_cryptography_key().public_key().public_numbers().e
                cert_pubkey_e = cert.get_pubkey().to_cryptography_key().public_numbers().e
                if pubkey_e != cert_pubkey_e:
                    self.module.fail_json(
                        msg="Certificate public modulus doesn't match the provided private key.")
                pubkey_n = privkey.to_cryptography_key().public_key().public_numbers().n
                cert_pubkey_n = cert.get_pubkey().to_cryptography_key().public_numbers().n
                if pubkey_n != cert_pubkey_n:
                    self.module.fail_json(
                        msg="Certificate public exponent doesn't match the provided private key.")
            except:
                # The OpenSSL.crypto.PKey.to_cryptography_key() function is only available in pyOpenSSL >= 0.16.1
                if self.module.params['warn']:
                    self.warnings.append("Could not compare the certificate and the supplied private key. Your pyOpenSSL version: %s" % opensslversion)
                pass

        # cryptography checks:
        # Ideally only cryptography would be used, but X.509 support there is too young for some older distributions currently
        # TODO: re-evaluate in a few years if pyOpenSSL can be dropped as a requirement.
        use_cryptography = False
        try:
            with open(self.path, "rb") as certfile:
                crypto_cert = x509.load_pem_x509_certificate(certfile.read(), default_backend())
            use_cryptography = True
        except:
            # The cryptography.x509.load_pem_x509_certificate() function is only available in cryptography >= 0.7
            if self.module.params['warn']:
                self.warnings.append("Could not load the certificate using the cryptography library. Your cryptography version: %s" % cryptographyversion)
            pass

        # Expiration checks
        if use_cryptography:
            valid_start = crypto_cert.not_valid_before
            valid_end = crypto_cert.not_valid_after

        if self.module.params['valid_at'] is not None:
            try:
                valid_at = datetime.datetime.strptime(self.module.params['valid_at'], '%Y-%m-%dT%H:%M:%SZ')
            except ValueError:
                self.module.fail_json(msg='Could not parse valid_at timestamp (got %s)' % self.module.params['valid_at'])
        else:
            valid_at = None
        if use_cryptography and valid_at is not None:
            if valid_at < valid_start or valid_at >= valid_end:
                self.module.fail_json(
                    msg="Certificate is not valid at the specified time (it is valid from %s to %s, not at %s)." %
                    (valid_start.strftime("%Y-%m-%dT%H:%M:%SZ"), valid_end.strftime("%Y-%m-%dT%H:%M:%SZ"), valid_at.strftime("%Y-%m-%dT%H:%M:%SZ")))

        if self.module.params['invalid_at'] is not None:
            try:
                invalid_at = datetime.datetime.strptime(self.module.params['invalid_at'], '%Y-%m-%dT%H:%M:%SZ')
            except ValueError:
                self.module.fail_json(msg='Could not parse invalid_at timestamp (got %s)' % self.module.params['invalid_at'])
        else:
            invalid_at = None
        if use_cryptography and invalid_at is not None:
            if invalid_at >= valid_start and invalid_at < valid_end:
                self.module.fail_json(
                    msg="Certificate is not invalid at the specified time (it is valid from %s to %s, also at %s)." %
                    (valid_start.strftime("%Y-%m-%dT%H:%M:%SZ"), valid_end.strftime("%Y-%m-%dT%H:%M:%SZ"), invalid_at.strftime("%Y-%m-%dT%H:%M:%SZ")))

        if self.module.params['starts_at'] is not None:
            try:
                starts_at = datetime.datetime.strptime(self.module.params['starts_at'], '%Y-%m-%dT%H:%M:%SZ')
            except ValueError:
                self.module.fail_json(msg='Could not parse starts_at timestamp (got %s)' % self.module.params['starts_at'])
        else:
            starts_at = None
        if use_cryptography and starts_at is not None:
            if starts_at != valid_start:
                self.module.fail_json(
                    msg="Certificate does not start at the specified time (it starts at %s, not at %s)." %
                    (valid_start.strftime("%Y-%m-%dT%H:%M:%SZ"), starts_at.strftime("%Y-%m-%dT%H:%M:%SZ")))

        if self.module.params['expires_at'] is not None:
            try:
                expires_at = datetime.datetime.strptime(self.module.params['expires_at'], '%Y-%m-%dT%H:%M:%SZ')
            except ValueError:
                self.module.fail_json(msg='Could not parse expires_at timestamp (got %s)' % self.module.params['expires_at'])
        else:
            expires_at = None
        if use_cryptography and expires_at is not None:
            if expires_at != valid_end:
                self.module.fail_json(
                    msg="Certificate does not expire at the specified time (it expires at %s, not at %s)." %
                    (valid_end.strftime("%Y-%m-%dT%H:%M:%SZ"), expires_at.strftime("%Y-%m-%dT%H:%M:%SZ")))

        if use_cryptography and self.module.params['valid_in'] is not None:
            delta = datetime.timedelta(seconds=self.module.params['valid_in'])
            future_time = datetime.utcnow() + delta
            if future_time < valid_start or future_time >= valid_end:
                self.module.fail_json(
                    msg="Certificate is not valid at the specified time in valid_in (it is valid from %s to %s, not at %s)." %
                    (valid_start.strftime("%Y-%m-%dT%H:%M:%SZ"), valid_end.strftime("%Y-%m-%dT%H:%M:%SZ"), future_time.strftime("%Y-%m-%dT%H:%M:%SZ")))

        # Extension checks
        try:
            crypto_extensions = crypto_cert.extensions
        except:
            # The certificate extension handling code is only available in cryptography >= 0.9
            if self.module.params['warn']:
                self.warnings.append("Could not read extensions using the cryptography library. Your cryptography version: %s" % cryptographyversion)
            use_cryptography = False

        # keyUsage extension
        if use_cryptography and self.module.params['keyUsage_contains'] is not None:
            # 2.5.29.15 is the OID for keyUsage
            # it is available as varible in versions >= 1.0
            key_usage = crypto_cert.extensions.get_extension_for_oid(x509.ObjectIdentifier("2.5.29.15"))
            for entry in self.module.params['keyUsage_contains']:
                if entry in ["digital_signature", "digitalSignature"]:
                    if self.module.params['keyUsage_contains'][entry] != key_usage.digital_signature:
                        self.module.fail_json(
                            msg="Mismatch for the digital signature key usage (expected %s, got %s)" %
                            (self.module.params['keyUsage_contains'][entry], key_usage.digital_signature))
                elif entry in ["content_commitment", "non_repudiation", "contentCommitment", "nonRepudiation"]:
                    if self.module.params['keyUsage_contains'][entry] != key_usage.content_commitment:
                        self.module.fail_json(
                            msg="Mismatch for the content commitment key usage (expected %s, got %s)" %
                            (self.module.params['keyUsage_contains'][entry], key_usage.content_commitment))
                elif entry in ["key_encipherment", "keyEncipherment"]:
                    if self.module.params['keyUsage_contains'][entry] != key_usage.key_encipherment:
                        self.module.fail_json(
                            msg="Mismatch for the key encipherment key usage (expected %s, got %s)" %
                            (self.module.params['keyUsage_contains'][entry], key_usage.key_encipherment))
                elif entry in ["data_encipherment", "dataEncipherment"]:
                    if self.module.params['keyUsage_contains'][entry] != key_usage.data_encipherment:
                        self.module.fail_json(
                            msg="Mismatch for the data encipherment key usage (expected %s, got %s)" %
                            (self.module.params['keyUsage_contains'][entry], key_usage.data_encipherment))
                elif entry in ["key_agreement", "keyAgreement"]:
                    if self.module.params['keyUsage_contains'][entry] != key_usage.key_agreement:
                        self.module.fail_json(
                            msg="Mismatch for the key agreement key usage (expected %s, got %s)" %
                            (self.module.params['keyUsage_contains'][entry], key_usage.key_agreement))
                elif entry in ["key_cert_sign", "keyCertSign"]:
                    if self.module.params['keyUsage_contains'][entry] != key_usage.key_cert_sign:
                        self.module.fail_json(
                            msg="Mismatch for the key cert sign key usage (expected %s, got %s)" %
                            (self.module.params['keyUsage_contains'][entry], key_usage.key_cert_sign))
                elif entry in ["crl_sign", "cRLSign"]:
                    if self.module.params['keyUsage_contains'][entry] != key_usage.crl_sign:
                        self.module.fail_json(
                            msg="Mismatch for the crl sign key usage (expected %s, got %s)" %
                            (self.module.params['keyUsage_contains'][entry], key_usage.crl_sign))
                elif entry in ["encipher_only", "encipherOnly"]:
                    if self.module.params['keyUsage_contains'][entry] and not key_usage.key_agreement:
                        self.module.fail_json(
                            msg="The certificate has disabled the key_agreement usage. Checking the encipher only attribute doesn't make sense.")
                    else:
                        if self.module.params['keyUsage_contains'][entry] != key_usage.encipher_only:
                            self.module.fail_json(
                                msg="Mismatch for the encipher only key usage (expected %s, got %s)" %
                                (self.module.params['keyUsage_contains'][entry], key_usage.encipher_only))
                elif entry in ["decipher_only", "decipherOnly"]:
                    if self.module.params['keyUsage_contains'][entry] and not key_usage.key_agreement:
                        self.module.fail_json(
                            msg="The certificate has disabled the key_agreement usage. Checking the decipher only attribute doesn't make sense.")
                    else:
                        if self.module.params['keyUsage_contains'][entry] != key_usage.decipher_only:
                            self.module.fail_json(
                                msg="Mismatch for the decipher only key usage (expected %s, got %s)" %
                                (self.module.params['keyUsage_contains'][entry], key_usage.decipher_only))
                else:
                    self.module.fail_json(msg='Could not parse the keyUsage_contains entry "%s"' % self.module.params['keyUsage_contains'][entry])

        if use_cryptography and self.module.params['keyUsage_only'] is not None:
            # 2.5.29.15 is the OID for keyUsage
            # it is available as varible in versions >= 1.0
            key_usage = crypto_cert.extensions.get_extension_for_oid(x509.ObjectIdentifier("2.5.29.15"))
            flags_done = {
                "digital_signature": False,
                "content_commitment": False,
                "key_encipherment": False,
                "data_encipherment": False,
                "key_agreement": False,
                "key_cert_sign": False,
                "crl_sign": False,
                "encipher_only": False,
                "decipher_only": False
            }
            for entry in self.module.params['keyUsage_only']:
                if entry in ["digital_signature", "digitalSignature"]:
                    if self.module.params['keyUsage_only'][entry] != key_usage.digital_signature:
                        self.module.fail_json(
                            msg="Mismatch for the digital signature key usage (expected %s, got %s)" %
                            (self.module.params['keyUsage_only'][entry], key_usage.digital_signature))
                    flags_done["digital_signature"] = True
                elif entry in ["content_commitment", "non_repudiation", "contentCommitment", "nonRepudiation"]:
                    if self.module.params['keyUsage_only'][entry] != key_usage.content_commitment:
                        self.module.fail_json(
                            msg="Mismatch for the content commitment key usage (expected %s, got %s)" %
                            (self.module.params['keyUsage_only'][entry], key_usage.content_commitment))
                    flags_done["content_commitment"] = True
                elif entry in ["key_encipherment", "keyEncipherment"]:
                    if self.module.params['keyUsage_only'][entry] != key_usage.key_encipherment:
                        self.module.fail_json(
                            msg="Mismatch for the key encipherment key usage (expected %s, got %s)" %
                            (self.module.params['keyUsage_only'][entry], key_usage.key_encipherment))
                    flags_done["key_encipherment"] = True
                elif entry in ["data_encipherment", "dataEncipherment"]:
                    if self.module.params['keyUsage_only'][entry] != key_usage.data_encipherment:
                        self.module.fail_json(
                            msg="Mismatch for the data encipherment key usage (expected %s, got %s)" %
                            (self.module.params['keyUsage_only'][entry], key_usage.data_encipherment))
                    flags_done["data_encipherment"] = True
                elif entry in ["key_agreement", "keyAgreement"]:
                    if self.module.params['keyUsage_only'][entry] != key_usage.key_agreement:
                        self.module.fail_json(
                            msg="Mismatch for the key agreement key usage (expected %s, got %s)" %
                            (self.module.params['keyUsage_only'][entry], key_usage.key_agreement))
                    flags_done["key_agreement"] = True
                elif entry in ["key_cert_sign", "keyCertSign"]:
                    if self.module.params['keyUsage_only'][entry] != key_usage.key_cert_sign:
                        self.module.fail_json(
                            msg="Mismatch for the key cert sign key usage (expected %s, got %s)" %
                            (self.module.params['keyUsage_only'][entry], key_usage.key_cert_sign))
                    flags_done["key_cert_sign"] = True
                elif entry in ["crl_sign", "cRLSign"]:
                    if self.module.params['keyUsage_only'][entry] != key_usage.crl_sign:
                        self.module.fail_json(
                            msg="Mismatch for the crl sign key usage (expected %s, got %s)" %
                            (self.module.params['keyUsage_only'][entry], key_usage.crl_sign))
                    flags_done["crl_sign"] = True
                elif entry in ["encipher_only", "encipherOnly"]:
                    if self.module.params['keyUsage_only'][entry] and not key_usage.key_agreement:
                        self.module.fail_json(
                            msg="The certificate has disabled the key_agreement usage. Checking the encipher only attribute doesn't make sense.")
                    else:
                        if self.module.params['keyUsage_only'][entry] != key_usage.encipher_only:
                            self.module.fail_json(
                                msg="Mismatch for the encipher only key usage (expected %s, got %s)" %
                                (self.module.params['keyUsage_only'][entry], key_usage.encipher_only))
                        flags_done["encipher_only"] = True
                elif entry in ["decipher_only", "decipherOnly"]:
                    if self.module.params['keyUsage_only'][entry] and not key_usage.key_agreement:
                        self.module.fail_json(
                            msg="The certificate has disabled the key_agreement usage. Checking the decipher only attribute doesn't make sense.")
                    else:
                        if self.module.params['keyUsage_only'][entry] != key_usage.decipher_only:
                            self.module.fail_json(
                                msg="Mismatch for the decipher only key usage (expected %s, got %s)" %
                                (self.module.params['keyUsage_only'][entry], key_usage.decipher_only))
                        flags_done["decipher_only"] = True
                else:
                    self.module.fail_json(msg='Could not parse the keyUsage_only entry "%s"' % self.module.params['keyUsage_only'][entry])
            for flag in flags_done:
                if flags_done[flag] is False:
                    if flag == "digital_signature" and key_usage.digital_signature is True:
                        self.module.fail_json(msg="The digital_signature key usage was set to True without being explicitly specified.")
                    elif flag == "content_commitment" and key_usage.content_commitment is True:
                        self.module.fail_json(msg="The content_commitment key usage was set to True without being explicitly specified.")
                    elif flag == "key_encipherment" and key_usage.key_encipherment is True:
                        self.module.fail_json(msg="The key_encipherment key usage was set to True without being explicitly specified.")
                    elif flag == "data_encipherment" and key_usage.data_encipherment is True:
                        self.module.fail_json(msg="The data_encipherment key usage was set to True without being explicitly specified.")
                    elif flag == "key_agreement" and key_usage.key_agreement is True:
                        self.module.fail_json(msg="The key_agreement key usage was set to True without being explicitly specified.")
                    elif flag == "key_cert_sign" and key_usage.key_cert_sign is True:
                        self.module.fail_json(msg="The key_cert_sign key usage was set to True without being explicitly specified.")
                    elif flag == "crl_sign" and key_usage.crl_sign is True:
                        self.module.fail_json(msg="The crl_sign key usage was set to True without being explicitly specified.")
                    elif flag == "encipher_only" and key_usage.encipher_only is True:
                        self.module.fail_json(msg="The encipher_only key usage was set to True without being explicitly specified.")
                    elif flag == "decipher_only" and key_usage.decipher_only is True:
                        self.module.fail_json(msg="The decipher_only key usage was set to True without being explicitly specified.")

        # extendedKeyUsage extension
        name_to_oid = {
            # Key: OID name, value: OID dotted string
            "server_auth": "1.3.6.1.5.5.7.3.1",
            "serverAuth": "1.3.6.1.5.5.7.3.1",
            "client_auth": "1.3.6.1.5.5.7.3.2",
            "clientAuth": "1.3.6.1.5.5.7.3.2",
            "code_signing": "1.3.6.1.5.5.7.3.3",
            "codeSigning": "1.3.6.1.5.5.7.3.3",
            "email_protection": "1.3.6.1.5.5.7.3.4",
            "emailProtection": "1.3.6.1.5.5.7.3.4",
            "time_stamping": "1.3.6.1.5.5.7.3.8",
            "timeStamping": "1.3.6.1.5.5.7.3.8",
            "ocsp_signing": "1.3.6.1.5.5.7.3.9",
            "OCSPsigning": "1.3.6.1.5.5.7.3.9",
        }

        if use_cryptography and self.module.params['extendedKeyUsage_contains'] is not None:
            # 2.5.29.37 is the OID for extendedKeyUsage
            # it is available as varible in versions >= 1.0
            extended_key_usage = crypto_cert.extensions.get_extension_for_oid(x509.ObjectIdentifier("2.5.29.37"))
            extended_key_usage_oids = [oid.dotted_string for oid in extended_key_usage.value]
            oid_only = []
            # at least 1 digit, followed by 0 or more instances of at least one digit with a literal dot in front
            # ^ and $ match the beginning/end of the string
            oid_pattern = re.compile("^\d+(\.\d+)*$")
            for entry in self.module.params['extendedKeyUsage_contains']:
                if entry in name_to_oid:
                    oid_only.append(name_to_oid[entry])
                else:
                    if not oid_pattern.match(entry):
                        self.module.fail_json(msg="Unknown extendedKeyUsage OID name: %s" % entry)
                    else:
                        oid_only.append(entry)
            for entry in oid_only:
                if entry not in extended_key_usage_oids:
                    self.module.fail_json(
                        msg="The required extendedKeyUsage object with the OID %s was not found in the certificate (existing OIDs: %s)" %
                        (entry, extended_key_usage_oids))

        if use_cryptography and self.module.params['extendedKeyUsage_only'] is not None:
            # 2.5.29.37 is the OID for extendedKeyUsage
            # it is available as varible in versions >= 1.0
            extended_key_usage = crypto_cert.extensions.get_extension_for_oid(x509.ObjectIdentifier("2.5.29.37"))
            extended_key_usage_oids = [oid.dotted_string for oid in extended_key_usage.value]
            oid_only = []
            # at least 1 digit, followed by 0 or more instances of one or more digits with a dot in front
            # ^ and $ match the beginning/end of the string
            oid_pattern = re.compile("^\d+(\.\d+)*$")
            for entry in self.module.params['extendedKeyUsage_only']:
                if entry in name_to_oid:
                    oid_only.append(name_to_oid[entry])
                else:
                    if not oid_pattern.match(entry):
                        self.module.fail_json(msg="Unknown extendedKeyUsage OID name: %s" % entry)
                    else:
                        oid_only.append(entry)
            if set(oid_only) != set(extended_key_usage_oids):
                self.module.fail_json(
                    msg="The required extendedKeyUsage object with the OID %s was not found in the certificate (existing OIDs: %s)" %
                    (entry, extended_key_usage_oids))

        # subjectAltName extension
        if use_cryptography and self.module.params['subjectAltName_contains'] is not None:
            # 2.5.29.17 is the OID for subjectAlternativeName
            # it is available as varible in versions >= 1.0
            san = crypto_cert.extensions.get_extension_for_oid(x509.ObjectIdentifier("2.5.29.17"))
            san_dns = san.value.get_values_for_type(x509.GeneralName)
            for entry in self.module.params['subjectAltName_contains']:
                if entry not in san_dns:
                    self.module.fail_json(
                        msg="The required entry couldn't be found in subjectAltName (was looking for %s in %s)" %
                        (entry, san_dns))

        if use_cryptography and self.module.params['subjectAltName_only'] is not None:
            # 2.5.29.17 is the OID for subjectAlternativeName
            # it is available as varible in versions >= 1.0
            san = crypto_cert.extensions.get_extension_for_oid(x509.ObjectIdentifier("2.5.29.17"))
            san_dns = san.value.get_values_for_type(x509.GeneralName)
            if set(san_dns) != set(self.module.params['subjectAltName_only']):
                self.module.fail_json(
                    msg="Not all required entries could be found in subjectAltName (was looking for %s in %s)" %
                    (self.module.params['subjectAltName_only'], san_dns))


class SelfSignedCertificate(Certificate):
    '''Generate the self-signed certificate.'''

    def __init__(self, module):
        Certificate.__init__(self, module)
        self.serial_number = randint(1000, 99999)
        self.notBefore = module.params['selfsigned_notBefore']
        self.notAfter = module.params['selfsigned_notAfter']
        self.selfsigned_digest = module.params['selfsigned_digest']
        self.backup = module.params['backup']
        self.request = self.load_csr()
        self.privatekey = self.load_privatekey()
        self.certificate = None

    def load_privatekey(self):
        '''Load the privatekey object from buffer.'''
        try:
            privatekey_content = open(self.privatekey_path).read()
        except EnvironmentError:
            self.module.fail_json(msg='Could not read file at %s' % self.privatekey_path)
        return crypto.load_privatekey(crypto.FILETYPE_PEM, privatekey_content)

    def load_csr(self):
        '''Load the certificate signing request object from buffer.'''
        try:
            csr_content = open(self.csr_path).read()
        except EnvironmentError:
                self.module.fail_json(msg='Could not read file at %s' % self.csr_path)
        return crypto.load_certificate_request(crypto.FILETYPE_PEM, csr_content)

    def generate(self):

        if not self.force and os.path.exists(self.path):
            self.changed = False
            return

        cert = crypto.X509()
        cert.set_serial_number(self.serial_number)
        cert.gmtime_adj_notBefore(self.notBefore)
        cert.gmtime_adj_notAfter(self.notAfter)
        cert.set_subject(self.request.get_subject())
        cert.set_version(self.request.get_version() - 1)
        cert.set_pubkey(self.request.get_pubkey())
        try:
            # NOTE: This is only available starting from pyOpenSSL >= 0.15
            cert.add_extensions(self.request.get_extensions())
        except NameError as e:
            raise CertificateError(e)
        cert.sign(self.privatekey, self.selfsigned_digest)
        self.certificate = cert

        self.backupdest = ""
        if self.changed and not self.module.check_mode:
            if self.backup and os.path.exists(self.path):
                self.backupdest = module.backup_local(self.path)
            try:
                with open(self.path, 'w') as cert_file:
                    cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, self.certificate))
            except EnvironmentError:
                self.module.fail_json(msg='Could not write to file at %s' % self.path)

    def dump(self):

        result = {
            'changed': self.changed,
            'cert_path': self.path,
            'notBefore': self.notBefore,
            'notAfter': self.notAfter,
            'serial_number': self.serial_number,
            'backup': self.backupdest,
            'warnings': self.warnings,
        }

        return result


class AssertOnlyCertificate(Certificate):
    '''validate the supplied certificate.'''

    def __init__(self, module):
        Certificate.__init__(self, module)

    def generate(self):
        '''Don't generate anything'''

        # This provider can not change anything, it only reads data
        self.changed = False

    def dump(self):

        result = {
            'changed': self.changed,
            'cert_path': self.path,
            'warnings': self.warnings,
        }

        return result


class LetsEncryptCertificate(Certificate):
    '''Retrieve Let's Encrypt certificate.'''

    def __init__(self, module):
        Certificate.__init__(self, module)
        self.accountkey = module.params['letsencrypt_accountkey']
        self.challenge_path = module.params['letsencrypt_challenge_path']

    def generate(self):
        if not self.force and os.path.exists(self.path):
            self.changed = False
            return

        self.backupdest = ""
        if self.changed and not self.module.check_mode:
            if self.backup and os.path.exists(self.path):
                self.backupdest = module.backup_local(self.path)

            # TODO (spredzy): Ugly part should be done directly by interacting
            # with the acme protocol through python-acme
            try:
                p = subprocess.Popen([
                    'acme-tiny',
                    '--account-key', self.accountkey,
                    '--csr', self.csr_path,
                    '--acme-dir', self.challenge_path], stdout=subprocess.PIPE)
                crt = p.communicate()[0]
                with open(self.path, 'w') as certfile:
                    certfile.write(str(crt))
            except OSError as e:
                raise CertificateError(e)

    def dump(self):

        result = {
            'changed': self.changed,
            'cert_path': self.path,
            'account_key': self.accountkey,
            'backup': self.backupdest,
            'warnings': self.warnings,
        }

        return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            path=dict(required=True, aliases=['dest', 'destfile'], type='path'),
            provider=dict(required=True, choices=['selfsigned', 'assertonly', 'letsencrypt'], type='str'),
            force=dict(default=False, type='bool'),
            backup=dict(default=False, type='bool'),
            csr_path=dict(type='path'),

            # General properties of a certificate
            privatekey_path=dict(type='path'),
            signature_algorithms=dict(type='list'),
            issuer=dict(type='dict'),
            subject=dict(type='dict'),
            has_expired=dict(type='bool'),
            version=dict(type='int'),
            warn=dict(default=True, type='bool'),
            valid_at=dict(type='str'),
            starts_at=dict(type='str'),
            invalid_at=dict(type='str'),
            expires_at=dict(type='str'),
            valid_in=dict(type='int'),
            keyUsage_contains=dict(type='dict'),
            keyUsage_only=dict(type='dict'),
            extendedKeyUsage_contains=dict(type='list'),
            extendedKeyUsage_only=dict(type='list'),
            subjectAltName_contains=dict(type='list'),
            subjectAltName_only=dict(type='list'),

            # provider: selfsigned
            selfsigned_digest=dict(default='sha256', type='str'),
            selfsigned_notBefore=dict(default=0, type='int'),
            selfsigned_notAfter=dict(default=315360000, type='int'),

            # provider: letsencrypt
            letsencrypt_accountkey=dict(type='path'),
            letsencrypt_challenge_path=dict(type='path'),
        ),
        mutually_exclusive=[
            ["keyUsage_contains", "keyUsage_only"],
            ["extendedKeyUsage_contains", "extendedKeyUsage_only"],
            ["subjectAltName_contains", "subjectAltName_only"]],
        supports_check_mode=True
    )

    if not pyopenssl_found:
        module.fail_json(msg='The python pyOpenSSL library is required')

    if not cryptography_found:
        module.fail_json(msg='The python cryptography library is required')

    provider = module.params['provider']
    if provider == 'selfsigned':
        if module.params['csr_path'] is None:
            module.fail_json(msg='No csr provided for selfsigned provider')
        cert = SelfSignedCertificate(module)
    elif provider == 'letsencrypt':
        if module.params['csr_path'] is None:
            module.fail_json(msg='No csr provided for letsencrypt provider')
        if module.params['letsencrypt_accountkey'] is None:
            module.fail_json(msg='No letsencrypt_accountkey provided for letsencrypt provider')
        if module.params['letsencrypt_challenge_path'] is None:
            module.fail_json(msg='No letsencrypt_challenge_path provided for letsencrypt provider')
        cert = LetsEncryptCertificate(module)
    else:
        cert = AssertOnlyCertificate(module)

    if module.params['state'] == 'present':
        try:
            if not module.check_mode:
                cert.generate()
        except CertificateError as exc:
            module.fail_json(msg='An error occured while generating the certificate. More details: %s' % to_native(exc))
        cert.check()
    else:
        if not module.check_mode:
            cert.remove()

    result = cert.dump()

    module.exit_json(**result)


if __name__ == "__main__":
    main()
