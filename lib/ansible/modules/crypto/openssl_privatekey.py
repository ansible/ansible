#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Yanis Guenane <yanis+ansible@guenane.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: openssl_privatekey
author: "Yanis Guenane (@Spredzy)"
version_added: "2.3"
short_description: Generate OpenSSL private keys.
description:
    - "This module allows one to (re)generate OpenSSL private keys. It uses
       the pyOpenSSL python library to interact with openssl. One can generate
       either RSA or DSA private keys. Keys are generated in PEM format."
requirements:
    - "python-pyOpenSSL"
options:
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the private key should exist or not, taking action if the state is different from what is stated.
    size:
        required: false
        default: 4096
        description:
            - Size (in bits) of the TLS/SSL key to generate
    type:
        required: false
        default: "RSA"
        choices: [ RSA, DSA ]
        description:
            - The algorithm used to generate the TLS/SSL private key
    force:
        required: false
        default: False
        type: bool
        description:
            - Should the key be regenerated even it it already exists
    path:
        required: true
        description:
            - Name of the file in which the generated TLS/SSL private key will be written. It will have 0600 mode.
    passphrase:
        required: false
        description:
            - The passphrase for the private key.
        version_added: "2.4"
    cipher:
        required: false
        description:
            - The cipher to encrypt the private key. (cipher can be found by running `openssl list-cipher-algorithms`)
        version_added: "2.4"
extends_documentation_fragment: files
'''

EXAMPLES = '''
# Generate an OpenSSL private key with the default values (4096 bits, RSA)
- openssl_privatekey:
    path: /etc/ssl/private/ansible.com.pem

# Generate an OpenSSL private key with the default values (4096 bits, RSA)
# and a passphrase
- openssl_privatekey:
    path: /etc/ssl/private/ansible.com.pem
    passphrase: ansible
    cipher: aes256

# Generate an OpenSSL private key with a different size (2048 bits)
- openssl_privatekey:
    path: /etc/ssl/private/ansible.com.pem
    size: 2048

# Force regenerate an OpenSSL private key if it already exists
- openssl_privatekey:
    path: /etc/ssl/private/ansible.com.pem
    force: True

# Generate an OpenSSL private key with a different algorithm (DSA)
- openssl_privatekey:
    path: /etc/ssl/private/ansible.com.pem
    type: DSA
'''

RETURN = '''
size:
    description: Size (in bits) of the TLS/SSL private key
    returned: changed or success
    type: int
    sample: 4096
type:
    description: Algorithm used to generate the TLS/SSL private key
    returned: changed or success
    type: string
    sample: RSA
filename:
    description: Path to the generated TLS/SSL private key file
    returned: changed or success
    type: string
    sample: /etc/ssl/private/ansible.com.pem
fingerprint:
    description: The fingerprint of the public key. Fingerprint will be generated for each hashlib.algorithms available.
                 Requires PyOpenSSL >= 16.0 for meaningful output.
    returned: changed or success
    type: dict
    sample:
      md5: "84:75:71:72:8d:04:b5:6c:4d:37:6d:66:83:f5:4c:29"
      sha1: "51:cc:7c:68:5d:eb:41:43:88:7e:1a:ae:c7:f8:24:72:ee:71:f6:10"
      sha224: "b1:19:a6:6c:14:ac:33:1d:ed:18:50:d3:06:5c:b2:32:91:f1:f1:52:8c:cb:d5:75:e9:f5:9b:46"
      sha256: "41:ab:c7:cb:d5:5f:30:60:46:99:ac:d4:00:70:cf:a1:76:4f:24:5d:10:24:57:5d:51:6e:09:97:df:2f:de:c7"
      sha384: "85:39:50:4e:de:d9:19:33:40:70:ae:10:ab:59:24:19:51:c3:a2:e4:0b:1c:b1:6e:dd:b3:0c:d9:9e:6a:46:af:da:18:f8:ef:ae:2e:c0:9a:75:2c:9b:b3:0f:3a:5f:3d"
      sha512: "fd:ed:5e:39:48:5f:9f:fe:7f:25:06:3f:79:08:cd:ee:a5:e7:b3:3d:13:82:87:1f:84:e1:f5:c7:28:77:53:94:86:56:38:69:f0:d9:35:22:01:1e:a6:60:...:0f:9b"
