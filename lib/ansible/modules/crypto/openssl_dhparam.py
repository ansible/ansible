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
    - The module can use the cryptography Python library, or the C(openssl) executable.
      By default, it tries to detect which one is available. This can be overridden
      with the I(select_crypto_backend) option.
requirements:
    - Either cryptography >= 2.0
    - Or OpenSSL binary C(openssl)
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
    select_crypto_backend:
        description:
            - Determines which crypto backend to use.
            - The default choice is C(auto), which tries to use C(cryptography) if available, and falls back to C(openssl).
            - If set to C(openssl), will try to use the OpenSSL C(openssl) executable.
            - If set to C(cryptography), will try to use the L(cryptography,https://cryptography.io/) library.
        type: str
        default: auto
        choices: [ auto, cryptography, openssl ]
        version_added: '2.10'
    return_content:
        description:
            - If set to C(yes), will return the (current or generated) DH params' content as I(dhparams).
        type: bool
        default: no
        version_added: "2.10"
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
dhparams:
    description: The (current or generated) DH params' content.
    returned: if I(state) is C(present) and I(return_content) is C(yes)
    type: str
    version_added: "2.10"
'''

import abc
import os
import re
import tempfile
import traceback
from distutils.version import LooseVersion

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native
from ansible.module_utils import crypto as crypto_utils


MINIMAL_CRYPTOGRAPHY_VERSION = '2.0'

CRYPTOGRAPHY_IMP_ERR = None
try:
    import cryptography
    import cryptography.exceptions
    import cryptography.hazmat.backends
    import cryptography.hazmat.primitives.asymmetric.dh
    import cryptography.hazmat.primitives.serialization
    CRYPTOGRAPHY_VERSION = LooseVersion(cryptography.__version__)
except ImportError:
    CRYPTOGRAPHY_IMP_ERR = traceback.format_exc()
    CRYPTOGRAPHY_FOUND = False
else:
    CRYPTOGRAPHY_FOUND = True


class DHParameterError(Exception):
    pass


class DHParameterBase(object):

    def __init__(self, module):
        self.state = module.params['state']
        self.path = module.params['path']
        self.size = module.params['size']
        self.force = module.params['force']
        self.changed = False
        self.return_content = module.params['return_content']

        self.backup = module.params['backup']
        self.backup_file = None

    @abc.abstractmethod
    def _do_generate(self, module):
        """Actually generate the DH params."""
        pass

    def generate(self, module):
        """Generate DH params."""
        changed = False

        # ony generate when necessary
        if self.force or not self._check_params_valid(module):
            self._do_generate(module)
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

    @abc.abstractmethod
    def _check_params_valid(self, module):
        """Check if the params are in the correct state"""
        pass

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
        if self.return_content:
            content = crypto_utils.load_file_if_exists(self.path, ignore_errors=True)
            result['dhparams'] = content.decode('utf-8') if content else None

        return result


class DHParameterAbsent(DHParameterBase):

    def __init__(self, module):
        super(DHParameterAbsent, self).__init__(module)

    def _do_generate(self, module):
        """Actually generate the DH params."""
        pass

    def _check_params_valid(self, module):
        """Check if the params are in the correct state"""
        pass


class DHParameterOpenSSL(DHParameterBase):

    def __init__(self, module):
        super(DHParameterOpenSSL, self).__init__(module)
        self.openssl_bin = module.get_bin_path('openssl', True)

    def _do_generate(self, module):
        """Actually generate the DH params."""
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


class DHParameterCryptography(DHParameterBase):

    def __init__(self, module):
        super(DHParameterCryptography, self).__init__(module)
        self.crypto_backend = cryptography.hazmat.backends.default_backend()

    def _do_generate(self, module):
        """Actually generate the DH params."""
        # Generate parameters
        params = cryptography.hazmat.primitives.asymmetric.dh.generate_parameters(
            generator=2,
            key_size=self.size,
            backend=self.crypto_backend,
        )
        # Serialize parameters
        result = params.parameter_bytes(
            encoding=cryptography.hazmat.primitives.serialization.Encoding.PEM,
            format=cryptography.hazmat.primitives.serialization.ParameterFormat.PKCS3,
        )
        # Write result
        if self.backup:
            self.backup_file = module.backup_local(self.path)
        crypto_utils.write_file(module, result)

    def _check_params_valid(self, module):
        """Check if the params are in the correct state"""
        # Load parameters
        try:
            with open(self.path, 'rb') as f:
                data = f.read()
            params = self.crypto_backend.load_pem_parameters(data)
        except Exception as dummy:
            return False
        # Check parameters
        bits = crypto_utils.count_bits(params.parameter_numbers().p)
        return bits == self.size


def main():
    """Main function"""

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['absent', 'present']),
            size=dict(type='int', default=4096),
            force=dict(type='bool', default=False),
            path=dict(type='path', required=True),
            backup=dict(type='bool', default=False),
            select_crypto_backend=dict(type='str', default='auto', choices=['auto', 'cryptography', 'openssl']),
            return_content=dict(type='bool', default=False),
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

    if module.params['state'] == 'present':
        backend = module.params['select_crypto_backend']
        if backend == 'auto':
            # Detection what is possible
            can_use_cryptography = CRYPTOGRAPHY_FOUND and CRYPTOGRAPHY_VERSION >= LooseVersion(MINIMAL_CRYPTOGRAPHY_VERSION)
            can_use_openssl = module.get_bin_path('openssl', False) is not None

            # First try cryptography, then OpenSSL
            if can_use_cryptography:
                backend = 'cryptography'
            elif can_use_openssl:
                backend = 'openssl'

            # Success?
            if backend == 'auto':
                module.fail_json(msg=("Can't detect either the required Python library cryptography (>= {0}) "
                                      "or the OpenSSL binary openssl").format(MINIMAL_CRYPTOGRAPHY_VERSION))

        if backend == 'openssl':
            dhparam = DHParameterOpenSSL(module)
        elif backend == 'cryptography':
            if not CRYPTOGRAPHY_FOUND:
                module.fail_json(msg=missing_required_lib('cryptography >= {0}'.format(MINIMAL_CRYPTOGRAPHY_VERSION)),
                                 exception=CRYPTOGRAPHY_IMP_ERR)
            dhparam = DHParameterCryptography(module)

        if module.check_mode:
            result = dhparam.dump()
            result['changed'] = module.params['force'] or not dhparam.check(module)
            module.exit_json(**result)

        try:
            dhparam.generate(module)
        except DHParameterError as exc:
            module.fail_json(msg=to_native(exc))
    else:
        dhparam = DHParameterAbsent(module)

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
