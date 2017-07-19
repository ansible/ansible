#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
module: openssl_pkcs12
author: "Guillaume Delpierre (@gdelpierre)"
version_added: "2.4"
short_description: Generate OpenSSL pkcs12 archive.
description:
    - "This module allows one to (re-)generate PKCS #12."
requirements:
    - "python-pyOpenSSL"
options:
    ca_certificates:
        required: False
        description:
            - List of CA certificate to include.
    certificate:
        required: False
        description:
            - The path to read certificates and private keys from.
              Must be in PEM format.
    action:
        required: False
        default: 'export'
        choices: [ 'parse', 'export' ]
        description:
            - Create (export) or parse a PKCS #12.
    dest:
        required: True
        default: null
        aliases: ['path', 'destfile']
        description:
            - Filename to write the PKCS#12 file to.
    force:
        required: False
        default: False
        choices: [ True, False ]
        description:
            - Should the PKCS #12 be regenerated even if it already exists.
    friendly_name:
        required: True
        default: null
        aliases: 'name'
        description:
            - Specifies the "friendly name" for the certificate and private key.
    iter_size:
        required: False
        default: 2048
        description:
            - Number of times to repeat the encryption step.
    maciter_size:
        required: False
        default: 1
        description:
            - Number of times to repeat the MAC step.
    mode:
        required: False
        default: 0400
        description:
            - Default mode for the generated PKCS #12 file.
    passphrase:
        required: False
        default: null
        description:
            - The PKCS#12 password.
    privatekey:
        required: True
        description:
            - File to read private key from.
    privatekey_passphrase:
        required: False
        default: null
        description:
            - Passphrase source to decrypt any input private keys with.
    state:
        required: False
        default: 'present'
        choices: [ 'present', 'absent' ]
        description:
            - Whether the file should exist or not.
'''

EXAMPLES = '''
- name: 'Generate temporary PKCS12 keystore'
  openssl_pkcs12:
    path: '/tmp/ansible.p12'
    friendly_name: 'raclette'
    privatekey_path: '/tmp/jambon.pem'
    cert_path: '/tmp/fromage.pem'
    ca_certificates: '/tmp/patates.cer'
    state: present

- name: 'generate kafka keystore'
  java_cert:
    state: present
    src_keystore_path: '/tmp/ansible.p12'
    keystore_path: '/tmp/ansible.jks'
    src_store_type: 'pkcs12'
    src_store_pass: ''
    keystore_pass: 'totototo'
    alias: 'raclette'

- name: 'Generate truststore'
  java_cert:
    state: present
    keystore_create: True
    keystore_path: '/tmp/truststore.jks'
    keystore_pass: 'totototo'
    cert_path: '/tmp/cert.pem'
    cert_alias: 'raymond'
'''

RETURN = '''
'''

import os

try:
    from OpenSSL import crypto
except ImportError:
    pyopenssl_found = False
else:
    pyopenssl_found = True

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.crypto import OpenSSLModule, OpenSSLModuleError, load_certificate, load_privatekey
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils._text import to_native

class PkcsError(OpenSSLModuleError):
    pass

class Pkcs(OpenSSLModule):

    def __init__(self, module):
        super(Pkcs, self).__init__(module)
        self.action = module.params['action']
        self.iter_size = module.params['iter_size']
        self.maciter_size = module.params['maciter_size']
        self.privatekey_path = module.params['privatekey_path']
        self.privatekey_passphrase = module.params['privatekey_passphrase']
        self.cert_path = module.params['cert_path']
        self.ca_certificates = module.params['ca_certificates']
        self.friendly_name = module.params['friendly_name']
        self.passphrase = module.params['passphrase']
        self.mode = module.params['mode']

    def export(self):
        ''' Generate PKCS #12 file. '''

        if os.path.exists(self.path) and not self.force:
            self.changed = False
            return

        self.pkcs12 = crypto.PKCS12()

        if self.ca_certificates:
            ca_certs = tuple([load_certificate(ca_cert) for ca_cert in self.ca_certificates])
            self.pkcs12.set_ca_certificates(ca_certs)

        if self.cert_path:
            self.pkcs12.set_certificate(load_certificate(self.cert_path))

        if self.friendly_name:
            self.pkcs12.set_friendlyname(self.friendly_name)

        if self.privatekey_path:
            self.pkcs12.set_privatekey(load_privatekey(
                                        self.privatekey_path,
                                        self.privatekey_passphrase)
                                        )

        try:
            with open(self.path, 'w', self.mode) as archive:
                archive.write(
                    self.pkcs12.export(
                        self.passphrase,
                        self.iter_size,
                        self.maciter_size
                    )
                )
        except (IOError, OSError) as exc:
            raise PkcsError(exc)
            
    def parse(self):
        ''' Parse PKCS #12 file. '''
        pass

    def check(self):
        return True

    def dump(self):
        result = {
            'changed': self.changed,
            'path': self.path,
        }
        return result


def main():
    module = AnsibleModule(
        argument_spec = dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            path=dict(required=True, type='path'),
            force=dict(default=False, type='bool'),
            action=dict(default='export', choices=['parse', 'export'], type='str'),
            ca_certificates=dict(type='list'),
            cert_path=dict(type='path'),
            friendly_name=dict(required=True, type='str'),
            iter_size=dict(default=2048, type='int'),
            maciter_size=dict(default=1, type='int'),
            mode=dict(default=0400, type='int'),
            passphrase=dict(type='str', no_log=True),
            privatekey_path=dict(required=True, type='path'),
            privatekey_passphrase=dict(type='str', no_log=True),
        ),
        required_together = [
            ['path', 'privatekey_path', 'friendly_name'],
        ],
        supports_check_mode = True,
        add_file_common_args = True,
    )

    if not pyopenssl_found:
        module.fail_json(msg='The python pyOpenSSL library is required')

    pkcs12 = Pkcs(module)

    if module.params['state'] == 'present':
        if module.check_mode:
            result = pkcs12.dump()
            result['changed'] = module.params['force'] or not pkcs12.check()
            module.exit_json(**result)

        try:
            pkcs12.export()
        except PkcsError as exc:
            module.fail_json(msg=to_native(exc))
    else:
        if module.check_mode:
            result = pkcs12.dump()
            result['changed'] = pkcs12.check()
            module.exit_json(**result)

        try:
            pkcs12.remove()
        except PkcsError as exc:
            module.fail_json(msg=to_native(exc))

    result = pkcs12.dump()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
