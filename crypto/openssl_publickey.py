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
module: openssl_publickey
author: "Yanis Guenane (@Spredzy)"
version_added: "2.3"
short_description: Generate an OpenSSL public key from its private key.
description:
    - "This module allows one to (re)generate OpenSSL public keys from their private keys.
       It uses the pyOpenSSL python library to interact with openssl. Keys are generated
       in PEM format. This module works only if the version of PyOpenSSL is recent enough (> 16.0.0)"
requirements:
    - "python-pyOpenSSL"
options:
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the public key should exist or not, taking action if the state is different from what is stated.
    force:
        required: false
        default: False
        choices: [ True, False ]
        description:
            - Should the key be regenerated even it it already exists
    path:
        required: true
        description:
            - Name of the file in which the generated TLS/SSL public key will be written.
    privatekey_path:
        required: true
        description:
            - Path to the TLS/SSL private key from which to genereate the public key.
'''

EXAMPLES = '''
# Generate an OpenSSL public key.
- openssl_publickey:
    path: /etc/ssl/public/ansible.com.pem
    privatekey_path: /etc/ssl/private/ansible.com.pem

# Force regenerate an OpenSSL public key if it already exists
- openssl_publickey:
    path: /etc/ssl/public/ansible.com.pem
    privatekey_path: /etc/ssl/private/ansible.com.pem
    force: True

# Remove an OpenSSL public key
- openssl_publickey:
    path: /etc/ssl/public/ansible.com.pem
    privatekey_path: /etc/ssl/private/ansible.com.pem
    state: absent
'''

RETURN = '''
privatekey:
    description: Path to the TLS/SSL private key the public key was generated from
    returned:
        - changed
        - success
    type: string
    sample: /etc/ssl/private/ansible.com.pem
filename:
    description: Path to the generated TLS/SSL public key file
    returned:
        - changed
        - success
    type: string
    sample: /etc/ssl/public/ansible.com.pem
'''

class PublicKeyError(Exception):
    pass

class PublicKey(object):

    def __init__(self, module):
        self.state = module.params['state']
        self.force = module.params['force']
        self.name = os.path.basename(module.params['path'])
        self.path = module.params['path']
        self.privatekey_path = module.params['privatekey_path']
        self.changed = True
        self.check_mode = module.check_mode


    def generate(self, module):
        """Generate the public key.."""

        if not os.path.exists(self.path) or self.force:
            try:
                 privatekey_content = open(self.privatekey_path, 'r').read()
                 privatekey = crypto.load_privatekey(crypto.FILETYPE_PEM, privatekey_content)
                 publickey_file = open(self.path, 'w')
                 publickey_file.write(crypto.dump_publickey(crypto.FILETYPE_PEM, privatekey))
                 publickey_file.close()
            except (IOError, OSError):
                e = get_exception()
                raise PublicKeyError(e)
            except AttributeError:
                self.remove()
                raise PublicKeyError('You need to have PyOpenSSL>=16.0.0 to generate public keys')
        else:
            self.changed = False

        file_args = module.load_file_common_arguments(module.params)
        if module.set_fs_attributes_if_different(file_args, False):
            self.changed = True

    def remove(self):
        """Remove the public key from the filesystem."""

        try:
            os.remove(self.path)
        except OSError:
            e = get_exception()
            if e.errno != errno.ENOENT:
                raise PublicKeyError(e)
            else:
                self.changed = False

    def dump(self):
        """Serialize the object into a dictionnary."""

        result = {
            'privatekey': self.privatekey_path,
            'filename': self.path,
            'changed': self.changed,
        }

        return result
        

def main():

    module = AnsibleModule(
        argument_spec = dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            force=dict(default=False, type='bool'),
            path=dict(required=True, type='path'),
            privatekey_path=dict(type='path'),
        ),
        supports_check_mode = True,
        add_file_common_args = True,
    )

    if not pyopenssl_found:
        module.fail_json(msg='the python pyOpenSSL module is required')

    path = module.params['path']
    privatekey_path = module.params['privatekey_path']
    base_dir = os.path.dirname(module.params['path'])

    if not os.path.isdir(base_dir):
        module.fail_json(name=base_dir, msg='The directory %s does not exist or the file is not a directory' % base_dir)

    public_key = PublicKey(module)
    if public_key.state == 'present':

        # This is only applicable when generating a new public key.
        # When removing one the privatekey_path should not be required.
        if not privatekey_path:
            module.fail_json(msg='When generating a new public key you must specify a private key')

        if not os.path.exists(privatekey_path):
            module.fail_json(name=privatekey_path, msg='The private key %s does not exist' % privatekey_path)

        if module.check_mode:
            result = public_key.dump()
            result['changed'] = module.params['force'] or not os.path.exists(path)
            module.exit_json(**result)

        try:
            public_key.generate(module)
        except PublicKeyError:
            e = get_exception()
            module.fail_json(msg=str(e))
    else:

        if module.check_mode:
            result = public_key.dump()
            result['changed'] = os.path.exists(path)
            module.exit_json(**result)

        try:
            public_key.remove()
        except PublicKeyError:
            e = get_exception()
            module.fail_json(msg=str(e))

    result = public_key.dump()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
