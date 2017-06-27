#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Yanis Guenane <yanis+ansible@guenane.org>
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
        choices: [ True, False ]
        description:
            - Should the key be regenerated even it it already exists
    path:
        required: true
        description:
            - Name of the file in which the generated TLS/SSL private key will be written. It will have 0600 mode.
'''

EXAMPLES = '''
# Generate an OpenSSL private key with the default values (4096 bits, RSA)
# and no public key
- openssl_privatekey:
    path: /etc/ssl/private/ansible.com.pem

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
'''

from ansible.module_utils.basic import *

try:
    from OpenSSL import crypto
except ImportError:
    pyopenssl_found = False
else:
    pyopenssl_found = True


import os
from ansible.module_utils._text import to_native


class PrivateKeyError(Exception):
    pass


class PrivateKey(object):

    def __init__(self, module):
        self.size = module.params['size']
        self.state = module.params['state']
        self.name = os.path.basename(module.params['path'])
        self.type = module.params['type']
        self.force = module.params['force']
        self.path = module.params['path']
        self.mode = module.params['mode']
        self.changed = True
        self.check_mode = module.check_mode

        self._needs_generating = True
        if self.type == 'RSA':
            self._type_id = crypto.TYPE_RSA
        else:
            self._type_id = crypto.TYPE_DSA

    def generate(self, module):
        """Generate a keypair."""

        if self._needs_generating:
            self.privatekey = crypto.PKey()

            try:
                self.privatekey.generate_key(self._type_id, self.size)
            except (TypeError, ValueError) as exc:
                raise PrivateKeyError(exc)

            try:
                privatekey_file = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, self.mode)
                os.write(privatekey_file, crypto.dump_privatekey(crypto.FILETYPE_PEM, self.privatekey))
                os.close(privatekey_file)
            except IOError as exc:
                self.remove()
                raise PrivateKeyError(exc)

        file_args = module.load_file_common_arguments(module.params)
        if module.set_fs_attributes_if_different(file_args, False):
            self.changed = True

    def check(self, module):
        """check if keypair exists and complies with user values."""

        self.changed = True
        self._needs_generating = True

        if not os.path.exists(self.path) or self.force:
            return

        try:
            privatekey_content = open(self.path, 'r').read()
            privatekey = crypto.load_privatekey(crypto.FILETYPE_PEM, privatekey_content)
            if self._type_id != privatekey.type():
                return
            if self.size != privatekey.bits():
                return
        except (IOError, OSError) as exc:
            raise PrivateKeyError(exc)

        self._needs_generating = False

        if module.check_mode:
            file_args = module.load_file_common_arguments(module.params)
            if module.set_fs_attributes_if_different(file_args, False):
                return

        self.changed = False

    def remove(self):
        """Remove the private key from the filesystem."""

        try:
            os.remove(self.path)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise PrivateKeyError(exc)
            else:
                self.changed = False

    def dump(self):
        """Serialize the object into a dictionary."""

        result = {
            'size': self.size,
            'type': self.type,
            'filename': self.path,
            'changed': self.changed,
        }

        return result


def main():

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            size=dict(default=4096, type='int'),
            type=dict(default='RSA', choices=['RSA', 'DSA'], type='str'),
            force=dict(default=False, type='bool'),
            path=dict(required=True, type='path'),
        ),
        supports_check_mode=True,
        add_file_common_args=True,
    )

    if not pyopenssl_found:
        module.fail_json(msg='the python pyOpenSSL module is required')

    path = module.params['path']
    base_dir = os.path.dirname(module.params['path'])

    if not os.path.isdir(base_dir):
        module.fail_json(name=base_dir, msg='The directory %s does not exist or the file is not a directory' % base_dir)

    if not module.params['mode']:
        module.params['mode'] = int('0600', 8)

    private_key = PrivateKey(module)
    if private_key.state == 'present':

        try:
            private_key.check(module)
        except PrivateKeyError as exc:
            module.fail_json(msg=to_native(exc))

        if module.check_mode:
            result = private_key.dump()
            module.exit_json(**result)

        try:
            private_key.generate(module)
        except PrivateKeyError as exc:
            module.fail_json(msg=to_native(exc))
    else:

        if module.check_mode:
            result = private_key.dump()
            result['changed'] = os.path.exists(path)
            module.exit_json(**result)

        try:
            private_key.remove()
        except PrivateKeyError as exc:
            module.fail_json(msg=to_native(exc))

    result = private_key.dump()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
