#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: acme_challenge_cert_helper
author: "Felix Fontein (@felixfontein)"
version_added: "2.7"
short_description: Prepare certificates required for ACME challenges such as C(tls-alpn-01)
description:
   - "Prepares certificates for ACME challenges such as C(tls-alpn-01)."
   - "The raw data is provided by the M(acme_certificate) module, and needs to be
      converted to a certificate to be used for challenge validation. This module
      provides a simple way to generate the required certificates."
seealso:
  - name: Automatic Certificate Management Environment (ACME)
    description: The specification of the ACME protocol (RFC 8555).
    link: https://tools.ietf.org/html/rfc8555
  - name: ACME TLS ALPN Challenge Extension
    description: The specification of the C(tls-alpn-01) challenge (RFC 8737).
    link: https://www.rfc-editor.org/rfc/rfc8737.html
requirements:
   - "cryptography >= 1.3"
options:
  challenge:
    description:
      - "The challenge type."
    type: str
    required: yes
    choices:
    - tls-alpn-01
  challenge_data:
    description:
      - "The C(challenge_data) entry provided by M(acme_certificate) for the challenge."
    type: dict
    required: yes
  private_key_src:
    description:
      - "Path to a file containing the private key file to use for this challenge
         certificate."
      - "Mutually exclusive with C(private_key_content)."
    type: path
  private_key_content:
    description:
      - "Content of the private key to use for this challenge certificate."
      - "Mutually exclusive with C(private_key_src)."
    type: str
'''

EXAMPLES = '''
- name: Create challenges for a given CRT for sample.com
  acme_certificate:
    account_key_src: /etc/pki/cert/private/account.key
    challenge: tls-alpn-01
    csr: /etc/pki/cert/csr/sample.com.csr
    dest: /etc/httpd/ssl/sample.com.crt
  register: sample_com_challenge

- name: Create certificates for challenges
  acme_challenge_cert_helper:
    challenge: tls-alpn-01
    challenge_data: "{{ item.value['tls-alpn-01'] }}"
    private_key_src: /etc/pki/cert/key/sample.com.key
  loop: "{{ sample_com_challenge.challenge_data | dictsort }}"
  register: sample_com_challenge_certs

- name: Install challenge certificates
  # We need to set up HTTPS such that for the domain,
  # regular_certificate is delivered for regular connections,
  # except if ALPN selects the "acme-tls/1"; then, the
  # challenge_certificate must be delivered.
  # This can for example be achieved with very new versions
  # of NGINX; search for ssl_preread and
  # ssl_preread_alpn_protocols for information on how to
  # route by ALPN protocol.
  ...:
    domain: "{{ item.domain }}"
    challenge_certificate: "{{ item.challenge_certificate }}"
    regular_certificate: "{{ item.regular_certificate }}"
    private_key: /etc/pki/cert/key/sample.com.key
  loop: "{{ sample_com_challenge_certs.results }}"

- name: Create certificate for a given CSR for sample.com
  acme_certificate:
    account_key_src: /etc/pki/cert/private/account.key
    challenge: tls-alpn-01
    csr: /etc/pki/cert/csr/sample.com.csr
    dest: /etc/httpd/ssl/sample.com.crt
    data: "{{ sample_com_challenge }}"
'''

RETURN = '''
domain:
  description:
    - "The domain the challenge is for. The certificate should be provided if
       this is specified in the request's the C(Host) header."
  returned: always
  type: str
identifier_type:
  description:
    - "The identifier type for the actual resource identifier. Will be C(dns)
       or C(ip)."
  returned: always
  type: str
  version_added: "2.8"
identifier:
  description:
    - "The identifier for the actual resource. Will be a domain name if the
       type is C(dns), or an IP address if the type is C(ip)."
  returned: always
  type: str
  version_added: "2.8"
challenge_certificate:
  description:
    - "The challenge certificate in PEM format."
  returned: always
  type: str
regular_certificate:
  description:
    - "A self-signed certificate for the challenge domain."
    - "If no existing certificate exists, can be used to set-up
       https in the first place if that is needed for providing
       the challenge."
  returned: always
  type: str
