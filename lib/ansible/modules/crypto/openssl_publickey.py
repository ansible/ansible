#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Yanis Guenane <yanis+ansible@guenane.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: openssl_publickey
version_added: "2.3"
short_description: Generate an OpenSSL public key from its private key.
description:
    - This module allows one to (re)generate OpenSSL public keys from their private keys.
    - It uses the pyOpenSSL python library to interact with openssl.
    - Keys are generated in PEM format.
    - This module works only if the version of PyOpenSSL is recent enough (> 16.0.0).
requirements:
    - python-pyOpenSSL
author:
- Yanis Guenane (@Spredzy)
options:
    state:
        description:
            - Whether the public key should exist or not, taking action if the state is different from what is stated.
        type: str
        default: present
        choices: [ absent, present ]
    force:
        description:
            - Should the key be regenerated even it it already exists.
        type: bool
        default: no
    format:
        description:
            - The format of the public key.
        type: str
        default: PEM
        choices: [ OpenSSH, PEM ]
        version_added: "2.4"
    path:
        description:
            - Name of the file in which the generated TLS/SSL public key will be written.
        type: path
        required: true
    privatekey_path:
        description:
            - Path to the TLS/SSL private key from which to generate the public key.
        type: path
        required: true
    privatekey_passphrase:
        description:
            - The passphrase for the private key.
        type: str
        version_added: "2.4"
    backup:
        description:
            - Create a backup file including a timestamp so you can get the original
              public key back if you overwrote it with a different one by accident.
        type: bool
        default: no
        version_added: "2.8"
extends_documentation_fragment:
- files
seealso:
- module: openssl_certificate
- module: openssl_csr
- module: openssl_dhparam
- module: openssl_pkcs12
- module: openssl_privatekey
'''

EXAMPLES = r'''
- name: Generate an OpenSSL public key in PEM format
  openssl_publickey:
    path: /etc/ssl/public/ansible.com.pem
    privatekey_path: /etc/ssl/private/ansible.com.pem

- name: Generate an OpenSSL public key in OpenSSH v2 format
  openssl_publickey:
    path: /etc/ssl/public/ansible.com.pem
    privatekey_path: /etc/ssl/private/ansible.com.pem
    format: OpenSSH

- name: Generate an OpenSSL public key with a passphrase protected private key
  openssl_publickey:
    path: /etc/ssl/public/ansible.com.pem
    privatekey_path: /etc/ssl/private/ansible.com.pem
    privatekey_passphrase: ansible

- name: Force regenerate an OpenSSL public key if it already exists
  openssl_publickey:
    path: /etc/ssl/public/ansible.com.pem
    privatekey_path: /etc/ssl/private/ansible.com.pem
    force: yes

- name: Remove an OpenSSL public key
  openssl_publickey:
    path: /etc/ssl/public/ansible.com.pem
    privatekey_path: /etc/ssl/private/ansible.com.pem
    state: absent
'''

RETURN = r'''
privatekey:
    description: Path to the TLS/SSL private key the public key was generated from.
    returned: changed or success
    type: str
    sample: /etc/ssl/private/ansible.com.pem
format:
    description: The format of the public key (PEM, OpenSSH, ...).
    returned: changed or success
    type: str
    sample: PEM
filename:
    description: Path to the generated TLS/SSL public key file.
    returned: changed or success
    type: str
    sample: /etc/ssl/public/ansible.com.pem
fingerprint:
    description:
    - The fingerprint of the public key. Fingerprint will be generated for each hashlib.algorithms available.
    - Requires PyOpenSSL >= 16.0 for meaningful output.
    returned: changed or success
    type: dict
    sample:
      md5: "84:75:71:72:8d:04:b5:6c:4d:37:6d:66:83:f5:4c:29"
      sha1: "51:cc:7c:68:5d:eb:41:43:88:7e:1a:ae:c7:f8:24:72:ee:71:f6:10"
      sha224: "b1:19:a6:6c:14:ac:33:1d:ed:18:50:d3:06:5c:b2:32:91:f1:f1:52:8c:cb:d5:75:e9:f5:9b:46"
      sha256: "41:ab:c7:cb:d5:5f:30:60:46:99:ac:d4:00:70:cf:a1:76:4f:24:5d:10:24:57:5d:51:6e:09:97:df:2f:de:c7"
      sha384: "85:39:50:4e:de:d9:19:33:40:70:ae:10:ab:59:24:19:51:c3:a2:e4:0b:1c:b1:6e:dd:b3:0c:d9:9e:6a:46:af:da:18:f8:ef:ae:2e:c0:9a:75:2c:9b:b3:0f:3a:5f:3d"
      sha512: "fd:ed:5e:39:48:5f:9f:fe:7f:25:06:3f:79:08:cd:ee:a5:e7:b3:3d:13:82:87:1f:84:e1:f5:c7:28:77:53:94:86:56:38:69:f0:d9:35:22:01:1e:a6:60:...:0f:9b"
backup_file:
    description: Name of backup file created.
    returned: changed and if I(backup) is C(yes)
    type: str
    sample: /path/to/publickey.pem.2019-03-09@11:22~
