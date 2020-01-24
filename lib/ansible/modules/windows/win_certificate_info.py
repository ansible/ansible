#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Ansible, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_certificate_info
version_added: "2.10"
short_description: Get information on certificates from a Windows Certificate Store
description:
- Returns information about certificates in a Windows Certificate Store.
options:
  thumbprint:
    description:
    - The thumbprint as a hex string of a certificate to find.
    - When specified, filters the I(certificates) return value to a single certificate
    - See the examples for how to format the thumbprint.
    type: str
    required: no
  store_name:
    description:
    - The name of the store to search.
    - See U(https://docs.microsoft.com/en-us/dotnet/api/system.security.cryptography.x509certificates.storename)
      for a list of built-in store names.
    type: str
    default: My
  store_location:
    description:
    - The location of the store to search.
    type: str
    choices: [ CurrentUser, LocalMachine ]
    default: LocalMachine
seealso:
- module: win_certificate_store
author:
- Micah Hunsberger (@mhunsber)
'''

EXAMPLES = r'''
- name: Obtain information about a particular certificate in the computer's personal store
  win_certificate_info:
    thumbprint: BD7AF104CF1872BDB518D95C9534EA941665FD27
  register: mycert

# thumbprint can also be lower case
- name: Obtain information about a particular certificate in the computer's personal store
  win_certificate_info:
    thumbprint: bd7af104cf1872bdb518d95c9534ea941665fd27
  register: mycert

- name: Obtain information about all certificates in the root store
  win_certificate_info:
    store_name: Root
  register: ca

# Import a pfx and then get information on the certificates
- name: Import pfx certificate that is password protected
  win_certificate_store:
    path: C:\Temp\cert.pfx
    state: present
    password: VeryStrongPasswordHere!
  become: yes
  become_method: runas
  register: mycert

- name: Obtain information on each certificate that was touched
  win_certificate_info:
    thumbprint: "{{ item }}"
  register: mycert_stats
  loop: "{{ mycert.thumbprints }}"
'''

RETURN = r'''
exists:
  description:
    - Whether any certificates were found in the store.
    - When I(thumbprint) is specified, returns true only if the certificate mathing the thumbprint exists.
  returned: success
  type: bool
  sample: true
certificates:
  description:
    - A list of information about certificates found in the store, sorted by thumbprint.
  returned: success
  type: list
  elements: dict
  contains:
    archived:
      description: Indicates that the certificate is archived.
      type: bool
      sample: false
    dns_names:
      description: Lists the registered dns names for the certificate.
      type: list
      elements: str
      sample: [ '*.m.wikiquote.org', '*.wikipedia.org' ]
    extensions:
      description: The collection of the certificates extensions.
      type: list
      elements: dict
      sample: [
            {
                "critical": false,
                "field": "Subject Key Identifier",
                "value": "88 27 17 09 a9 b6 18 60 8b ec eb ba f6 47 59 c5 52 54 a3 b7"
            },
            {
                "critical": true,
                "field": "Basic Constraints",
                "value": "Subject Type=CA, Path Length Constraint=None"
            },
            {
                "critical": false,
                "field": "Authority Key Identifier",
                "value": "KeyID=2b d0 69 47 94 76 09 fe f4 6b 8d 2e 40 a6 f7 47 4d 7f 08 5e"
            },
            {
                "critical": false,
                "field": "CRL Distribution Points",
                "value": "[1]CRL Distribution Point: Distribution Point Name:Full Name:URL=http://crl.apple.com/root.crl"
            },
            {
                "critical": true,
                "field": "Key Usage",
                "value": "Digital Signature, Certificate Signing, Off-line CRL Signing, CRL Signing (86)"
            },
            {
                "critical": false,
                "field": null,
                "value": "05 00"
            }
        ]
    friendly_name:
      description: The associated alias for the certificate.
      type: str
      sample: Microsoft Root Authority
    has_private_key:
      description: Indicates that the certificate contains a private key.
      type: bool
      sample: false
    intended_purposes:
      description: lists the intended applications for the certificate.
      returned: enhanced key usages extension exists.
      type: list
      sample: [ "Server Authentication" ]
    is_ca:
      description: Indicates that the certificate is a certificate authority (CA) certificate.
      returned: basic constraints extension exists.
      type: bool
      sample: true
    issued_by:
      description: The certificate issuer's common name.
      type: str
      sample: Apple Root CA
    issued_to:
      description: The certificate's common name.
      type: str
      sample: Apple Worldwide Developer Relations Certification Authority
    issuer:
      description: The certificate issuer's distinguished name.
      type: str
      sample: 'CN=Apple Root CA, OU=Apple Certification Authority, O=Apple Inc., C=US'
    key_usages:
      description:
        - Defines how the certificate key can be used.
        - If this value is not defined, the key can be used for any purpose.
      returned: key usages extension exists.
      type: list
      elements: str
      sample: [ "CrlSign", "KeyCertSign", "DigitalSignature" ]
    path_length_constraint:
      description:
        - The number of levels allowed in a certificates path.
        - If this value is 0, the certificate does not have a restriction.
      returned: basic constraints extension exists
      type: int
      sample: 0
    public_key:
      description: The base64 encoded public key of the certificate.
      type: str
    cert_data:
      description: The base64 encoded data of the entire certificate.
      type: str
    serial_number:
      description: The serial number of the certificate represented as a hexadecimal string
      type: str
      sample: 01DEBCC4396DA010
    signature_algorithm:
      description: The algorithm used to create the certificate's signature
      type: str
      sample: sha1RSA
    ski:
      description: The certificate's subject key identifier
      returned: subject key identifier extension exists.
      type: str
      sample: 88271709A9B618608BECEBBAF64759C55254A3B7
    subject:
      description: The certificate's distinguished name.
      type: str
      sample: 'CN=Apple Worldwide Developer Relations Certification Authority, OU=Apple Worldwide Developer Relations, O=Apple Inc., C=US'
    thumbprint:
      description:
        - The thumbprint as a hex string of the certificate.
        - The return format will always be upper case.
      type: str
      sample: FF6797793A3CD798DC5B2ABEF56F73EDC9F83A64
    valid_from:
      description: The start date of the certificate represented in seconds since epoch.
      type: float
      sample: 1360255727
    valid_from_iso8601:
      description: The start date of the certificate represented as an iso8601 formatted date.
      type: str
      sample: '2017-12-15T08:39:32Z'
    valid_to:
      description: The expiry date of the certificate represented in seconds since epoch.
      type: float
      sample: 1675788527
    valid_to_iso8601:
      description: The expiry date of the certificate represented as an iso8601 formatted date.
      type: str
      sample: '2086-01-02T08:39:32Z'
    version:
      description: The x509 format version of the certificate
      type: int
      sample: 3
'''
