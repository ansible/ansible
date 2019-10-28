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
module: win_cert_stat
version_added: "2.10"
short_description: Get information from the Windows Certificate Store
description:
- Returns information about a certificate in the Windows Certificate Store.
options:
  thumbprint:
    description:
    - The thumbprint as a hex string of the certificate to find.
    - See M(win_certificate_store) for how to format the thumbprint.
    type: str
    required: yes
  store_name:
    description:
    - The store name to use when searching for a certificate.
    type: str
    default: My
  store_location:
    description:
    - The store location to use when searching for a certificate.
    type: str
    choices: [ CurrentUser, LocalMachine ]
    default: LocalMachine
seealso:
- module: win_stat
- module: win_reg_stat
- module: win_certificate_store
author:
- Micah Hunsberger (@mhunsber)
'''

EXAMPLES = r'''
- name: Obtain information about a certificate in the computer's personal store
  win_cert_stat:
    thumbprint: BD7AF104CF1872BDB518D95C9534EA941665FD27
  register: mycert

- name: Obtain information about a certificate in the root store
  win_cert_stat:
    store_name: Root
    thumbprint: A43489159A520F0D93D032CCAF37E7FE20A8B419
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
  win_cert_stat:
    thumbprint: "{{ item }}"
  register: mycert_stats
  loop: "{{ mycert.thumbprints }}"
'''

RETURN = r'''
archived:
  description: if the cert is archived or not
  returned: cert exists
  type: bool
  sample: false
dns_names:
  description: A list of dns names the certificate is registered for
  returned: cert exists
  type: list
  sample: [ '*.m.wikiquote.org', '*.wikipedia.org' ]
exists:
  description: If the cert exists or not.
  returned: success
  type: bool
  sample: true
extensions:
  description: The collection of the certificates extensions
  returned: cert exists
  type: list
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
  returned: cert exists
  type: str
  sample: Microsoft Root Authority
has_private_key:
  description: if the certificate has an associated private key
  returned: cert exists
  type: bool
  sample: false
intended_purposes:
  description: The applications that use the certificate.
  returned: cert exists, extensions contains an enhanced key usages extension.
  type: list
  sample: [ "Server Authentication" ]
is_ca:
  description: if the certificate is a certificate authority (CA) certificate.
  returned: cert exists, extensions contains basic constraints extension
  type: bool
  sample: true
issued_by:
  description: the common name of the issuer
  returned: cert exists
  type: str
  sample: Apple Root CA
issued_to:
  description: the common name of the certificate subject
  returned: cert exists
  type: str
  sample: Apple Worldwide Developer Relations Certification Authority
issuer:
  description: The distinguished name of the issuer of the certificate.
  returned: cert exists
  type: str
  sample: 'CN=Apple Root CA, OU=Apple Certification Authority, O=Apple Inc., C=US'
key_usages:
  description:
    - Defines how the certificate key can be used.
    - If this value is not defined, the key can be used for any purpose.
  returned: cert exists, extensions contains key usages extension.
  type: list
  sample: [ "CrlSign", "KeyCertSign", "DigitalSignature" ]
path_length_constraint:
  description:
    - The number of levels allowed in a certificates path.
    - If this value is 0, the certificate does not have a restriction.
  returned: cert exists, extensions contains basic constraints extension
  type: int
  sample: 0
public_key:
  description: The base64 encoded public key of the certificate.
  returned: cert exists
  type: str
cert_data:
  description: The base64 encoded data of the entire certificate.
  returned: cert exists
  type: str
serial_number:
  description: The serial number of the certificate represented as a hexadecimal string
  returned: cert exists
  type: str
  sample: 01DEBCC4396DA010
signature_algorithm:
  description: The algorithm used to create the certificate's signature
  returned: cert exists
  type: str
  sample: sha1RSA
ski:
  description: The certificate's subject key identifier
  returned: cert exists, extensions contains a subject key identifier extension
  type: str
  sample: 88271709A9B618608BECEBBAF64759C55254A3B7
subject:
  description: The subject or distinguished name of the certificate.
  returned: cert exists
  type: str
  sample: 'CN=Apple Worldwide Developer Relations Certification Authority, OU=Apple Worldwide Developer Relations, O=Apple Inc., C=US'
thumbprint:
  description: The thumbprint as a hex string of the certificate.
  returned: cert exists
  type: str
  sample: FF6797793A3CD798DC5B2ABEF56F73EDC9F83A64
valid_from:
  description: The start date of the certificate represented in seconds since epoch.
  returned: cert exists
  type: float
  sample: 1360255727
valid_to:
  description: The expiry date of the certificate represented in seconds since epoch.
  returned: cert exists
  type: float
  sample: 1675788527
version:
  description: The x509 format version of the certificate
  returned: cert exists
  type: int
  sample: 3
'''
