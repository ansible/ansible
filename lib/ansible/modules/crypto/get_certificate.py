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
options:
    host:
      description:
        - The host to get the cert for (IP is fine)
      required: True
    ca_certs:
      description:
        - A PEM file containing a list of root certificates; if present, the cert will be validated against these root certs.
        - Note that this only validates the certificate is signed by the chain; not that the cert is valid for the host presenting it.
      required: False
    port:
      description:
        - The port to connect to
      required: True
    timeout:
      description:
        - The timeout in seconds
      required: False
      default: 10

notes:
  - When using ca_certs on OS X it has been reported that in some conditions the validate will always succeed.

requirements:
  - "python >= 2.6"
  - "python-pyOpenSSL >= 0.15"
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
'''

from ansible.module_utils.basic import AnsibleModule

from os.path import isfile
from ssl import get_server_certificate
from socket import setdefaulttimeout

try:
    from OpenSSL import crypto
except ImportError:
    pyopenssl_found = False
else:
    pyopenssl_found = True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ca_certs=dict(required=False, type='path', default=None),
            host=dict(required=True),
            port=dict(required=True, type='int'),
            timeout=dict(required=False, type='int', default=10),
        ),
    )

    ca_certs = module.params.get('ca_certs')
    host = module.params.get('host')
    port = module.params.get('port')
    timeout = module.params.get('timeout')

    result = dict(
        changed=False,
    )

    if not pyopenssl_found:
        module.fail_json(msg='the python pyOpenSSL module is required')

    if timeout:
        setdefaulttimeout(timeout)

    if ca_certs:
        if not isfile(ca_certs):
            module.fail_json(msg="ca_certs file does not exist")

    try:
        cert = get_server_certificate((host, port), ca_certs=ca_certs)
        x509 = crypto.load_certificate(crypto.FILETYPE_PEM, cert)
    except Exception as e:
        module.fail_json(msg="Failed to get cert from port with error: {0}".format(e))

    result['cert'] = cert
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

    module.exit_json(**result)


if __name__ == '__main__':
    main()
