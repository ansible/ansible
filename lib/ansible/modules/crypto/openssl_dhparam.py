#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Thom Wiggers  <ansible@thomwiggers.nl>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: openssl_dhparam
version_added: "2.5"
short_description: Generate OpenSSL Diffie-Hellman Parameters
description:
    - This module allows one to (re)generate OpenSSL DH-params.
    - This module uses file common arguments to specify generated file permissions.
    - "Please note that the module regenerates existing DH params if they don't
      match the module's options. If you are concerned that this could overwrite
      your existing DH params, consider using the I(backup) option."
requirements:
    - OpenSSL
author:
- Thom Wiggers (@thomwiggers)
options:
    state:
        description:
            - Whether the parameters should exist or not,
              taking action if the state is different from what is stated.
        type: str
        default: present
        choices: [ absent, present ]
    size:
        description:
            - Size (in bits) of the generated DH-params.
        type: int
        default: 4096
    force:
        description:
            - Should the parameters be regenerated even it it already exists.
        type: bool
        default: no
    path:
        description:
            - Name of the file in which the generated parameters will be saved.
        type: path
        required: true
    backup:
        description:
            - Create a backup file including a timestamp so you can get the original
              DH params back if you overwrote them with new ones by accident.
        type: bool
        default: no
        version_added: "2.8"
extends_documentation_fragment:
- files
seealso:
- module: openssl_certificate
- module: openssl_csr
- module: openssl_pkcs12
- module: openssl_privatekey
- module: openssl_publickey
'''

EXAMPLES = r'''
- name: Generate Diffie-Hellman parameters with the default size (4096 bits)
  openssl_dhparam:
    path: /etc/ssl/dhparams.pem

- name: Generate DH Parameters with a different size (2048 bits)
  openssl_dhparam:
    path: /etc/ssl/dhparams.pem
    size: 2048

- name: Force regenerate an DH parameters if they already exist
  openssl_dhparam:
    path: /etc/ssl/dhparams.pem
    force: yes
'''

RETURN = r'''
size:
    description: Size (in bits) of the Diffie-Hellman parameters.
    returned: changed or success
    type: int
    sample: 4096
filename:
    description: Path to the generated Diffie-Hellman parameters.
    returned: changed or success
    type: str
    sample: /etc/ssl/dhparams.pem
backup_file:
    description: Name of backup file created.
    returned: changed and if I(backup) is C(yes)
    type: str
    sample: /path/to/dhparams.pem.2019-03-09@11:22~
'''

import os
import re
import tempfile

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


class DHParameterError(Exception):
    pass


class DHParameter(object):

    def __init__(self, module):
        self.state = module.params['state']
        self.path = module.params['path']
        self.size = module.params['size']
        self.force = module.params['force']
        self.changed = False
        self.openssl_bin = module.get_bin_path('openssl', True)

        self.backup = module.params['backup']
        self.backup_file = None

    def generate(self, module):
        """Generate a keypair."""
        changed = False

        # ony generate when necessary
        if self.force or not self._check_params_valid(module):
            # create a tempfile
            fd, tmpsrc = tempfile.mkstemp()
            os.close(fd)
            module.add_cleanup_file(tmpsrc)  # Ansible will delete the file on exit
            # openssl dhparam -out <path> <bits>
            command = [self.openssl_bin, 'dhparam', '-out', tmpsrc, str(self.size)]
            rc, dummy, err = module.run_command(command, check_rc=False)
            if rc != 0:
                raise DHParameterError(to_native(err))
            if self.backup:
                self.backup_file = module.backup_local(self.path)
            try:
                module.atomic_move(tmpsrc, self.path)
            except Exception as e:
                module.fail_json(msg="Failed to write to file %s: %s" % (self.path, str(e)))
            changed = True

        # fix permissions (checking force not necessary as done above)
        if not self._check_fs_attributes(module):
            # Fix done implicitly by
            # AnsibleModule.set_fs_attributes_if_different
            changed = True

        self.changed = changed

    def remove(self, module):
        if self.backup:
            self.backup_file = module.backup_local(self.path)
        try:
            os.remove(self.path)
            self.changed = True
        except OSError as exc:
            module.fail_json(msg=to_native(exc))

    def check(self, module):
        """Ensure the resource is in its desired state."""
        if self.force:
            return False
        return self._check_params_valid(module) and self._check_fs_attributes(module)

    def _check_params_valid(self, module):
        """Check if the params are in the correct state"""
        command = [self.openssl_bin, 'dhparam', '-check', '-text', '-noout', '-in', self.path]
        rc, out, err = module.run_command(command, check_rc=False)
        result = to_native(out)
        if rc != 0:
            # If the call failed the file probably doesn't exist or is
            # unreadable
            return False
        # output contains "(xxxx bit)"
        match = re.search(r"Parameters:\s+\((\d+) bit\).*", result)
        if not match:
            return False  # No "xxxx bit" in output

        bits = int(match.group(1))

        # if output contains "WARNING" we've got a problem
        if "WARNING" in result or "WARNING" in to_native(err):
            return False

        return bits == self.size

    def _check_fs_attributes(self, module):
        """Checks (and changes if not in check mode!) fs attributes"""
        file_args = module.load_file_common_arguments(module.params)
        attrs_changed = module.set_fs_attributes_if_different(file_args, False)

        return not attrs_changed

    def dump(self):
        """Serialize the object into a dictionary."""

        result = {
            'size': self.size,
            'filename': self.path,
            'changed': self.changed,
        }
        if self.backup_file:
            result['backup_file'] = self.backup_file

        return result


def main():
    """Main function"""

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['absent', 'present']),
            size=dict(type='int', default=4096),
            force=dict(type='bool', default=False),
            path=dict(type='path', required=True),
            backup=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
        add_file_common_args=True,
    )

    base_dir = os.path.dirname(module.params['path']) or '.'
    if not os.path.isdir(base_dir):
        module.fail_json(
            name=base_dir,
            msg="The directory '%s' does not exist or the file is not a directory" % base_dir
        )

    dhparam = DHParameter(module)

    if dhparam.state == 'present':

        if module.check_mode:
            result = dhparam.dump()
            result['changed'] = module.params['force'] or not dhparam.check(module)
            module.exit_json(**result)

        try:
            dhparam.generate(module)
        except DHParameterError as exc:
            module.fail_json(msg=to_native(exc))
    else:

        if module.check_mode:
            result = dhparam.dump()
            result['changed'] = os.path.exists(module.params['path'])
            module.exit_json(**result)

        if os.path.exists(module.params['path']):
            try:
                dhparam.remove(module)
            except Exception as exc:
                module.fail_json(msg=to_native(exc))

    result = dhparam.dump()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
