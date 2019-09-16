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
module: openssl_csr_info
version_added: '2.8'
short_description: Provide information of OpenSSL Certificate Signing Requests (CSR)
description:
    - This module allows one to query information on OpenSSL Certificate Signing Requests (CSR).
    - In case the CSR signature cannot be validated, the module will fail. In this case, all return
      variables are still returned.
    - It uses the pyOpenSSL or cryptography python library to interact with OpenSSL. If both the
      cryptography and PyOpenSSL libraries are available (and meet the minimum version requirements)
      cryptography will be preferred as a backend over PyOpenSSL (unless the backend is forced with
      C(select_crypto_backend))
requirements:
    - PyOpenSSL >= 0.15 or cryptography >= 1.3
author:
  - Felix Fontein (@felixfontein)
  - Yanis Guenane (@Spredzy)
options:
    path:
        description:
            - Remote absolute path where the CSR file is loaded from.
        type: path
        required: true

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
- module: openssl_csr
'''

EXAMPLES = r'''
- name: Generate an OpenSSL Certificate Signing Request
  openssl_csr:
    path: /etc/ssl/csr/www.ansible.com.csr
    privatekey_path: /etc/ssl/private/ansible.com.pem
    common_name: www.ansible.com

- name: Get information on the CSR
  openssl_csr_info:
    path: /etc/ssl/csr/www.ansible.com.csr
  register: result

- name: Dump information
  debug:
    var: result
'''

RETURN = r'''
signature_valid:
    description:
        - Whether the CSR's signature is valid.
        - In case the check returns C(no), the module will fail.
    returned: success
    type: bool
basic_constraints:
    description: Entries in the C(basic_constraints) extension, or C(none) if extension is not present.
    returned: success
    type: list
    sample: "[CA:TRUE, pathlen:1]"
basic_constraints_critical:
    description: Whether the C(basic_constraints) extension is critical.
    returned: success
    type: bool
extended_key_usage:
    description: Entries in the C(extended_key_usage) extension, or C(none) if extension is not present.
    returned: success
    type: list
    sample: "[Biometric Info, DVCS, Time Stamping]"
extended_key_usage_critical:
    description: Whether the C(extended_key_usage) extension is critical.
    returned: success
    type: bool
extensions_by_oid:
    description: Returns a dictionary for every extension OID
    returned: success
    type: complex
    contains:
        critical:
            description: Whether the extension is critical.
            returned: success
            type: bool
        value:
            description: The Base64 encoded value (in DER format) of the extension
            returned: success
            type: str
            sample: "MAMCAQU="
    sample: '{"1.3.6.1.5.5.7.1.24": { "critical": false, "value": "MAMCAQU="}}'
key_usage:
    description: Entries in the C(key_usage) extension, or C(none) if extension is not present.
    returned: success
    type: str
    sample: "[Key Agreement, Data Encipherment]"
key_usage_critical:
    description: Whether the C(key_usage) extension is critical.
    returned: success
    type: bool
subject_alt_name:
    description: Entries in the C(subject_alt_name) extension, or C(none) if extension is not present.
    returned: success
    type: list
    sample: "[DNS:www.ansible.com, IP:1.2.3.4]"
subject_alt_name_critical:
    description: Whether the C(subject_alt_name) extension is critical.
    returned: success
    type: bool
ocsp_must_staple:
    description: C(yes) if the OCSP Must Staple extension is present, C(none) otherwise.
    returned: success
    type: bool
ocsp_must_staple_critical:
    description: Whether the C(ocsp_must_staple) extension is critical.
    returned: success
    type: bool
subject:
    description: The CSR's subject.
    returned: success
    type: dict
    sample: '{"commonName": "www.example.com", "emailAddress": "test@example.com"}'
public_key:
    description: CSR's public key in PEM format
    returned: success
    type: str
    sample: "-----BEGIN PUBLIC KEY-----\nMIICIjANBgkqhkiG9w0BAQEFAAOCAg8A..."
