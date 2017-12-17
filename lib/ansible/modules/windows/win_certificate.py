#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Andre Bindewald(@tiwood)
#
# This file is part of Ansible
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


DOCUMENTATION = r'''
---
module: win_certificate
version_added: "2.4"
short_description: Manages certificates on a Windows machine
description:
  - The M(win_certificate) module can be used to import or remove certificates from the internal LocalMachine certificate store.
    The certificate needs to be copied to the node before you try to import/delte the certificate object, as the module needs to extract
    certificate facts from the cert file
    The following filetypes are supported *.pfx, *.p12, *.cer, *.crt, *.p7b, *.spc
    If you want to import a certificate with private key included (PFX), you have to provide the certificate password.
options:
  state:
    version_added: "2.4"
    description:
      - Specifies the desired state of the provided certificate.
    required: true
    choices:
      - present
      - absent
  path:
    version_added: "2.4"
    description:
      - The host local path to the certificate file.
        Usage "C:\Install\MyCert.pfx"
    required: true
  store:
    version_added: "2.4"
    description:
      - Specifies the path of the store to which certificates will be imported/deleted.
    required: true
    choices:
      - My
      - TrustedPublisher
      - Root
      - CA
  password:
    version_added: "2.4"
    description:
      - Specifies the password for the imported certificate file.
    required: false
  privatekey_exportable:
    version_added: "2.4"
    description:
      - Specifies whether the imported private key can be exported. If this parameter is not specified, then the private key cannot be exported.
    required: false
    default: false
    choices:
      - true
      - false
  force:
    version_added: "2.4"
    description:
      - Defines if the certificate should be overwritten.
    required: false
    default: false
    choices:
      - true
      - false
author: "Andre Bindewald (@tiwood)"
'''

EXAMPLES = r'''
- name: Import a certificate with embedded private key to the personal local machine store.
  win_certificate:
      state: present
      path: C:\foo\Certificate.pfx
      store: My
      password: mypasswd
- name: Import a certificate with embedded private key to the personal local machine store. (Private key exportable)
  win_certificate:
      state: present
      path: C:\foo\Certificate.pfx
      store: TrustedPublisher
      password: mypasswd
      privatekey_exportable: true
- name: Import a trusted Root CA certificate.
  win_certificate:
      state: present
      path: C:\foo\TrustedRootCertificate.cer
      store: TrustedPublisher
- name: Ensure a specific certificate is absent on the personal machine store.
  win_certificate:
      state: absent
      path: C:\foo\Certificate.pfx
      store: My
      password: mypasswd
'''

RETURN = r'''
state:
    description: whether the certificate should be present or absent
    returned: always
    type: string
    sample: present
thumbprint:
    description: thumbprint of the certificate
    returned: success
    type: string
    sample: 058C31261C8C5FD55831E0EC9E2E1041E4A03238
subject:
    description: the certificate subject
    returned: success
    type: string
    sample: "*.myansible-demo.int"
hasPrivateKey:
    description: whether the certificate has a private key embedded
    returned: success
    type: bool
    sample: true
store:
    description: the store where the certificate is located
    returned: success
    type: string
    sample: My
notValidBefore:
    description: unix timestamp of the ValidBefore certificate property
    returned: success
    type: string
    sample: 1639440000
notValidAfter:
    description: tunix timestamp of the ValidBefore certificate property
    returned: success
    type: string
    sample: 1639440000
'''
