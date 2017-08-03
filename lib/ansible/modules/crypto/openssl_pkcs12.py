#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: openssl_pkcs12
author: "Guillaume Delpierre (@gdelpierre)"
version_added: "2.4"
short_description: Generate OpenSSL PKCS#12 archive.
description:
    - "This module allows one to (re-)generate PKCS#12."
requirements:
    - "python-pyOpenSSL"
options:
    action:
        required: False
        default: None
        choices: ['parse', 'export', None]
        description:
            - Create (export) or parse a PKCS#12.
              None is used with absent state.
    ca_certificates:
        required: False
        description:
            - List of CA certificate to include.
    cert_path:
        required: False
        description:
            - The path to read certificates and private keys from.
              Must be in PEM format.
    force:
        required: False
        default: False
        description:
            - Should the file be regenerated even it it already exists.
    friendly_name:
        required: False
        default: null
        aliases: 'name'
        description:
            - Specifies the friendly name for the certificate and private key.
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
            - Default mode for the generated PKCS#12 file.
    passphrase:
        required: False
        default: null
        description:
            - The PKCS#12 password.
    path:
        required: True
        default: null
        description:
            - Filename to write the PKCS#12 file to.
    privatekey_passphrase:
        required: False
        default: null
        description:
            - Passphrase source to decrypt any input private keys with.
    privatekey_path:
        required: False
        description:
            - File to read private key from.
    state:
        required: False
        default: 'present'
        choices: ['present', 'absent']
        description:
            - Whether the file should exist or not.
    src:
        required: False
        description:
            - PKCS#12 file path to parse.
'''

EXAMPLES = '''
- name: 'Generate PKCS#12 file'
  openssl_pkcs12:
    action: export
    path: '/opt/certs/ansible.p12'
    friendly_name: 'raclette'
    privatekey_path: '/opt/certs/keys/key.pem'
    cert_path: '/opt/certs/cert.pem'
    ca_certificates: '/opt/certs/ca.pem'
    state: present

- name: 'Change PKCS#12 file permission'
  openssl_pkcs12:
    action: export
    path: '/opt/certs/ansible.p12'
    friendly_name: 'raclette'
    privatekey_path: '/opt/certs/keys/key.pem'
    cert_path: '/opt/certs/cert.pem'
    ca_certificates: '/opt/certs/ca.pem'
    state: present
    mode: 0600

- name: 'Regen PKCS#12 file'
  openssl_pkcs12:
    action: export
    src: '/opt/certs/ansible.p12'
    path: '/opt/certs/ansible.p12'
    friendly_name: 'raclette'
    privatekey_path: '/opt/certs/keys/key.pem'
    cert_path: '/opt/certs/cert.pem'
    ca_certificates: '/opt/certs/ca.pem'
    state: present
    mode: 0600
    force: True

- name: 'Dump/Parse PKCS#12 file'
  openssl_pkcs12:
    action: parse
    src: '/opt/certs/ansible.p12'
    path: '/opt/certs/ansible.pem'
    state: present

- name: 'Remove PKCS#12 file'
  openssl_pkcs12:
    path: '/opt/certs/ansible.p12'
    state: absent
'''

RETURN = '''
filename:
    description: Path to the generate PKCS#12 file.
    returned: changed or success
    type: string
    sample: /opt/certs/ansible.p12
privatekey:
    description: Path to the TLS/SSL private key the public key was generated from
    returned: changed or success
    type: string
    sample: /etc/ssl/private/ansible.com.pem