public_key_fingerprints:
    description:
        - Fingerprints of CSR's public key.
        - For every hash algorithm available, the fingerprint is computed.
    returned: success
    type: dict
    sample: "{'sha256': 'd4:b3:aa:6d:c8:04:ce:4e:ba:f6:29:4d:92:a3:94:b0:c2:ff:bd:bf:33:63:11:43:34:0f:51:b0:95:09:2f:63',
              'sha512': 'f7:07:4a:f0:b0:f0:e6:8b:95:5f:f9:e6:61:0a:32:68:f1..."
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
from ansible.module_utils.compat import ipaddress as compat_ipaddress

MINIMAL_CRYPTOGRAPHY_VERSION = '1.3'
MINIMAL_PYOPENSSL_VERSION = '0.15'

PYOPENSSL_IMP_ERR = None
try:
    import OpenSSL
    from OpenSSL import crypto
    PYOPENSSL_VERSION = LooseVersion(OpenSSL.__version__)
    if OpenSSL.SSL.OPENSSL_VERSION_NUMBER >= 0x10100000:
        # OpenSSL 1.1.0 or newer
        OPENSSL_MUST_STAPLE_NAME = b"tlsfeature"
        OPENSSL_MUST_STAPLE_VALUE = b"status_request"
    else:
        # OpenSSL 1.0.x or older
        OPENSSL_MUST_STAPLE_NAME = b"1.3.6.1.5.5.7.1.24"
        OPENSSL_MUST_STAPLE_VALUE = b"DER:30:03:02:01:05"
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


class CertificateSigningRequestInfo(crypto_utils.OpenSSLObject):
    def __init__(self, module, backend):
        super(CertificateSigningRequestInfo, self).__init__(
            module.params['path'],
            'present',
            False,
            module.check_mode,
        )
        self.backend = backend
        self.module = module

    def generate(self):
        # Empty method because crypto_utils.OpenSSLObject wants this
        pass

    def dump(self):
        # Empty method because crypto_utils.OpenSSLObject wants this
        pass

    @abc.abstractmethod
    def _get_subject(self):
        pass

    @abc.abstractmethod
    def _get_key_usage(self):
        pass

    @abc.abstractmethod
    def _get_extended_key_usage(self):
        pass

    @abc.abstractmethod
    def _get_basic_constraints(self):
        pass

    @abc.abstractmethod
    def _get_ocsp_must_staple(self):
        pass

    @abc.abstractmethod
    def _get_subject_alt_name(self):
        pass

    @abc.abstractmethod
    def _get_public_key(self, binary):
        pass

    @abc.abstractmethod
    def _get_all_extensions(self):
        pass

    @abc.abstractmethod
    def _is_signature_valid(self):
        pass

    def get_info(self):
        result = dict()
        self.csr = crypto_utils.load_certificate_request(self.path, backend=self.backend)

        result['subject'] = self._get_subject()
        result['key_usage'], result['key_usage_critical'] = self._get_key_usage()
        result['extended_key_usage'], result['extended_key_usage_critical'] = self._get_extended_key_usage()
        result['basic_constraints'], result['basic_constraints_critical'] = self._get_basic_constraints()
        result['ocsp_must_staple'], result['ocsp_must_staple_critical'] = self._get_ocsp_must_staple()
        result['subject_alt_name'], result['subject_alt_name_critical'] = self._get_subject_alt_name()

        result['public_key'] = self._get_public_key(binary=False)
        pk = self._get_public_key(binary=True)
        result['public_key_fingerprints'] = crypto_utils.get_fingerprint_of_bytes(pk) if pk is not None else dict()

        result['extensions_by_oid'] = self._get_all_extensions()

        result['signature_valid'] = self._is_signature_valid()
        if not result['signature_valid']:
            self.module.fail_json(
                msg='CSR signature is invalid!',
                **result
            )
        return result


