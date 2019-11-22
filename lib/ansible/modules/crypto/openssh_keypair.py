#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, David Kainz <dkainz@mgit.at> <dave.jokain@gmx.at>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: openssh_keypair
author: "David Kainz (@lolcube)"
version_added: "2.8"
short_description: Generate OpenSSH private and public keys.
description:
    - "This module allows one to (re)generate OpenSSH private and public keys. It uses
      ssh-keygen to generate keys. One can generate C(rsa), C(dsa), C(rsa1), C(ed25519)
      or C(ecdsa) private keys."
requirements:
    - "ssh-keygen"
options:
    state:
        description:
            - Whether the private and public keys should exist or not, taking action if the state is different from what is stated.
        type: str
        default: present
        choices: [ present, absent ]
    size:
        description:
            - "Specifies the number of bits in the private key to create. For RSA keys, the minimum size is 1024 bits and the default is 4096 bits.
              Generally, 2048 bits is considered sufficient.  DSA keys must be exactly 1024 bits as specified by FIPS 186-2.
              For ECDSA keys, size determines the key length by selecting from one of three elliptic curve sizes: 256, 384 or 521 bits.
              Attempting to use bit lengths other than these three values for ECDSA keys will cause this module to fail.
              Ed25519 keys have a fixed length and the size will be ignored."
        type: int
    type:
        description:
            - "The algorithm used to generate the SSH private key. C(rsa1) is for protocol version 1.
              C(rsa1) is deprecated and may not be supported by every version of ssh-keygen."
        type: str
        default: rsa
        choices: ['rsa', 'dsa', 'rsa1', 'ecdsa', 'ed25519']
    force:
        description:
            - Should the key be regenerated even if it already exists
        type: bool
        default: false
    path:
        description:
            - Name of the files containing the public and private key. The file containing the public key will have the extension C(.pub).
        type: path
        required: true
    comment:
        description:
            - Provides a new comment to the public key. When checking if the key is in the correct state this will be ignored.
        type: str
        version_added: "2.9"

extends_documentation_fragment: files
'''

EXAMPLES = '''
# Generate an OpenSSH keypair with the default values (4096 bits, rsa)
- openssh_keypair:
    path: /tmp/id_ssh_rsa

# Generate an OpenSSH rsa keypair with a different size (2048 bits)
- openssh_keypair:
    path: /tmp/id_ssh_rsa
    size: 2048

# Force regenerate an OpenSSH keypair if it already exists
- openssh_keypair:
    path: /tmp/id_ssh_rsa
    force: True

# Generate an OpenSSH keypair with a different algorithm (dsa)
- openssh_keypair:
    path: /tmp/id_ssh_dsa
    type: dsa
'''

RETURN = '''
size:
    description: Size (in bits) of the SSH private key
    returned: changed or success
    type: int
    sample: 4096
type:
    description: Algorithm used to generate the SSH private key
    returned: changed or success
    type: str
    sample: rsa
filename:
    description: Path to the generated SSH private key file
    returned: changed or success
    type: str
    sample: /tmp/id_ssh_rsa
fingerprint:
    description: The fingerprint of the key.
    returned: changed or success
    type: str
    sample: SHA256:r4YCZxihVjedH2OlfjVGI6Y5xAYtdCwk8VxKyzVyYfM
public_key:
    description: The public key of the generated SSH private key
    returned: changed or success
    type: str
    sample: ssh-rsa AAAAB3Nza(...omitted...)veL4E3Xcw== test_key
comment:
    description: The comment of the generated key
    returned: changed or success
    type: str
    sample: test@comment
