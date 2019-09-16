#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Guillaume Delpierre <gde@llew.me>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: openssl_pkcs12
author:
- Guillaume Delpierre (@gdelpierre)
version_added: "2.7"
short_description: Generate OpenSSL PKCS#12 archive
description:
    - This module allows one to (re-)generate PKCS#12.
requirements:
    - python-pyOpenSSL
options:
    action:
        description:
            - C(export) or C(parse) a PKCS#12.
        type: str
        default: export
        choices: [ export, parse ]
    other_certificates:
        description:
            - List of other certificates to include. Pre 2.8 this parameter was called C(ca_certificates)
        type: list
        aliases: [ ca_certificates ]
    certificate_path:
        description:
            - The path to read certificates and private keys from.
            - Must be in PEM format.
        type: path
    force:
        description:
            - Should the file be regenerated even if it already exists.
        type: bool
        default: no
    friendly_name:
        description:
            - Specifies the friendly name for the certificate and private key.
        type: str
        aliases: [ name ]
    iter_size:
        description:
            - Number of times to repeat the encryption step.
        type: int
        default: 2048
    maciter_size:
        description:
            - Number of times to repeat the MAC step.
        type: int
        default: 1
    passphrase:
        description:
            - The PKCS#12 password.
        type: str
    path:
        description:
            - Filename to write the PKCS#12 file to.
        type: path
        required: true
    privatekey_passphrase:
        description:
            - Passphrase source to decrypt any input private keys with.
        type: str
    privatekey_path:
        description:
            - File to read private key from.
        type: path
    state:
        description:
            - Whether the file should exist or not.
              All parameters except C(path) are ignored when state is C(absent).
        choices: [ absent, present ]
        default: present
        type: str
    src:
        description:
            - PKCS#12 file path to parse.
        type: path
    backup:
        description:
            - Create a backup file including a timestamp so you can get the original
              output file back if you overwrote it with a new one by accident.
        type: bool
        default: no
        version_added: "2.8"
extends_documentation_fragment:
    - files
seealso:
- module: openssl_certificate
- module: openssl_csr
- module: openssl_dhparam
- module: openssl_privatekey
- module: openssl_publickey
'''

EXAMPLES = r'''
- name: Generate PKCS#12 file
  openssl_pkcs12:
    action: export
    path: /opt/certs/ansible.p12
    friendly_name: raclette
    privatekey_path: /opt/certs/keys/key.pem
    certificate_path: /opt/certs/cert.pem
    other_certificates: /opt/certs/ca.pem
    state: present

- name: Change PKCS#12 file permission
  openssl_pkcs12:
    action: export
    path: /opt/certs/ansible.p12
    friendly_name: raclette
    privatekey_path: /opt/certs/keys/key.pem
    certificate_path: /opt/certs/cert.pem
    other_certificates: /opt/certs/ca.pem
    state: present
    mode: '0600'

- name: Regen PKCS#12 file
  openssl_pkcs12:
    action: export
    src: /opt/certs/ansible.p12
    path: /opt/certs/ansible.p12
    friendly_name: raclette
    privatekey_path: /opt/certs/keys/key.pem
    certificate_path: /opt/certs/cert.pem
    other_certificates: /opt/certs/ca.pem
    state: present
    mode: '0600'
    force: yes

- name: Dump/Parse PKCS#12 file
  openssl_pkcs12:
    action: parse
    src: /opt/certs/ansible.p12
    path: /opt/certs/ansible.pem
    state: present

- name: Remove PKCS#12 file
  openssl_pkcs12:
    path: /opt/certs/ansible.p12
    state: absent
'''

RETURN = r'''
filename:
    description: Path to the generate PKCS#12 file.
    returned: changed or success
    type: str
    sample: /opt/certs/ansible.p12
privatekey:
    description: Path to the TLS/SSL private key the public key was generated from.
    returned: changed or success
    type: str
    sample: /etc/ssl/private/ansible.com.pem