'''

import os
import traceback

PYOPENSSL_IMP_ERR = None
try:
    from OpenSSL import crypto
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization as crypto_serialization
except ImportError:
    PYOPENSSL_IMP_ERR = traceback.format_exc()
    pyopenssl_found = False
else:
    pyopenssl_found = True

from ansible.module_utils import crypto as crypto_utils
from ansible.module_utils._text import to_native, to_bytes
from ansible.module_utils.basic import AnsibleModule, missing_required_lib


class PublicKeyError(crypto_utils.OpenSSLObjectError):
    pass


class PublicKey(crypto_utils.OpenSSLObject):

    def __init__(self, module):
        super(PublicKey, self).__init__(
            module.params['path'],
            module.params['state'],
            module.params['force'],
            module.check_mode
        )
        self.format = module.params['format']
        self.privatekey_path = module.params['privatekey_path']
        self.privatekey_passphrase = module.params['privatekey_passphrase']
        self.privatekey = None
        self.fingerprint = {}

        self.backup = module.params['backup']
        self.backup_file = None

    def generate(self, module):
        """Generate the public key."""

        if not os.path.exists(self.privatekey_path):
            raise PublicKeyError(
                'The private key %s does not exist' % self.privatekey_path
            )

        if not self.check(module, perms_required=False) or self.force:
            try:
                if self.format == 'OpenSSH':
                    with open(self.privatekey_path, 'rb') as private_key_fh:
                        privatekey_content = private_key_fh.read()
                    key = crypto_serialization.load_pem_private_key(
                        privatekey_content,
                        password=None if self.privatekey_passphrase is None else to_bytes(self.privatekey_passphrase),
                        backend=default_backend()
                    )
                    publickey_content = key.public_key().public_bytes(
                        crypto_serialization.Encoding.OpenSSH,
                        crypto_serialization.PublicFormat.OpenSSH
                    )
                else:
                    self.privatekey = crypto_utils.load_privatekey(
                        self.privatekey_path, self.privatekey_passphrase
                    )
                    publickey_content = crypto.dump_publickey(crypto.FILETYPE_PEM, self.privatekey)

                if self.backup:
                    self.backup_file = module.backup_local(self.path)
                crypto_utils.write_file(module, publickey_content)

                self.changed = True
            except crypto_utils.OpenSSLBadPassphraseError as exc:
                raise PublicKeyError(exc)
            except (IOError, OSError) as exc:
                raise PublicKeyError(exc)
            except AttributeError as exc:
                raise PublicKeyError('You need to have PyOpenSSL>=16.0.0 to generate public keys')

        self.fingerprint = crypto_utils.get_fingerprint(
            self.privatekey_path,
            self.privatekey_passphrase
        )
        file_args = module.load_file_common_arguments(module.params)
        if module.set_fs_attributes_if_different(file_args, False):
            self.changed = True

    def check(self, module, perms_required=True):
        """Ensure the resource is in its desired state."""

        state_and_perms = super(PublicKey, self).check(module, perms_required)

        def _check_privatekey():
            if not os.path.exists(self.privatekey_path):
                return False

            try:
                with open(self.path, 'rb') as public_key_fh:
                    publickey_content = public_key_fh.read()
                if self.format == 'OpenSSH':
                    current_publickey = crypto_serialization.load_ssh_public_key(publickey_content, backend=default_backend())
                    publickey_content = current_publickey.public_bytes(crypto_serialization.Encoding.PEM,
                                                                       crypto_serialization.PublicFormat.SubjectPublicKeyInfo)
                current_publickey = crypto.dump_publickey(
                    crypto.FILETYPE_ASN1,
                    crypto.load_publickey(crypto.FILETYPE_PEM, publickey_content)
                )
            except Exception as dummy:
                return False

            try:
                desired_publickey = crypto.dump_publickey(
                    crypto.FILETYPE_ASN1,
                    crypto_utils.load_privatekey(self.privatekey_path, self.privatekey_passphrase)
                )
            except crypto_utils.OpenSSLBadPassphraseError as exc:
                raise PublicKeyError(exc)

            return current_publickey == desired_publickey

        if not state_and_perms:
            return state_and_perms

        return _check_privatekey()

    def remove(self, module):
        if self.backup:
            self.backup_file = module.backup_local(self.path)
        super(PublicKey, self).remove(module)

    def dump(self):
        """Serialize the object into a dictionary."""

        result = {
            'privatekey': self.privatekey_path,
            'filename': self.path,
            'format': self.format,
            'changed': self.changed,
            'fingerprint': self.fingerprint,
        }
        if self.backup_file:
            result['backup_file'] = self.backup_file

        return result


def main():

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            force=dict(type='bool', default=False),
            path=dict(type='path', required=True),
            privatekey_path=dict(type='path'),
            format=dict(type='str', default='PEM', choices=['OpenSSH', 'PEM']),
            privatekey_passphrase=dict(type='str', no_log=True),
            backup=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
        add_file_common_args=True,
        required_if=[('state', 'present', ['privatekey_path'])],
    )

    if not pyopenssl_found:
        module.fail_json(msg=missing_required_lib('pyOpenSSL'), exception=PYOPENSSL_IMP_ERR)

    base_dir = os.path.dirname(module.params['path']) or '.'
    if not os.path.isdir(base_dir):
        module.fail_json(
            name=base_dir,
            msg="The directory '%s' does not exist or the file is not a directory" % base_dir
        )

    try:
        public_key = PublicKey(module)

        if public_key.state == 'present':
            if module.check_mode:
                result = public_key.dump()
                result['changed'] = module.params['force'] or not public_key.check(module)
                module.exit_json(**result)

            public_key.generate(module)
        else:
            if module.check_mode:
                result = public_key.dump()
                result['changed'] = os.path.exists(module.params['path'])
                module.exit_json(**result)

            public_key.remove(module)

        result = public_key.dump()
        module.exit_json(**result)
    except crypto_utils.OpenSSLObjectError as exc:
        module.fail_json(msg=to_native(exc))


if __name__ == '__main__':
    main()