'''

import os
import stat
import errno

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


class KeypairError(Exception):
    pass


class Keypair(object):

    def __init__(self, module):
        self.path = module.params['path']
        self.state = module.params['state']
        self.force = module.params['force']
        self.size = module.params['size']
        self.type = module.params['type']
        self.comment = module.params['comment']
        self.changed = False
        self.check_mode = module.check_mode
        self.privatekey = None
        self.fingerprint = {}
        self.public_key = {}

        if self.type in ('rsa', 'rsa1'):
            self.size = 4096 if self.size is None else self.size
            if self.size < 1024:
                module.fail_json(msg=('For RSA keys, the minimum size is 1024 bits and the default is 4096 bits. '
                                      'Attempting to use bit lengths under 1024 will cause the module to fail.'))

        if self.type == 'dsa':
            self.size = 1024 if self.size is None else self.size
            if self.size != 1024:
                module.fail_json(msg=('DSA keys must be exactly 1024 bits as specified by FIPS 186-2.'))

        if self.type == 'ecdsa':
            self.size = 256 if self.size is None else self.size
            if self.size not in (256, 384, 521):
                module.fail_json(msg=('For ECDSA keys, size determines the key length by selecting from '
                                      'one of three elliptic curve sizes: 256, 384 or 521 bits. '
                                      'Attempting to use bit lengths other than these three values for '
                                      'ECDSA keys will cause this module to fail. '))
        if self.type == 'ed25519':
            self.size = 256

    def generate(self, module):
        # generate a keypair
        if not self.isPrivateKeyValid(module, perms_required=False) or self.force:
            args = [
                module.get_bin_path('ssh-keygen', True),
                '-q',
                '-N', '',
                '-b', str(self.size),
                '-t', self.type,
                '-f', self.path,
            ]

            if self.comment:
                args.extend(['-C', self.comment])
            else:
                args.extend(['-C', ""])

            try:
                if os.path.exists(self.path) and not os.access(self.path, os.W_OK):
                    os.chmod(self.path, stat.S_IWUSR + stat.S_IRUSR)
                self.changed = True
                stdin_data = None
                if os.path.exists(self.path):
                    stdin_data = 'y'
                module.run_command(args, data=stdin_data)
                proc = module.run_command([module.get_bin_path('ssh-keygen', True), '-lf', self.path])
                self.fingerprint = proc[1].split()
                pubkey = module.run_command([module.get_bin_path('ssh-keygen', True), '-yf', self.path])
                self.public_key = pubkey[1].strip('\n')
            except Exception as e:
                self.remove()
                module.fail_json(msg="%s" % to_native(e))

        elif not self.isPublicKeyValid(module, perms_required=False):
            pubkey = module.run_command([module.get_bin_path('ssh-keygen', True), '-yf', self.path])
            pubkey = pubkey[1].strip('\n')
            try:
                self.changed = True
                with open(self.path + ".pub", "w") as pubkey_f:
                    pubkey_f.write(pubkey + '\n')
                os.chmod(self.path + ".pub", stat.S_IWUSR + stat.S_IRUSR + stat.S_IRGRP + stat.S_IROTH)
            except IOError:
                module.fail_json(
                    msg='The public key is missing or does not match the private key. '
                        'Unable to regenerate the public key.')
            self.public_key = pubkey

            if self.comment:
                try:
                    if os.path.exists(self.path) and not os.access(self.path, os.W_OK):
                        os.chmod(self.path, stat.S_IWUSR + stat.S_IRUSR)
                    args = [module.get_bin_path('ssh-keygen', True),
                            '-q', '-o', '-c', '-C', self.comment, '-f', self.path]
                    module.run_command(args)
                except IOError:
                    module.fail_json(
                        msg='Unable to update the comment for the public key.')

        file_args = module.load_file_common_arguments(module.params)
        if module.set_fs_attributes_if_different(file_args, False):
            self.changed = True
        file_args['path'] = file_args['path'] + '.pub'
        if module.set_fs_attributes_if_different(file_args, False):
            self.changed = True

    def isPrivateKeyValid(self, module, perms_required=True):

        # check if the key is correct
        def _check_state():
            return os.path.exists(self.path)

        if _check_state():
            proc = module.run_command([module.get_bin_path('ssh-keygen', True), '-lf', self.path], check_rc=False)
            if not proc[0] == 0:
                if os.path.isdir(self.path):
                    module.fail_json(msg='%s is a directory. Please specify a path to a file.' % (self.path))

                return False

            fingerprint = proc[1].split()
            keysize = int(fingerprint[0])
            keytype = fingerprint[-1][1:-1].lower()
        else:
            return False

        def _check_perms(module):
            file_args = module.load_file_common_arguments(module.params)
            return not module.set_fs_attributes_if_different(file_args, False)

        def _check_type():
            return self.type == keytype

        def _check_size():
            return self.size == keysize

        self.fingerprint = fingerprint

        if not perms_required:
            return _check_state() and _check_type() and _check_size()

        return _check_state() and _check_perms(module) and _check_type() and _check_size()

    def isPublicKeyValid(self, module, perms_required=True):

        def _get_pubkey_content():
            if os.path.exists(self.path + ".pub"):
                with open(self.path + ".pub", "r") as pubkey_f:
                    present_pubkey = pubkey_f.read().strip(' \n')
                return present_pubkey
            else:
                return False

        def _parse_pubkey(pubkey_content):
            if pubkey_content:
                parts = pubkey_content.split(' ', 2)
                return parts[0], parts[1], '' if len(parts) <= 2 else parts[2]
            return False

        def _pubkey_valid(pubkey):
            if pubkey_parts:
                return pubkey_parts[:2] == _parse_pubkey(pubkey)[:2]
            return False

        def _comment_valid():
            if pubkey_parts:
                return pubkey_parts[2] == self.comment
            return False

        def _check_perms(module):
            file_args = module.load_file_common_arguments(module.params)
            file_args['path'] = file_args['path'] + '.pub'
            return not module.set_fs_attributes_if_different(file_args, False)

        pubkey = module.run_command([module.get_bin_path('ssh-keygen', True), '-yf', self.path])
        pubkey = pubkey[1].strip('\n')
        pubkey_parts = _parse_pubkey(_get_pubkey_content())
        if _pubkey_valid(pubkey):
            self.public_key = pubkey

        if not self.comment:
            return _pubkey_valid(pubkey)

        if not perms_required:
            return _pubkey_valid(pubkey) and _comment_valid()

        return _pubkey_valid(pubkey) and _comment_valid() and _check_perms(module)

    def dump(self):
        # return result as a dict

        """Serialize the object into a dictionary."""
        result = {
            'changed': self.changed,
            'size': self.size,
            'type': self.type,
            'filename': self.path,
            # On removal this has no value
            'fingerprint': self.fingerprint[1] if self.fingerprint else '',
            'public_key': self.public_key,
            'comment': self.comment if self.comment else '',
        }

        return result

    def remove(self):
        """Remove the resource from the filesystem."""

        try:
            os.remove(self.path)
            self.changed = True
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise KeypairError(exc)
            else:
                pass

        if os.path.exists(self.path + ".pub"):
            try:
                os.remove(self.path + ".pub")
                self.changed = True
            except OSError as exc:
                if exc.errno != errno.ENOENT:
                    raise KeypairError(exc)
                else:
                    pass


def main():

    # Define Ansible Module
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            size=dict(type='int'),
            type=dict(type='str', default='rsa', choices=['rsa', 'dsa', 'rsa1', 'ecdsa', 'ed25519']),
            force=dict(type='bool', default=False),
            path=dict(type='path', required=True),
            comment=dict(type='str'),
        ),
        supports_check_mode=True,
        add_file_common_args=True,
    )

    # Check if Path exists
    base_dir = os.path.dirname(module.params['path']) or '.'
    if not os.path.isdir(base_dir):
        module.fail_json(
            name=base_dir,
            msg='The directory %s does not exist or the file is not a directory' % base_dir
        )

    keypair = Keypair(module)

    if keypair.state == 'present':

        if module.check_mode:
            result = keypair.dump()
            result['changed'] = module.params['force'] or not keypair.isPrivateKeyValid(module) or not keypair.isPublicKeyValid(module)
            module.exit_json(**result)

        try:
            keypair.generate(module)
        except Exception as exc:
            module.fail_json(msg=to_native(exc))
    else:

        if module.check_mode:
            keypair.changed = os.path.exists(module.params['path'])
            if keypair.changed:
                keypair.fingerprint = {}
            result = keypair.dump()
            module.exit_json(**result)

        try:
            keypair.remove()
        except Exception as exc:
            module.fail_json(msg=to_native(exc))

    result = keypair.dump()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
