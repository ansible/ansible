#!/usr/bin/python
# coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: get_certificate
author: "John Westcott IV (@john-westcott-iv)"
version_added: "2.8"
short_description: Get a certificate from a host:port
description:
    - Makes a secure connection and returns information about the presented certificate
    - The module can use the cryptography Python library, or the pyOpenSSL Python
      library. By default, it tries to detect which one is available. This can be
      overridden with the I(select_crypto_backend) option. Please note that the PyOpenSSL
      backend was deprecated in Ansible 2.9 and will be removed in Ansible 2.13."
options:
    host:
      description:
        - The host to get the cert for (IP is fine)
      type: str
      required: true
    ca_cert:
      description:
        - A PEM file containing one or more root certificates; if present, the cert will be validated against these root certs.
        - Note that this only validates the certificate is signed by the chain; not that the cert is valid for the host presenting it.
      type: path
    port:
      description:
        - The port to connect to
      type: int
      required: true
    proxy_host:
      description:
        - Proxy host used when get a certificate.
      type: str
      version_added: 2.9
    proxy_port:
      description:
        - Proxy port used when get a certificate.
      type: int
      default: 8080
      version_added: 2.9
    timeout:
      description:
        - The timeout in seconds
      type: int
      default: 10
    select_crypto_backend:
      description:
        - Determines which crypto backend to use.
        - The default choice is C(auto), which tries to use C(cryptography) if available, and falls back to C(pyopenssl).
        - If set to C(pyopenssl), will try to use the L(pyOpenSSL,https://pypi.org/project/pyOpenSSL/) library.
        - If set to C(cryptography), will try to use the L(cryptography,https://cryptography.io/) library.
      type: str
      default: auto
      choices: [ auto, cryptography, pyopenssl ]
      version_added: "2.9"

notes:
  - When using ca_cert on OS X it has been reported that in some conditions the validate will always succeed.

requirements:
  - "python >= 2.7 when using C(proxy_host)"
  - "cryptography >= 1.6 or pyOpenSSL >= 0.15"
'''

RETURN = '''
cert:
    description: The certificate retrieved from the port
    returned: success
    type: str
expired:
    description: Boolean indicating if the cert is expired
    returned: success
    type: bool
extensions:
    description: Extensions applied to the cert
    returned: success
    type: list
    elements: dict
    contains:
        critical:
            returned: success
            type: bool
            description: Whether the extension is critical.
        asn1_data:
            returned: success
            type: str
            description: The Base64 encoded ASN.1 content of the extnesion.
        name:
            returned: success
            type: str
            description: The extension's name.
issuer:
    description: Information about the issuer of the cert
    returned: success
    type: dict
not_after:
    description: Expiration date of the cert
    returned: success
    type: str
not_before:
    description: Issue date of the cert
    returned: success
    type: str
serial_number:
    description: The serial number of the cert
    returned: success
    type: str
signature_algorithm:
    description: The algorithm used to sign the cert
    returned: success
    type: str
subject:
    description: Information about the subject of the cert (OU, CN, etc)
    returned: success
    type: dict
version:
    description: The version number of the certificate
    returned: success
    type: str
'''

EXAMPLES = '''
- name: Get the cert from an RDP port
  get_certificate:
    host: "1.2.3.4"
    port: 3389
  delegate_to: localhost
  run_once: true
  register: cert

- name: Get a cert from an https port
  get_certificate:
    host: "www.google.com"
    port: 443
  delegate_to: localhost
  run_once: true
  register: cert

- name: How many days until cert expires
  debug:
    msg: "cert expires in: {{ expire_days }} days."
  vars:
    expire_days: "{{ (( cert.not_after | to_datetime('%Y%m%d%H%M%SZ')) - (ansible_date_time.iso8601 | to_datetime('%Y-%m-%dT%H:%M:%SZ')) ).days }}"
'''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_bytes
from ansible.module_utils import crypto as crypto_utils

from distutils.version import LooseVersion
from os.path import isfile
from socket import setdefaulttimeout, socket
from ssl import get_server_certificate, DER_cert_to_PEM_cert, CERT_NONE, CERT_OPTIONAL

import atexit
import base64
import datetime
import traceback

MINIMAL_PYOPENSSL_VERSION = '0.15'
MINIMAL_CRYPTOGRAPHY_VERSION = '1.6'

CREATE_DEFAULT_CONTEXT_IMP_ERR = None
try:
    from ssl import create_default_context
except ImportError:
    CREATE_DEFAULT_CONTEXT_IMP_ERR = traceback.format_exc()
    HAS_CREATE_DEFAULT_CONTEXT = False
else:
    HAS_CREATE_DEFAULT_CONTEXT = True

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
    import cryptography.x509
    from cryptography.hazmat.backends import default_backend as cryptography_backend
    CRYPTOGRAPHY_VERSION = LooseVersion(cryptography.__version__)
except ImportError:
    CRYPTOGRAPHY_IMP_ERR = traceback.format_exc()
    CRYPTOGRAPHY_FOUND = False
else:
    CRYPTOGRAPHY_FOUND = True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ca_cert=dict(type='path'),
            host=dict(type='str', required=True),
            port=dict(type='int', required=True),
            proxy_host=dict(type='str'),
            proxy_port=dict(type='int', default=8080),
            timeout=dict(type='int', default=10),
            select_crypto_backend=dict(type='str', choices=['auto', 'pyopenssl', 'cryptography'], default='auto'),
        ),
    )

    ca_cert = module.params.get('ca_cert')
    host = module.params.get('host')
    port = module.params.get('port')
    proxy_host = module.params.get('proxy_host')
    proxy_port = module.params.get('proxy_port')
    timeout = module.params.get('timeout')

    backend = module.params.get('select_crypto_backend')
    if backend == 'auto':
        # Detection what is possible
        can_use_cryptography = CRYPTOGRAPHY_FOUND and CRYPTOGRAPHY_VERSION >= LooseVersion(MINIMAL_CRYPTOGRAPHY_VERSION)
        can_use_pyopenssl = PYOPENSSL_FOUND and PYOPENSSL_VERSION >= LooseVersion(MINIMAL_PYOPENSSL_VERSION)

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

    if backend == 'pyopenssl':
        if not PYOPENSSL_FOUND:
            module.fail_json(msg=missing_required_lib('pyOpenSSL >= {0}'.format(MINIMAL_PYOPENSSL_VERSION)),
                             exception=PYOPENSSL_IMP_ERR)
        module.deprecate('The module is using the PyOpenSSL backend. This backend has been deprecated', version='2.13')
    elif backend == 'cryptography':
        if not CRYPTOGRAPHY_FOUND:
            module.fail_json(msg=missing_required_lib('cryptography >= {0}'.format(MINIMAL_CRYPTOGRAPHY_VERSION)),
                             exception=CRYPTOGRAPHY_IMP_ERR)

    result = dict(
        changed=False,
    )

    if timeout:
        setdefaulttimeout(timeout)

    if ca_cert:
        if not isfile(ca_cert):
            module.fail_json(msg="ca_cert file does not exist")

    if proxy_host:
        if not HAS_CREATE_DEFAULT_CONTEXT:
            module.fail_json(msg='To use proxy_host, you must run the get_certificate module with Python 2.7 or newer.',
                             exception=CREATE_DEFAULT_CONTEXT_IMP_ERR)

        try:
            connect = "CONNECT %s:%s HTTP/1.0\r\n\r\n" % (host, port)
            sock = socket()
            atexit.register(sock.close)
            sock.connect((proxy_host, proxy_port))
            sock.send(connect.encode())
            sock.recv(8192)

            ctx = create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = CERT_NONE

            if ca_cert:
                ctx.verify_mode = CERT_OPTIONAL
                ctx.load_verify_locations(cafile=ca_cert)

            cert = ctx.wrap_socket(sock, server_hostname=host).getpeercert(True)
            cert = DER_cert_to_PEM_cert(cert)
        except Exception as e:
            module.fail_json(msg="Failed to get cert from port with error: {0}".format(e))

    else:
        try:
            cert = get_server_certificate((host, port), ca_certs=ca_cert)
        except Exception as e:
            module.fail_json(msg="Failed to get cert from port with error: {0}".format(e))

    result['cert'] = cert

    if backend == 'pyopenssl':
        x509 = crypto.load_certificate(crypto.FILETYPE_PEM, cert)
        result['subject'] = {}
        for component in x509.get_subject().get_components():
            result['subject'][component[0]] = component[1]

        result['expired'] = x509.has_expired()

        result['extensions'] = []
        extension_count = x509.get_extension_count()
        for index in range(0, extension_count):
            extension = x509.get_extension(index)
            result['extensions'].append({
                'critical': extension.get_critical(),
                'asn1_data': extension.get_data(),
                'name': extension.get_short_name(),
            })

        result['issuer'] = {}
        for component in x509.get_issuer().get_components():
            result['issuer'][component[0]] = component[1]

        result['not_after'] = x509.get_notAfter()
        result['not_before'] = x509.get_notBefore()

        result['serial_number'] = x509.get_serial_number()
        result['signature_algorithm'] = x509.get_signature_algorithm()

        result['version'] = x509.get_version()

    elif backend == 'cryptography':
        x509 = cryptography.x509.load_pem_x509_certificate(to_bytes(cert), cryptography_backend())
        result['subject'] = {}
        for attribute in x509.subject:
            result['subject'][crypto_utils.cryptography_oid_to_name(attribute.oid, short=True)] = attribute.value

        result['expired'] = x509.not_valid_after < datetime.datetime.utcnow()

        result['extensions'] = []
        for dotted_number, entry in crypto_utils.cryptography_get_extensions_from_cert(x509).items():
            oid = cryptography.x509.oid.ObjectIdentifier(dotted_number)
            result['extensions'].append({
                'critical': entry['critical'],
                'asn1_data': base64.b64decode(entry['value']),
                'name': crypto_utils.cryptography_oid_to_name(oid, short=True),
            })

        result['issuer'] = {}
        for attribute in x509.issuer:
            result['issuer'][crypto_utils.cryptography_oid_to_name(attribute.oid, short=True)] = attribute.value

        result['not_after'] = x509.not_valid_after.strftime('%Y%m%d%H%M%SZ')
        result['not_before'] = x509.not_valid_before.strftime('%Y%m%d%H%M%SZ')

        result['serial_number'] = x509.serial_number
        result['signature_algorithm'] = crypto_utils.cryptography_oid_to_name(x509.signature_algorithm_oid)

        # We need the -1 offset to get the same values as pyOpenSSL
        if x509.version == cryptography.x509.Version.v1:
            result['version'] = 1 - 1
        elif x509.version == cryptography.x509.Version.v3:
            result['version'] = 3 - 1
        else:
            result['version'] = "unknown"

    module.exit_json(**result)


if __name__ == '__main__':
    main()
