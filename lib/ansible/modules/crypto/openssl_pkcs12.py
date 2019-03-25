#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# Copyright (c) 2017 Guillaume Delpierre <gde@llew.me>

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: openssl_pkcs12
author: "Guillaume Delpierre (@gdelpierre)"
version_added: "2.7"
short_description: Generate OpenSSL PKCS#12 archive.
description:
    - This module allows one to (re-)generate PKCS#12.
requirements:
    - python-pyOpenSSL
options:
    action:
        default: export
        choices: ['parse', 'export']
        description:
            - C(export) or C(parse) a PKCS#12.
    ca_certificates:
        description:
            - List of CA certificate to include.
    certificate_path:
        description:
            - The path to read certificates and private keys from.  Must be in PEM format.
    force:
        default: False
        type: bool
        description:
            - Should the file be regenerated even if it already exists.
    friendly_name:
        aliases: ['name']
        description:
            - Specifies the friendly name for the certificate and private key.
    iter_size:
        default: 2048
        description:
            - Number of times to repeat the encryption step.
    maciter_size:
        default: 1
        description:
            - Number of times to repeat the MAC step.
    passphrase:
        description:
            - The PKCS#12 password.
    path:
        required: True
        description:
            - Filename to write the PKCS#12 file to.
    privatekey_passphrase:
        description:
            - Passphrase source to decrypt any input private keys with.
    privatekey_path:
        description:
            - File to read private key from.
    state:
        default: 'present'
        choices: ['present', 'absent']
        description:
            - Whether the file should exist or not.
              All parameters except C(path) are ignored when state is C(absent).
    src:
        description:
            - PKCS#12 file path to parse.

extends_documentation_fragment:
    - files
'''

EXAMPLES = '''
- name: 'Generate PKCS#12 file'
  openssl_pkcs12:
    action: export
    path: '/opt/certs/ansible.p12'
    friendly_name: 'raclette'
    privatekey_path: '/opt/certs/keys/key.pem'
    certificate_path: '/opt/certs/cert.pem'
    ca_certificates: '/opt/certs/ca.pem'
    state: present

- name: 'Change PKCS#12 file permission'
  openssl_pkcs12:
    action: export
    path: '/opt/certs/ansible.p12'
    friendly_name: 'raclette'
    privatekey_path: '/opt/certs/keys/key.pem'
    certificate_path: '/opt/certs/cert.pem'
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
    certificate_path: '/opt/certs/cert.pem'
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

import stat
import os

try:
    from OpenSSL import crypto
except ImportError:
    pyopenssl_found = False
else:
    pyopenssl_found = True

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import crypto as crypto_utils
from ansible.module_utils._text import to_bytes, to_native


class PkcsError(crypto_utils.OpenSSLObjectError):
    pass