'''

from ansible.module_utils.acme import (
    ModuleFailException,
    read_file,
)

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_bytes, to_text

import base64
import datetime
import sys
import traceback

CRYPTOGRAPHY_IMP_ERR = None
try:
    import cryptography
    import cryptography.hazmat.backends
    import cryptography.hazmat.primitives.serialization
    import cryptography.hazmat.primitives.asymmetric.rsa
    import cryptography.hazmat.primitives.asymmetric.ec
    import cryptography.hazmat.primitives.asymmetric.padding
    import cryptography.hazmat.primitives.hashes
    import cryptography.hazmat.primitives.asymmetric.utils
    import cryptography.x509
    import cryptography.x509.oid
    import ipaddress
    from distutils.version import LooseVersion
    HAS_CRYPTOGRAPHY = (LooseVersion(cryptography.__version__) >= LooseVersion('1.3'))
    _cryptography_backend = cryptography.hazmat.backends.default_backend()
except ImportError as dummy:
    CRYPTOGRAPHY_IMP_ERR = traceback.format_exc()
    HAS_CRYPTOGRAPHY = False


# Convert byte string to ASN1 encoded octet string
if sys.version_info[0] >= 3:
    def encode_octet_string(octet_string):
        if len(octet_string) >= 128:
            raise ModuleFailException('Cannot handle octet strings with more than 128 bytes')
        return bytes([0x4, len(octet_string)]) + octet_string
else:
    def encode_octet_string(octet_string):
        if len(octet_string) >= 128:
            raise ModuleFailException('Cannot handle octet strings with more than 128 bytes')
        return b'\x04' + chr(len(octet_string)) + octet_string


def main():
    module = AnsibleModule(
        argument_spec=dict(
            challenge=dict(type='str', required=True, choices=['tls-alpn-01']),
            challenge_data=dict(type='dict', required=True),
            private_key_src=dict(type='path'),
            private_key_content=dict(type='str', no_log=True),
        ),
        required_one_of=(
            ['private_key_src', 'private_key_content'],
        ),
        mutually_exclusive=(
            ['private_key_src', 'private_key_content'],
        ),
    )
    if not HAS_CRYPTOGRAPHY:
        module.fail_json(msg=missing_required_lib('cryptography >= 1.3'), exception=CRYPTOGRAPHY_IMP_ERR)

    try:
        # Get parameters
        challenge = module.params['challenge']
        challenge_data = module.params['challenge_data']

        # Get hold of private key
        private_key_content = module.params.get('private_key_content')
        if private_key_content is None:
            private_key_content = read_file(module.params['private_key_src'])
        else:
            private_key_content = to_bytes(private_key_content)
        try:
            private_key = cryptography.hazmat.primitives.serialization.load_pem_private_key(private_key_content, password=None, backend=_cryptography_backend)
        except Exception as e:
            raise ModuleFailException('Error while loading private key: {0}'.format(e))

        # Some common attributes
        domain = to_text(challenge_data['resource'])
        identifier_type, identifier = to_text(challenge_data.get('resource_original', 'dns:' + challenge_data['resource'])).split(':', 1)
        subject = issuer = cryptography.x509.Name([])
        not_valid_before = datetime.datetime.utcnow()
        not_valid_after = datetime.datetime.utcnow() + datetime.timedelta(days=10)
        if identifier_type == 'dns':
            san = cryptography.x509.DNSName(identifier)
        elif identifier_type == 'ip':
            san = cryptography.x509.IPAddress(ipaddress.ip_address(identifier))
        else:
            raise ModuleFailException('Unsupported identifier type "{0}"'.format(identifier_type))

        # Generate regular self-signed certificate
        regular_certificate = cryptography.x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            cryptography.x509.random_serial_number()
        ).not_valid_before(
            not_valid_before
        ).not_valid_after(
            not_valid_after
        ).add_extension(
            cryptography.x509.SubjectAlternativeName([san]),
            critical=False,
        ).sign(
            private_key,
            cryptography.hazmat.primitives.hashes.SHA256(),
            _cryptography_backend
        )

        # Process challenge
        if challenge == 'tls-alpn-01':
            value = base64.b64decode(challenge_data['resource_value'])
            challenge_certificate = cryptography.x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                cryptography.x509.random_serial_number()
            ).not_valid_before(
                not_valid_before
            ).not_valid_after(
                not_valid_after
            ).add_extension(
                cryptography.x509.SubjectAlternativeName([san]),
                critical=False,
            ).add_extension(
                cryptography.x509.UnrecognizedExtension(
                    cryptography.x509.ObjectIdentifier("1.3.6.1.5.5.7.1.31"),
                    encode_octet_string(value),
                ),
                critical=True,
            ).sign(
                private_key,
                cryptography.hazmat.primitives.hashes.SHA256(),
                _cryptography_backend
            )

        module.exit_json(
            changed=True,
            domain=domain,
            identifier_type=identifier_type,
            identifier=identifier,
            challenge_certificate=challenge_certificate.public_bytes(cryptography.hazmat.primitives.serialization.Encoding.PEM),
            regular_certificate=regular_certificate.public_bytes(cryptography.hazmat.primitives.serialization.Encoding.PEM)
        )
    except ModuleFailException as e:
        e.do_fail(module)


if __name__ == '__main__':
    main()