'''

import os
import traceback

try:
    from OpenSSL import crypto
except ImportError:
    pyopenssl_found = False
else:
    pyopenssl_found = True

from ansible.module_utils import crypto as crypto_utils
from ansible.module_utils._text import to_native, to_bytes
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types


class PrivateKeyError(crypto_utils.OpenSSLObjectError):
    pass


class PrivateKey(crypto_utils.OpenSSLObject):

    def __init__(self, module):
        super(PrivateKey, self).__init__(
            module.params['path'],
            module.params['state'],
            module.params['force'],
            module.check_mode
        )
        self.size = module.params['size']
        self.passphrase = module.params['passphrase']
        self.cipher = module.params['cipher']
        self.privatekey = None
        self.fingerprint = {}

        self.mode = module.params.get('mode', None)
        if self.mode is None:
            self.mode = 0o600

        self.type = crypto.TYPE_RSA
        if module.params['type'] == 'DSA':
            self.type = crypto.TYPE_DSA

    def generate(self, module):
        """Generate a keypair."""

        if not self.check(module, perms_required=False) or self.force:
            self.privatekey = crypto.PKey()

            try:
                self.privatekey.generate_key(self.type, self.size)
            except (TypeError, ValueError) as exc:
                raise PrivateKeyError(exc)

            try:
                privatekey_file = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
                os.close(privatekey_file)
                if isinstance(self.mode, string_types):
                    try:
                        self.mode = int(self.mode, 8)
                    except ValueError as e:
                        try:
                            st = os.lstat(self.path)
                            self.mode = AnsibleModule._symbolic_mode_to_octal(st, self.mode)
                        except ValueError as e:
                            module.fail_json(msg="%s" % to_native(e), exception=traceback.format_exc())
                os.chmod(self.path, self.mode)
                privatekey_file = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, self.mode)
                if self.cipher and self.passphrase:
                    os.write(privatekey_file, crypto.dump_privatekey(crypto.FILETYPE_PEM, self.privatekey,
                                                                     self.cipher, to_bytes(self.passphrase)))
                else:
                    os.write(privatekey_file, crypto.dump_privatekey(crypto.FILETYPE_PEM, self.privatekey))
                os.close(privatekey_file)
                self.changed = True
            except IOError as exc:
                self.remove()
                raise PrivateKeyError(exc)

        self.fingerprint = crypto_utils.get_fingerprint(self.path, self.passphrase)
        file_args = module.load_file_common_arguments(module.params)
        if module.set_fs_attributes_if_different(file_args, False):
            self.changed = True

    def check(self, module, perms_required=True):
        """Ensure the resource is in its desired state."""

        state_and_perms = super(PrivateKey, self).check(module, perms_required)

        def _check_size(privatekey):
            return self.size == privatekey.bits()

        def _check_type(privatekey):
            return self.type == privatekey.type()

        def _check_passphrase():
            try:
                crypto_utils.load_privatekey(self.path, self.passphrase)
                return True
            except crypto.Error:
                return False

        if not state_and_perms or not _check_passphrase():
            return False

        privatekey = crypto_utils.load_privatekey(self.path, self.passphrase)

        return _check_size(privatekey) and _check_type(privatekey)

    def dump(self):
        """Serialize the object into a dictionary."""

        result = {
            'size': self.size,
            'filename': self.path,
            'changed': self.changed,
            'fingerprint': self.fingerprint,
        }

        if self.type == crypto.TYPE_RSA:
            result['type'] = 'RSA'
        else:
            result['type'] = 'DSA'

        return result


def main():

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            size=dict(default=4096, type='int'),
            type=dict(default='RSA', choices=['RSA', 'DSA'], type='str'),
            force=dict(default=False, type='bool'),
            path=dict(required=True, type='path'),
            passphrase=dict(type='str', no_log=True),
            cipher=dict(type='str'),
        ),
        supports_check_mode=True,
        add_file_common_args=True,
        required_together=[['cipher', 'passphrase']],
    )

    if not pyopenssl_found:
        module.fail_json(msg='the python pyOpenSSL module is required')

    base_dir = os.path.dirname(module.params['path'])
    if not os.path.isdir(base_dir):
        module.fail_json(
            name=base_dir,
            msg='The directory %s does not exist or the file is not a directory' % base_dir
        )

    private_key = PrivateKey(module)

    if private_key.state == 'present':

        if module.check_mode:
            result = private_key.dump()
            result['changed'] = module.params['force'] or not private_key.check(module)
            module.exit_json(**result)

        try:
            private_key.generate(module)
        except PrivateKeyError as exc:
            module.fail_json(msg=to_native(exc))
    else:

        if module.check_mode:
            result = private_key.dump()
            result['changed'] = os.path.exists(module.params['path'])
            module.exit_json(**result)

        try:
            private_key.remove()
        except PrivateKeyError as exc:
            module.fail_json(msg=to_native(exc))

    result = private_key.dump()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
