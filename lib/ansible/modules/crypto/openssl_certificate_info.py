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
module: openssl_certificate_info
version_added: '2.8'
short_description: Provide information of OpenSSL X.509 certificates
description:
    - This module allows one to query information on OpenSSL certificates.
    - It uses the pyOpenSSL or cryptography python library to interact with OpenSSL. If both the
      cryptography and PyOpenSSL libraries are available (and meet the minimum version requirements)
      cryptography will be preferred as a backend over PyOpenSSL (unless the backend is forced with
      C(select_crypto_backend))
requirements:
    - PyOpenSSL >= 0.15 or cryptography >= 1.6
author:
  - Felix Fontein (@felixfontein)
  - Yanis Guenane (@Spredzy)
  - Markus Teufelberger (@MarkusTeufelberger)
options:
    path:
        description:
            - Remote absolute path where the certificate file is loaded from.
        type: path
        required: true
    valid_at:
        description:
            - A dict of names mapping to time specifications. Every time specified here
              will be checked whether the certificate is valid at this point. See the
              C(valid_at) return value for informations on the result.
            - Time can be specified either as relative time or as absolute timestamp.
            - Time will always be interpreted as UTC.
            - Valid format is C([+-]timespec | ASN.1 TIME) where timespec can be an integer
              + C([w | d | h | m | s]) (e.g. C(+32w1d2h), and ASN.1 TIME (i.e. pattern C(YYYYMMDDHHMMSSZ)).
              Note that all timestamps will be treated as being in UTC.

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
    - All timestamp values are provided in ASN.1 TIME format, i.e. following the C(YYYYMMDDHHMMSSZ) pattern.
      They are all in UTC.
seealso:
- module: openssl_certificate
'''

EXAMPLES = r'''
- name: Generate a Self Signed OpenSSL certificate
  openssl_certificate:
    path: /etc/ssl/crt/ansible.com.crt
    privatekey_path: /etc/ssl/private/ansible.com.pem
    csr_path: /etc/ssl/csr/ansible.com.csr
    provider: selfsigned

- name: Get information on generated certificate
  openssl_certificate_info:
    path: /etc/ssl/crt/ansible.com.crt
  register: result

- name: Dump information
  debug:
    var: result

- name: Check that certificate is valid tomorrow, but not in three weeks
  openssl_certificate_info:
    path: /etc/ssl/crt/ansible.com.crt
    valid_at:
      point_1: "+1d"
      point_2: "+3w"
  register: result
- assert:
    that:
      - result.valid_at.point_1      # valid in one day
      - not result.valid_at.point_2  # not valid in three weeks
'''

RETURN = r'''
filename:
    description: Path to the generated Certificate
    returned: changed or success
    type: str
    sample: /etc/ssl/crt/www.ansible.com.crt
'''


import abc
import datetime
import os
import traceback
from distutils.version import LooseVersion

from ansible.module_utils import crypto as crypto_utils
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native, to_text

MINIMAL_CRYPTOGRAPHY_VERSION = '1.6'
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
except ImportError:
    CRYPTOGRAPHY_IMP_ERR = traceback.format_exc()
    CRYPTOGRAPHY_FOUND = False
else:
    CRYPTOGRAPHY_FOUND = True


TIMESTAMP_FORMAT = "%Y%m%d%H%M%SZ"


def get_relative_time_option(input_string, input_name):
    """Return an ASN1 formatted string if a relative timespec
       or an ASN1 formatted string is provided."""
    result = input_string
    if result.startswith("+") or result.startswith("-"):
        return crypto_utils.convert_relative_to_datetime(result)
    if result is None:
        raise crypto_utils.CertificateError(
            'The timespec "%s" for %s is not valid' %
            input_string, input_name)
    for date_fmt in ['%Y%m%d%H%M%SZ', '%Y%m%d%H%MZ', '%Y%m%d%H%M%S%z', '%Y%m%d%H%M%z']:
        try:
            result = datetime.datetime.strptime(input_string, date_fmt)
            break
        except ValueError:
            pass

    if not isinstance(result, datetime.datetime):
        raise crypto_utils.CertificateError(
            'The time spec "%s" for %s is invalid' %
            (input_string, input_name)
        )
    return result


class CertificateInfo(crypto_utils.OpenSSLObject):
    def __init__(self, module, backend):
        super(CertificateInfo, self).__init__(
            module.params['path'],
            'present',
            False,
            module.check_mode,
        )
        self.backend = backend
        self.module = module

        self.valid_at = module.params['valid_at']
        if self.valid_at:
            for k, v in self.valid_at.items():
                if not isinstance(v, string_types):
                    self.module.fail_json(
                        msg='The value for valid_at.{0} must be of type string (got {1})'.format(k, type(v))
                    )
                self.valid_at[k] = get_relative_time_option(v, 'valid_at.{0}'.format(k))

    def generate(self):
        # Empty method because crypto_utils.OpenSSLObject wants this
        pass

    def dump(self):
        # Empty method because crypto_utils.OpenSSLObject wants this
        pass

    @abc.abstractmethod
    def _get_signature_algorithm(self):
        pass

    @abc.abstractmethod
    def _get_subject(self):
        pass

    @abc.abstractmethod
    def _get_issuer(self):
        pass

    @abc.abstractmethod
    def _get_version(self):
        pass

    @abc.abstractmethod
    def _get_key_usage(self):
        pass

    @abc.abstractmethod
    def _get_extended_key_usage(self):
        pass

    @abc.abstractmethod
    def _get_subject_alt_name(self):
        pass

    @abc.abstractmethod
    def _get_not_before(self):
        pass

    @abc.abstractmethod
    def _get_not_after(self):
        pass

    @abc.abstractmethod
    def _get_public_key(self, binary):
        pass

    def get_info(self):
        result = dict()
        self.cert = crypto_utils.load_certificate(self.path, backend=self.backend)

        result['signature_algorithm'] = self._get_signature_algorithm()
        result['subject'] = self._get_subject()
        result['issuer'] = self._get_issuer()
        result['version'] = self._get_version()
        result['key_usage'], result['key_usage_critical'] = self._get_key_usage()
        result['extended_key_usage'], result['extended_key_usage_critical'] = self._get_extended_key_usage()
        result['subject_alt_name'], result['subject_alt_name_critical'] = self._get_subject_alt_name()

        not_before = self._get_not_before()
        not_after = self._get_not_after()
        result['not_before'] = not_before.strftime(TIMESTAMP_FORMAT)
        result['not_after'] = not_after.strftime(TIMESTAMP_FORMAT)
        result['expired'] = not_after < datetime.datetime.utcnow()

        result['valid_at'] = dict()
        if self.valid_at:
            for k, v in self.valid_at.items():
                result['valid_at'][k] = not_before <= v <= not_after

        result['public_key'] = self._get_public_key(binary=False)
        result['public_key_fingerprints'] = crypto_utils.get_fingerprint_of_bytes(self._get_public_key(binary=True))

        return result


class CertificateInfoCryptography(CertificateInfo):
    """Validate the supplied cert, using the cryptography backend"""
    def __init__(self, module):
        super(CertificateInfoCryptography, self).__init__(module, 'cryptography')

    def _get_signature_algorithm(self):
        return crypto_utils.crpytography_oid_to_name(self.cert.signature_algorithm_oid)

    def _get_subject(self):
        result = dict()
        for attribute in self.cert.subject:
            result[crypto_utils.crpytography_oid_to_name(attribute.oid)] = attribute.value
        return result

    def _get_issuer(self):
        result = dict()
        for attribute in self.cert.issuer:
            result[crypto_utils.crpytography_oid_to_name(attribute.oid)] = attribute.value
        return result

    def _get_version(self):
        if self.cert.version == x509.Version.v1:
            return 1
        if self.cert.version == x509.Version.v3:
            return 3
        return "unknown"

    def _get_key_usage(self):
        try:
            current_key_ext = self.cert.extensions.get_extension_for_class(x509.KeyUsage)
            current_key_usage = current_key_ext.value
            key_usage = dict(
                digital_signature=current_key_usage.digital_signature,
                content_commitment=current_key_usage.content_commitment,
                key_encipherment=current_key_usage.key_encipherment,
                data_encipherment=current_key_usage.data_encipherment,
                key_agreement=current_key_usage.key_agreement,
                key_cert_sign=current_key_usage.key_cert_sign,
                crl_sign=current_key_usage.crl_sign,
                encipher_only=False,
                decipher_only=False,
            )
            if key_usage['key_agreement']:
                key_usage.update(dict(
                    encipher_only=current_key_usage.encipher_only,
                    decipher_only=current_key_usage.decipher_only
                ))

            key_usage_names = dict(
                digital_signature='Digital Signature',
                content_commitment='Non Repudiation',
                key_encipherment='Key Encipherment',
                data_encipherment='Data Encipherment',
                key_agreement='Key Agreement',
                key_cert_sign='Certificate Sign',
                crl_sign='CRL Sign',
                encipher_only='Encipher Only',
                decipher_only='Decipher Only',
            )
            return sorted([
                key_usage_names[name] for name, value in key_usage.items() if value
            ]), current_key_ext.critical
        except cryptography.x509.ExtensionNotFound:
            return None, False

    def _get_extended_key_usage(self):
        try:
            ext_keyusage_ext = self.cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage)
            return sorted([
                crypto_utils.crpytography_oid_to_name(eku) for eku in ext_keyusage_ext.value
            ]), ext_keyusage_ext.critical
        except cryptography.x509.ExtensionNotFound:
            return None, False

    def _get_subject_alt_name(self):
        try:
            san_ext = self.cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
            result = [crypto_utils.cryptography_decode_name(san) for san in san_ext.value]
            return result, san_ext.critical
        except cryptography.x509.ExtensionNotFound:
            return None, False

    def _get_not_before(self):
        return self.cert.not_valid_before

    def _get_not_after(self):
        return self.cert.not_valid_after

    def _get_public_key(self, binary):
        return self.cert.public_key().public_bytes(
            serialization.Encoding.DER if binary else serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        )


class CertificateInfoPyOpenSSL(CertificateInfo):
    """validate the supplied certificate."""

    def __init__(self, module):
        super(CertificateInfoPyOpenSSL, self).__init__(module, 'pyopenssl')

    def _get_signature_algorithm(self):
        return to_text(self.cert.get_signature_algorithm())

    def __get_name(self, name):
        result = dict()
        for sub in name.get_components():
            result[crypto_utils.pyopenssl_normalize_name(sub[0])] = to_text(sub[1])
        return result

    def _get_subject(self):
        return self.__get_name(self.cert.get_subject())

    def _get_issuer(self):
        return self.__get_name(self.cert.get_issuer())

    def _get_version(self):
        # Version numbers in certs are off by one:
        # v1: 0, v2: 1, v3: 2 ...
        return self.cert.get_version() + 1

    def _get_key_usage(self):
        for extension_idx in range(0, self.cert.get_extension_count()):
            extension = self.cert.get_extension(extension_idx)
            if extension.get_short_name() == b'keyUsage':
                result = [
                    crypto_utils.pyopenssl_normalize_name(usage.strip()) for usage in to_text(extension, errors='surrogate_or_strict').split(',')
                ]
                return sorted(result), bool(extension.get_critical())
        return None, False

    def _get_extended_key_usage(self):
        for extension_idx in range(0, self.cert.get_extension_count()):
            extension = self.cert.get_extension(extension_idx)
            if extension.get_short_name() == b'extendedKeyUsage':
                result = [
                    crypto_utils.pyopenssl_normalize_name(usage.strip()) for usage in to_text(extension, errors='surrogate_or_strict').split(',')
                ]
                return sorted(result), bool(extension.get_critical())
        return None, False

    def _normalize_san(self, san):
        if san.startswith('IP Address:'):
            san = 'IP:' + san[len('IP Address:'):]
        if san.startswith('IP:'):
            ip = ipaddress.ip_address(san[3:])
            san = 'IP:{0}'.format(ip.compressed)
        return san

    def _get_subject_alt_name(self):
        for extension_idx in range(0, self.cert.get_extension_count()):
            extension = self.cert.get_extension(extension_idx)
            if extension.get_short_name() == b'subjectAltName':
                result = [self._normalize_san(altname.strip()) for altname in
                          to_text(extension, errors='surrogate_or_strict').split(', ')]
                return result, bool(extension.get_critical())
        return None, False

    def _get_not_before(self):
        time_string = to_native(self.cert.get_notBefore())
        return datetime.datetime.strptime(time_string, "%Y%m%d%H%M%SZ")

    def _get_not_after(self):
        time_string = to_native(self.cert.get_notAfter())
        return datetime.datetime.strptime(time_string, "%Y%m%d%H%M%SZ")

    def _get_public_key(self, binary):
        try:
            return crypto.dump_publickey(
                crypto.FILETYPE_ASN1 if binary else crypto.FILETYPE_PEM,
                self.cert.get_pubkey()
            )
        except AttributeError:
            self.module.warn('Your pyOpenSSL version does not support dumping public keys. '
                             'Please upgrade to version 16.0 or newer, or use the cryptography backend.')


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True),
            valid_at=dict(type='dict'),
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

            certificate = CertificateInfoPyOpenSSL(module)
        elif backend == 'cryptography':
            if not CRYPTOGRAPHY_FOUND:
                module.fail_json(msg=missing_required_lib('cryptography'), exception=CRYPTOGRAPHY_IMP_ERR)
            certificate = CertificateInfoCryptography(module)

        result = certificate.get_info()
        module.exit_json(**result)
    except crypto_utils.OpenSSLObjectError as exc:
        module.fail_json(msg=to_native(exc))


if __name__ == "__main__":
    main()
