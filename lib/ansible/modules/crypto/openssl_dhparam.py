#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Thom Wiggers  <ansible@thomwiggers.nl>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: openssl_dhparam
author: "Thom Wiggers (@thomwiggers)"
version_added: "2.5"
short_description: Generate OpenSSL Diffie-Hellman Parameters
description:
    - "This module allows one to (re)generate OpenSSL DH-params.
      This module uses file common arguments to specify generated file permissions."
requirements:
    - OpenSSL
options:
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the parameters should exist or not,
              taking action if the state is different from what is stated.
    size:
        required: false
        default: 4096
        description:
            - Size (in bits) of the generated DH-params
    force:
        required: false
        default: False
        choices: [ True, False ]
        description:
            - Should the parameters be regenerated even it it already exists
    path:
        required: true
        description:
            - Name of the file in which the generated parameters will be saved.
extends_documentation_fragment: files
'''

EXAMPLES = '''
# Generate Diffie-Hellman parameters with the default size (4096 bits)
- openssl_dhparam:
    path: /etc/ssl/dhparams.pem

# Generate DH Parameters with a different size (2048 bits)
- openssl_dhparam:
    path: /etc/ssl/dhparams.pem
    size: 2048

# Force regenerate an DH parameters if they already exist
- openssl_dhparam:
    path: /etc/ssl/dhparams.pem
    force: True

'''

RETURN = '''
size:
    description: Size (in bits) of the Diffie-Hellman parameters
    returned: changed or success
    type: int
    sample: 4096
filename:
    description: Path to the generated Diffie-Hellman parameters
    returned: changed or success
    type: string
    sample: /etc/ssl/dhparams.pem
'''

import os
import re

"""Note: We also monkey-patch subprocess for python 2.6 to
give feature parity with later versions.
Monkey-patch from http://pydoc.net/pep8radius/0.9.0/ with slight modifications
MIT Licence

Remove patch when Python 2.6 is no longer supported
"""
import subprocess
try:
    from subprocess import check_output, CalledProcessError
except ImportError:  # pragma: no cover
    # python 2.6 doesn't include check_output
    # monkey patch it in!
    def check_output(*popenargs, **kwargs):
        if 'stdout' in kwargs:  # pragma: no cover
            raise ValueError('stdout argument not allowed, '
                             'it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE,
                                   *popenargs, **kwargs)
        output = process.communicate()[0]
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise CalledProcessError(retcode, cmd, output=output)
        return output

    # overwrite CalledProcessError due to `output`
    # keyword not being available (in 2.6)
    class CalledProcessError(Exception):
        """Exception raised for call errors"""

        def __init__(self, returncode, cmd, output=None):
            self.returncode = returncode
            self.cmd = cmd
            self.output = output

        def __str__(self):
            return "Command '%s' returned non-zero exit status %d" % (
                self.cmd, self.returncode)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


class DHParameterError(Exception):
    pass


class DHParameter(object):

    def __init__(self, module):
        self.state = module.params['state']
        self.path = module.params['path']
        self.size = int(module.params['size'])
        self.force = module.params['force']
        self.changed = False

    def generate(self, module):
        """Generate a keypair."""
        changed = False

        # ony generate when necessary
        if self.force or not self._check_params_valid(module):
            try:
                # openssl dhparam -out <path> <bits>
                subprocess.check_call(
                    ["openssl", "dhparam", "-out", self.path, str(self.size)])
            except CalledProcessError as exc:
                os.remove(self.path)
                raise DHParameterError(str(exc))
            finally:
                changed = True

        # fix permissions (checking force not necessary as done above)
        if not self._check_fs_attributes(module):
            # Fix done implicitly by
            # AnsibleModule.set_fs_attributes_if_different
            changed = True

        self.changed = changed

    def check(self, module):
        """Ensure the resource is in its desired state."""
        if self.force:
            return False
        return self._check_params_valid(module) and self._check_fs_attributes(module)

    def _check_params_valid(self, module):
        """Check if the params are in the correct state"""
        try:
            result = to_native(check_output(
                ["openssl", "dhparam", "-check", "-text", "-noout", "-in", self.path],
                stderr=subprocess.STDOUT,
            )).strip()
        except CalledProcessError as e:
            # If the call failed the file probably doesn't exist or is
            # unreadable
            return False
        # output contains "(xxxx bit)"
        match = re.search(r"Parameters:\s+\((\d+) bit\).*", result)
        if not match:
            return False  # No "xxxx bit" in output
        else:
            bits = int(match.group(1))

        # if output contains "WARNING" we've got a problem
        if "WARNING" in result:
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
        return result


def main():
    """Main function"""

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            size=dict(default=4096, type='int'),
            force=dict(default=False, type='bool'),
            path=dict(required=True, type='path'),
        ),
        supports_check_mode=True,
        add_file_common_args=True,
    )

    base_dir = os.path.dirname(module.params['path'])
    if not os.path.isdir(base_dir):
        module.fail_json(
            name=base_dir,
            msg='The directory %s does not exist or the file is not a directory' % base_dir
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

        try:
            os.remove(module.params['path'])
        except OSError as exc:
            module.fail_json(msg=to_native(exc))

    result = dhparam.dump()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