backup_file:
    description: Name of backup file created.
    returned: changed and if I(backup) is C(yes)
    type: str
    sample: /path/to/ansible.com.pem.2019-03-09@11:22~
'''

import stat
import os
import traceback

PYOPENSSL_IMP_ERR = None
try:
    from OpenSSL import crypto
except ImportError:
    PYOPENSSL_IMP_ERR = traceback.format_exc()
    pyopenssl_found = False
else:
    pyopenssl_found = True

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
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
        self.other_certificates = module.params['other_certificates']
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

        self.backup = module.params['backup']
        self.backup_file = None

    def check(self, module, perms_required=True):
        """Ensure the resource is in its desired state."""

        state_and_perms = super(Pkcs, self).check(module, perms_required)

        def _check_pkey_passphrase():
            if self.privatekey_passphrase:
                try:
                    crypto_utils.load_privatekey(self.privatekey_path,
                                                 self.privatekey_passphrase)
                except crypto.Error:
                    return False
                except crypto_utils.OpenSSLBadPassphraseError:
                    return False
            return True

        if not state_and_perms:
            return state_and_perms

        if os.path.exists(self.path) and module.params['action'] == 'export':
            dummy = self.generate(module)
            self.src = self.path
            try:
                pkcs12_privatekey, pkcs12_certificate, pkcs12_other_certificates, pkcs12_friendly_name = self.parse()
            except crypto.Error:
                return False
            if (pkcs12_privatekey is not None) and (self.privatekey_path is not None):
                expected_pkey = crypto.dump_privatekey(crypto.FILETYPE_PEM,
                                                       self.pkcs12.get_privatekey())
                if pkcs12_privatekey != expected_pkey:
                    return False
            elif bool(pkcs12_privatekey) != bool(self.privatekey_path):
                return False

            if (pkcs12_certificate is not None) and (self.certificate_path is not None):

                expected_cert = crypto.dump_certificate(crypto.FILETYPE_PEM,
                                                        self.pkcs12.get_certificate())
                if pkcs12_certificate != expected_cert:
                    return False
            elif bool(pkcs12_certificate) != bool(self.certificate_path):
                return False

            if (pkcs12_other_certificates is not None) and (self.other_certificates is not None):
                expected_other_certs = [crypto.dump_certificate(crypto.FILETYPE_PEM,
                                                                other_cert) for other_cert in self.pkcs12.get_ca_certificates()]
                if set(pkcs12_other_certificates) != set(expected_other_certs):
                    return False
            elif bool(pkcs12_other_certificates) != bool(self.other_certificates):
                return False

            if pkcs12_privatekey:
                # This check is required because pyOpenSSL will not return a friendly name
                # if the private key is not set in the file
                if ((self.pkcs12.get_friendlyname() is not None) and (pkcs12_friendly_name is not None)):
                    if self.pkcs12.get_friendlyname() != pkcs12_friendly_name:
                        return False
                elif bool(self.pkcs12.get_friendlyname()) != bool(pkcs12_friendly_name):
                    return False
        else:
            return False

        return _check_pkey_passphrase()

    def dump(self):
        """Serialize the object into a dictionary."""

        result = {
            'filename': self.path,
        }
        if self.privatekey_path:
            result['privatekey_path'] = self.privatekey_path
        if self.backup_file:
            result['backup_file'] = self.backup_file

        return result

    def generate(self, module):
        """Generate PKCS#12 file archive."""
        self.pkcs12 = crypto.PKCS12()

        if self.other_certificates:
            other_certs = [crypto_utils.load_certificate(other_cert) for other_cert
                           in self.other_certificates]
            self.pkcs12.set_ca_certificates(other_certs)

        if self.certificate_path:
            self.pkcs12.set_certificate(crypto_utils.load_certificate(
                                        self.certificate_path))

        if self.friendly_name:
            self.pkcs12.set_friendlyname(to_bytes(self.friendly_name))

        if self.privatekey_path:
            try:
                self.pkcs12.set_privatekey(crypto_utils.load_privatekey(
                                           self.privatekey_path,
                                           self.privatekey_passphrase)
                                           )
            except crypto_utils.OpenSSLBadPassphraseError as exc:
                raise PkcsError(exc)

        return self.pkcs12.export(self.passphrase, self.iter_size, self.maciter_size)

    def remove(self, module):
        if self.backup:
            self.backup_file = module.backup_local(self.path)
        super(Pkcs, self).remove(module)

    def parse(self):
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
            other_certs = []
            if p12.get_ca_certificates() is not None:
                other_certs = [crypto.dump_certificate(crypto.FILETYPE_PEM,
                                                       other_cert) for other_cert in p12.get_ca_certificates()]

            friendly_name = p12.get_friendlyname()

            return (pkey, crt, other_certs, friendly_name)

        except IOError as exc:
            raise PkcsError(exc)

    def write(self, module, content, mode=None):
        """Write the PKCS#12 file."""
        if self.backup:
            self.backup_file = module.backup_local(self.path)
        crypto_utils.write_file(module, content, mode)


def main():
    argument_spec = dict(
        action=dict(type='str', default='export', choices=['export', 'parse']),
        other_certificates=dict(type='list', elements='path', aliases=['ca_certificates']),
        certificate_path=dict(type='path'),
        force=dict(type='bool', default=False),
        friendly_name=dict(type='str', aliases=['name']),
        iter_size=dict(type='int', default=2048),
        maciter_size=dict(type='int', default=1),
        passphrase=dict(type='str', no_log=True),
        path=dict(type='path', required=True),
        privatekey_passphrase=dict(type='str', no_log=True),
        privatekey_path=dict(type='path'),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        src=dict(type='path'),
        backup=dict(type='bool', default=False),
    )

    required_if = [
        ['action', 'parse', ['src']],
    ]

    module = AnsibleModule(
        add_file_common_args=True,
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=True,
    )

    if not pyopenssl_found:
        module.fail_json(msg=missing_required_lib('pyOpenSSL'), exception=PYOPENSSL_IMP_ERR)

    base_dir = os.path.dirname(module.params['path']) or '.'
    if not os.path.isdir(base_dir):
        module.fail_json(
            name=base_dir,
            msg="The directory '%s' does not exist or the path is not a directory" % base_dir
        )

    try:
        pkcs12 = Pkcs(module)
        changed = False

        if module.params['state'] == 'present':
            if module.check_mode:
                result = pkcs12.dump()
                result['changed'] = module.params['force'] or not pkcs12.check(module)
                module.exit_json(**result)

            if not pkcs12.check(module, perms_required=False) or module.params['force']:
                if module.params['action'] == 'export':
                    if not module.params['friendly_name']:
                        module.fail_json(msg='Friendly_name is required')
                    pkcs12_content = pkcs12.generate(module)
                    pkcs12.write(module, pkcs12_content, 0o600)
                    changed = True
                else:
                    pkey, cert, other_certs, friendly_name = pkcs12.parse()
                    dump_content = '%s%s%s' % (to_native(pkey), to_native(cert), to_native(b''.join(other_certs)))
                    pkcs12.write(module, to_bytes(dump_content))

            file_args = module.load_file_common_arguments(module.params)
            if module.set_fs_attributes_if_different(file_args, changed):
                changed = True
        else:
            if module.check_mode:
                result = pkcs12.dump()
                result['changed'] = os.path.exists(module.params['path'])
                module.exit_json(**result)

            if os.path.exists(module.params['path']):
                pkcs12.remove(module)
                changed = True

        result = pkcs12.dump()
        result['changed'] = changed
        if os.path.exists(module.params['path']):
            file_mode = "%04o" % stat.S_IMODE(os.stat(module.params['path']).st_mode)
            result['mode'] = file_mode

        module.exit_json(**result)
    except crypto_utils.OpenSSLObjectError as exc:
        module.fail_json(msg=to_native(exc))


if __name__ == '__main__':
    main()