'''

import os

try:
    from OpenSSL import crypto
except ImportError:
    pyopenssl_found = False
else:
    pyopenssl_found = True

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import crypto as crypto_utils
from ansible.module_utils._text import to_native


class PkcsError(crypto_utils.OpenSSLObjectError):
    pass


class Pkcs(crypto_utils.OpenSSLObject):

    def __init__(self, module):
        super(Pkcs, self).__init__(
            module.params['path'],
            module.params['force'],
            module.params['state'],
            module.check_mode
        )
        self.action = module.params['action']
        self.ca_certificates = module.params['ca_certificates']
        self.cert_path = module.params['cert_path']
        self.friendly_name = module.params['friendly_name']
        self.iter_size = module.params['iter_size']
        self.maciter_size = module.params['maciter_size']
        self.passphrase = module.params['passphrase']
        self.pkcs12 = None
        self.privatekey_passphrase = module.params['privatekey_passphrase']
        self.privatekey_path = module.params['privatekey_path']
        self.src = module.params['src']
        self.mode = module.params['mode']
        if not self.mode:
            self.mode = int('0400', 8)

    def check(self, module, perms_required=True):
        ''' Ensure the resource is in its desired state. '''

        state_and_perms = super(Pkcs, self).check(module, perms_required)

        def _check_pkey_passphrase():
            if self.privatekey_passphrase:
                try:
                    crypto_utils.load_privatekey(self.path,
                                                 self.privatekey_passphrase)
                    return True
                except crypto.Error:
                    return False
            return True

        if not state_and_perms:
            return state_and_perms

        return _check_pkey_passphrase

    def dump(self):
        ''' Serialize the object into a dictionary. '''

        result = {
            'changed': self.changed,
            'filename': self.path,
        }
        if self.privatekey_path:
            result['privatekey_path'] = self.privatekey_path

        return result

    def generate(self, module):
        ''' Generate PKCS#12 file archive. '''

        if not self.check(module, perms_required=False) or module.params['force']:
            self.pkcs12 = crypto.PKCS12()

            try:
                self.remove()
            except PkcsError as exc:
                module.fail_json(msg=to_native(exc))

            if self.ca_certificates:
                ca_certs = [crypto_utils.load_certificate(ca_cert) for ca_cert
                            in self.ca_certificates]
                self.pkcs12.set_ca_certificates(ca_certs)

            if self.cert_path:
                self.pkcs12.set_certificate(crypto_utils.load_certificate(
                                            self.cert_path))

            if self.friendly_name:
                self.pkcs12.set_friendlyname(self.friendly_name)

            if self.privatekey_path:
                self.pkcs12.set_privatekey(crypto_utils.load_privatekey(
                                           self.privatekey_path,
                                           self.privatekey_passphrase)
                                           )

            try:
                with open(self.path, 'wb') as archive:
                    archive.write(
                        self.pkcs12.export(
                            self.passphrase,
                            self.iter_size,
                            self.maciter_size
                        )
                    )
                module.set_mode_if_different(self.path, self.mode, False)
                self.changed = True
            except (IOError, OSError) as exc:
                self.remove()
                raise PkcsError(exc)

        file_args = module.load_file_common_arguments(module.params)
        if module.set_fs_attributes_if_different(file_args, False):
            module.set_mode_if_different(self.path, self.mode, False)
            self.changed = True

    def parse(self, module):
        ''' Read PKCS#12 file. '''

        if not self.check(module, perms_required=False) or module.params['force']:
            try:
                self.remove()

                p12 = crypto.load_pkcs12(open(self.src, 'rb').read(),
                                         passphrase=self.passphrase)
                pkey = crypto.dump_privatekey(crypto.FILETYPE_PEM,
                                              p12.get_privatekey())
                crt = crypto.dump_certificate(crypto.FILETYPE_PEM,
                                              p12.get_certificate())

                with open(self.path, 'wb') as content:
                    content.write("%s%s" % (pkey, crt))
                module.set_mode_if_different(self.path, self.mode, False)
                self.changed = True
            except IOError as exc:
                self.remove()
                raise PkcsError(exc)

        file_args = module.load_file_common_arguments(module.params)
        if module.set_fs_attributes_if_different(file_args, False):
            module.set_mode_if_different(self.path, self.mode, False)
            self.changed = True


def main():
    argument_spec = dict(
        action=dict(default=None,
                    choices=['parse', 'export'],
                    type='str'),
        ca_certificates=dict(type='list'),
        cert_path=dict(type='path'),
        force=dict(default=False, type='bool'),
        friendly_name=dict(type='str', aliases=['name']),
        iter_size=dict(default=2048, type='int'),
        maciter_size=dict(default=1, type='int'),
        passphrase=dict(type='str', no_log=True),
        path=dict(required=True, type='path'),
        privatekey_passphrase=dict(type='str', no_log=True),
        privatekey_path=dict(type='path'),
        state=dict(default='present',
                   choices=['present', 'absent'],
                   type='str'),
        src=dict(type='path'),
    )

    required_if = [
        ['action', 'export', ['friendly_name']],
        ['action', 'parse', ['src']],
    ]

    required_together = [
        ['privatekey_path', 'friendly_name'],
    ]

    module = AnsibleModule(
        add_file_common_args=True,
        argument_spec=argument_spec,
        required_if=required_if,
        required_together=required_together,
        supports_check_mode=True,
    )

    if not pyopenssl_found:
        module.fail_json(msg='The python pyOpenSSL library is required')

    base_dir = os.path.dirname(module.params['path'])
    if not os.path.isdir(base_dir):
        module.fail_json(
            name=base_dir,
            msg='The directory %s does not exist or '
                'the file is not a directory' % base_dir
        )

    pkcs12 = Pkcs(module)

    if module.params['state'] == 'present':
        if module.check_mode:
            result = pkcs12.dump()
            result['changed'] = module.params['force'] or not pkcs12.check(module)
            module.exit_json(**result)

        try:
            if module.params['action'] == 'export':
                pkcs12.generate(module)
            else:
                pkcs12.parse(module)
        except PkcsError as exc:
            module.fail_json(msg=to_native(exc))
    else:
        if module.check_mode:
            result = pkcs12.dump()
            result['changed'] = os.path.exists(module.params['path'])
            module.exit_json(**result)

        try:
            pkcs12.remove()
        except PkcsError as exc:
            module.fail_json(msg=to_native(exc))

    result = pkcs12.dump()

    module.exit_json(**result)

if __name__ == '__main__':
    main()