class CertificateSigningRequestInfoCryptography(CertificateSigningRequestInfo):
    """Validate the supplied CSR, using the cryptography backend"""
    def __init__(self, module):
        super(CertificateSigningRequestInfoCryptography, self).__init__(module, 'cryptography')

    def _get_subject(self):
        result = dict()
        for attribute in self.csr.subject:
            result[crypto_utils.cryptography_oid_to_name(attribute.oid)] = attribute.value
        return result

    def _get_key_usage(self):
        try:
            current_key_ext = self.csr.extensions.get_extension_for_class(x509.KeyUsage)
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
            ext_keyusage_ext = self.csr.extensions.get_extension_for_class(x509.ExtendedKeyUsage)
            return sorted([
                crypto_utils.cryptography_oid_to_name(eku) for eku in ext_keyusage_ext.value
            ]), ext_keyusage_ext.critical
        except cryptography.x509.ExtensionNotFound:
            return None, False

    def _get_basic_constraints(self):
        try:
            ext_keyusage_ext = self.csr.extensions.get_extension_for_class(x509.BasicConstraints)
            result = []
            result.append('CA:{0}'.format('TRUE' if ext_keyusage_ext.value.ca else 'FALSE'))
            if ext_keyusage_ext.value.path_length is not None:
                result.append('pathlen:{0}'.format(ext_keyusage_ext.value.path_length))
            return sorted(result), ext_keyusage_ext.critical
        except cryptography.x509.ExtensionNotFound:
            return None, False

    def _get_ocsp_must_staple(self):
        try:
            try:
                # This only works with cryptography >= 2.1
                tlsfeature_ext = self.csr.extensions.get_extension_for_class(x509.TLSFeature)
                value = cryptography.x509.TLSFeatureType.status_request in tlsfeature_ext.value
            except AttributeError as dummy:
                # Fallback for cryptography < 2.1
                oid = x509.oid.ObjectIdentifier("1.3.6.1.5.5.7.1.24")
                tlsfeature_ext = self.csr.extensions.get_extension_for_oid(oid)
                value = tlsfeature_ext.value.value == b"\x30\x03\x02\x01\x05"
            return value, tlsfeature_ext.critical
        except cryptography.x509.ExtensionNotFound:
            return None, False

    def _get_subject_alt_name(self):
        try:
            san_ext = self.csr.extensions.get_extension_for_class(x509.SubjectAlternativeName)
            result = [crypto_utils.cryptography_decode_name(san) for san in san_ext.value]
            return result, san_ext.critical
        except cryptography.x509.ExtensionNotFound:
            return None, False

    def _get_public_key(self, binary):
        return self.csr.public_key().public_bytes(
            serialization.Encoding.DER if binary else serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def _get_all_extensions(self):
        return crypto_utils.cryptography_get_extensions_from_csr(self.csr)

    def _is_signature_valid(self):
        return self.csr.is_signature_valid


class CertificateSigningRequestInfoPyOpenSSL(CertificateSigningRequestInfo):
    """validate the supplied CSR."""

    def __init__(self, module):
        super(CertificateSigningRequestInfoPyOpenSSL, self).__init__(module, 'pyopenssl')

    def __get_name(self, name):
        result = dict()
        for sub in name.get_components():
            result[crypto_utils.pyopenssl_normalize_name(sub[0])] = to_text(sub[1])
        return result

    def _get_subject(self):
        return self.__get_name(self.csr.get_subject())

    def _get_extension(self, short_name):
        for extension in self.csr.get_extensions():
            if extension.get_short_name() == short_name:
                result = [
                    crypto_utils.pyopenssl_normalize_name(usage.strip()) for usage in to_text(extension, errors='surrogate_or_strict').split(',')
                ]
                return sorted(result), bool(extension.get_critical())
        return None, False

    def _get_key_usage(self):
        return self._get_extension(b'keyUsage')

    def _get_extended_key_usage(self):
        return self._get_extension(b'extendedKeyUsage')

    def _get_basic_constraints(self):
        return self._get_extension(b'basicConstraints')

    def _get_ocsp_must_staple(self):
        extensions = self.csr.get_extensions()
        oms_ext = [
            ext for ext in extensions
            if to_bytes(ext.get_short_name()) == OPENSSL_MUST_STAPLE_NAME and to_bytes(ext) == OPENSSL_MUST_STAPLE_VALUE
        ]
        if OpenSSL.SSL.OPENSSL_VERSION_NUMBER < 0x10100000:
            # Older versions of libssl don't know about OCSP Must Staple
            oms_ext.extend([ext for ext in extensions if ext.get_short_name() == b'UNDEF' and ext.get_data() == b'\x30\x03\x02\x01\x05'])
        if oms_ext:
            return True, bool(oms_ext[0].get_critical())
        else:
            return None, False

    def _normalize_san(self, san):
        # apparently openssl returns 'IP address' not 'IP' as specifier when converting the subjectAltName to string
        # although it won't accept this specifier when generating the CSR. (https://github.com/openssl/openssl/issues/4004)
        if san.startswith('IP Address:'):
            san = 'IP:' + san[len('IP Address:'):]
        if san.startswith('IP:'):
            ip = compat_ipaddress.ip_address(san[3:])
            san = 'IP:{0}'.format(ip.compressed)
        return san

    def _get_subject_alt_name(self):
        for extension in self.csr.get_extensions():
            if extension.get_short_name() == b'subjectAltName':
                result = [self._normalize_san(altname.strip()) for altname in
                          to_text(extension, errors='surrogate_or_strict').split(', ')]
                return result, bool(extension.get_critical())
        return None, False

    def _get_public_key(self, binary):
        try:
            return crypto.dump_publickey(
                crypto.FILETYPE_ASN1 if binary else crypto.FILETYPE_PEM,
                self.csr.get_pubkey()
            )
        except AttributeError:
            try:
                bio = crypto._new_mem_buf()
                if binary:
                    rc = crypto._lib.i2d_PUBKEY_bio(bio, self.csr.get_pubkey()._pkey)
                else:
                    rc = crypto._lib.PEM_write_bio_PUBKEY(bio, self.csr.get_pubkey()._pkey)
                if rc != 1:
                    crypto._raise_current_error()
                return crypto._bio_to_string(bio)
            except AttributeError:
                self.module.warn('Your pyOpenSSL version does not support dumping public keys. '
                                 'Please upgrade to version 16.0 or newer, or use the cryptography backend.')

    def _get_all_extensions(self):
        return crypto_utils.pyopenssl_get_extensions_from_csr(self.csr)

    def _is_signature_valid(self):
        try:
            return bool(self.csr.verify(self.csr.get_pubkey()))
        except crypto.Error:
            # OpenSSL error means that key is not consistent
            return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True),
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
                module.fail_json(msg=("Can't detect any of the required Python libraries "
                                      "cryptography (>= {0}) or PyOpenSSL (>= {1})").format(
                                          MINIMAL_CRYPTOGRAPHY_VERSION,
                                          MINIMAL_PYOPENSSL_VERSION))

        if backend == 'pyopenssl':
            if not PYOPENSSL_FOUND:
                module.fail_json(msg=missing_required_lib('pyOpenSSL >= {0}'.format(MINIMAL_PYOPENSSL_VERSION)),
                                 exception=PYOPENSSL_IMP_ERR)
            try:
                getattr(crypto.X509Req, 'get_extensions')
            except AttributeError:
                module.fail_json(msg='You need to have PyOpenSSL>=0.15')

            certificate = CertificateSigningRequestInfoPyOpenSSL(module)
        elif backend == 'cryptography':
            if not CRYPTOGRAPHY_FOUND:
                module.fail_json(msg=missing_required_lib('cryptography >= {0}'.format(MINIMAL_CRYPTOGRAPHY_VERSION)),
                                 exception=CRYPTOGRAPHY_IMP_ERR)
            certificate = CertificateSigningRequestInfoCryptography(module)

        result = certificate.get_info()
        module.exit_json(**result)
    except crypto_utils.OpenSSLObjectError as exc:
        module.fail_json(msg=to_native(exc))


if __name__ == "__main__":
    main()