class Pkcs(crypto_utils.OpenSSLObject):

    def __init__(self, module):
        super(Pkcs, self).__init__(
            module.params['path'],
            module.params['state'],
            module.params['force'],
            module.check_mode
        )
        self.action = module.params['action']
        self.ca_certificates = module.params['ca_certificates']
        self.certificate_path = module.params['certificate_path']
        self.friendly_name = module.params['friendly_name']
        self.iter_size = module.params['iter_size']
        self.maciter_size = module.params['maciter_size']
        self.passphrase = module.params['passphrase']
        self.pkcs12 = None
        self.privatekey_passphrase = module.params['privatekey_passphrase']
        self.privatekey_path = module.params['privatekey_path']
        self.src = module.params['src']

        if module.params['mode'] is None:
            module.params['mode'] = '0400'

    def check(self, module, perms_required=True):
        """Ensure the resource is in its desired state."""

        state_and_perms = super(Pkcs, self).check(module, perms_required)

        def _check_pkey_passphrase():
            if self.privatekey_passphrase:
                try:
                    crypto_utils.load_privatekey(self.path,
                                                 self.privatekey_passphrase)
                except crypto.Error:
                    return False
            return True

        if not state_and_perms:
            return state_and_perms

        return _check_pkey_passphrase

    def dump(self):
        """Serialize the object into a dictionary."""

        result = {
            'filename': self.path,
        }
        if self.privatekey_path:
            result['privatekey_path'] = self.privatekey_path

        return result

    def generate(self, module):
        """Generate PKCS#12 file archive."""

        self.pkcs12 = crypto.PKCS12()

        if self.ca_certificates:
            ca_certs = [crypto_utils.load_certificate(os.path.expanduser(os.path.expandvars(ca_cert))) for ca_cert
                        in self.ca_certificates]
            self.pkcs12.set_ca_certificates(ca_certs)

        if self.certificate_path:
            self.pkcs12.set_certificate(crypto_utils.load_certificate(
                                        self.certificate_path))

        if self.friendly_name:
            self.pkcs12.set_friendlyname(to_bytes(self.friendly_name))

        if self.privatekey_path:
            self.pkcs12.set_privatekey(crypto_utils.load_privatekey(
                                       self.privatekey_path,
                                       self.privatekey_passphrase)
                                       )

        crypto_utils.write_file(
            module,
            self.pkcs12.export(self.passphrase, self.iter_size, self.maciter_size),
            0o600
        )

    def parse(self, module):
        """Read PKCS#12 file."""

        try:
            with open(self.src, 'rb') as pkcs12_fh:
                pkcs12_content = pkcs12_fh.read()
            p12 = crypto.load_pkcs12(pkcs12_content,
                                     self.passphrase)
            pkey = crypto.dump_privatekey(crypto.FILETYPE_PEM,
                                          p12.get_privatekey())
            crt = crypto.dump_certificate(crypto.FILETYPE_PEM,
                                          p12.get_certificate())

            crypto_utils.write_file(module, b'%s%s' % (pkey, crt))

        except IOError as exc:
            raise PkcsError(exc)


def main():
    argument_spec = dict(
        action=dict(type='str', default='export',
                    choices=['parse', 'export']),
        ca_certificates=dict(type='list'),
        certificate_path=dict(type='path'),
        force=dict(type='bool', default=False),
        friendly_name=dict(type='str', aliases=['name']),
        iter_size=dict(type='int', default=2048),
        maciter_size=dict(type='int', default=1),
        passphrase=dict(type='str', no_log=True),
        path=dict(type='path', required=True),
        privatekey_passphrase=dict(type='str', no_log=True),
        privatekey_path=dict(type='path'),
        state=dict(type='str', default='present',
                   choices=['present', 'absent']),
        src=dict(type='path'),
    )

    required_if = [
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

    base_dir = os.path.dirname(module.params['path']) or '.'
    if not os.path.isdir(base_dir):
        module.fail_json(
            name=base_dir,
            msg='The directory %s does not exist or '
                'the path is not a directory' % base_dir
        )

    pkcs12 = Pkcs(module)
    changed = False

    if module.params['state'] == 'present':
        if module.check_mode:
            result = pkcs12.dump()
            result['changed'] = module.params['force'] or not pkcs12.check(module)
            module.exit_json(**result)

        try:
            if not pkcs12.check(module, perms_required=False) or module.params['force']:
                if module.params['action'] == 'export':
                    if not module.params['friendly_name']:
                        module.fail_json(msg='Friendly_name is required')
                    pkcs12.generate(module)
                    changed = True
                else:
                    pkcs12.parse(module)

            file_args = module.load_file_common_arguments(module.params)
            if module.set_fs_attributes_if_different(file_args, changed):
                changed = True

        except PkcsError as exc:
            module.fail_json(msg=to_native(exc))
    else:
        if module.check_mode:
            result = pkcs12.dump()
            result['changed'] = os.path.exists(module.params['path'])
            module.exit_json(**result)

        if os.path.exists(module.params['path']):
            try:
                pkcs12.remove()
                changed = True
            except PkcsError as exc:
                module.fail_json(msg=to_native(exc))

    result = pkcs12.dump()
    result['changed'] = changed
    if os.path.exists(module.params['path']):
        file_mode = "%04o" % stat.S_IMODE(os.stat(module.params['path']).st_mode)
        result['mode'] = file_mode

    module.exit_json(**result)


if __name__ == '__main__':
    main()
