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

from ansible.module_utils.basic import *

try:
    from OpenSSL import crypto
except ImportError:
    pyopenssl_found = False
else:
    pyopenssl_found = True


import os

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
    returned:
        - changed
        - success
    type: integer
    sample: 4096
type:
    description: Algorithm used to generate the TLS/SSL private key
    returned:
        - changed
        - success
    type: string
    sample: RSA
filename:
    description: Path to the generated TLS/SSL private key file
    returned:
        - changed
        - success
    type: string
    sample: /etc/ssl/private/ansible.com.pem
'''

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


    def generate(self, module):
        """Generate a keypair."""

        if not os.path.exists(self.path) or self.force:
            self.privatekey = crypto.PKey()

            if self.type == 'RSA':
                crypto_type = crypto.TYPE_RSA
            else:
                crypto_type = crypto.TYPE_DSA

            try:
                self.privatekey.generate_key(crypto_type, self.size)
            except (TypeError, ValueError):
                raise PrivateKeyError(get_exception())

            try:
                privatekey_file = os.open(self.path,
                                          os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                                          self.mode)

                os.write(privatekey_file, crypto.dump_privatekey(crypto.FILETYPE_PEM, self.privatekey))
                os.close(privatekey_file)
            except IOError:
                self.remove()
                raise PrivateKeyError(get_exception())
        else:
            self.changed = False

        file_args = module.load_file_common_arguments(module.params)
        if module.set_fs_attributes_if_different(file_args, False):
            self.changed = True


    def remove(self):
        """Remove the private key from the filesystem."""

        try:
            os.remove(self.path)
        except OSError:
            e = get_exception()
            if e.errno != errno.ENOENT:
                raise PrivateKeyError(e)
            else:
                self.changed = False


    def dump(self):
        """Serialize the object into a dictionnary."""

        result = {
            'size': self.size,
            'type': self.type,
            'filename': self.path,
            'changed': self.changed,
        }

        return result
        

def main():

    module = AnsibleModule(
        argument_spec = dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            size=dict(default=4096, type='int'),
            type=dict(default='RSA', choices=['RSA', 'DSA'], type='str'),
            force=dict(default=False, type='bool'),
            path=dict(required=True, type='path'),
        ),
        supports_check_mode = True,
        add_file_common_args = True,
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

        if module.check_mode:
            result = private_key.dump()
            result['changed'] = module.params['force'] or not os.path.exists(path)
            module.exit_json(**result)

        try:
            private_key.generate(module)
        except PrivateKeyError:
            e = get_exception()
            module.fail_json(msg=str(e))
    else:

        if module.check_mode:
            result = private_key.dump()
            result['changed'] = os.path.exists(path)
            module.exit_json(**result)

        try:
            private_key.remove()
        except PrivateKeyError:
            e = get_exception()
            module.fail_json(msg=str(e))

    result = private_key.dump()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
