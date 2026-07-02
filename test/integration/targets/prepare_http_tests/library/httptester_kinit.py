#!/usr/bin/python

# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = r"""
---
module: httptester_kinit
short_description: Get Kerberos ticket
description: Get Kerberos ticket using kinit non-interactively.
options:
  username:
    description: The username to get the ticket for.
    required: true
    type: str
  password:
    description: The password for I(username).
    required; true
    type: str
author:
- Ansible Project
"""

EXAMPLES = r"""
#
"""

RETURN = r"""
#
"""

import contextlib
import os
import subprocess

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_bytes, to_text

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


@contextlib.contextmanager
def env_path(name, value, default_value):
    """ Adds a value to a PATH-like env var and preserve the existing value if present. """
    orig_value = os.environ.get(name, None)
    os.environ[name] = '%s:%s' % (value, orig_value or default_value)
    try:
        yield

    finally:
        if orig_value:
            os.environ[name] = orig_value

        else:
            del os.environ[name]


@contextlib.contextmanager
def krb5_conf(module, config):
    """ Runs with a custom krb5.conf file that extends the existing config if present. """
    if config:
        ini_config = configparser.ConfigParser()
        for section, entries in config.items():
            ini_config.add_section(section)
            for key, value in entries.items():
                ini_config.set(section, key, value)

        config_path = os.path.join(module.tmpdir, 'krb5.conf')
        with open(config_path, mode='wt') as config_fd:
            ini_config.write(config_fd)

        with env_path('KRB5_CONFIG', config_path, '/etc/krb5.conf'):
            yield

    else:
        yield


def main():
    module_args = dict(
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
    )
    module = AnsibleModule(
        argument_spec=module_args,
        required_together=[('username', 'password')],
    )

    # Heimdal has a few quirks that we want to paper over in this module
    #     1. KRB5_TRACE does not work in any released version (<=7.7), we need to use a custom krb5.config to enable it
    #     2. When reading the password it reads from the pty not stdin by default causing an issue with subprocess. We
    #        can control that behaviour with '--password-file=STDIN'
    # Also need to set the custom path to krb5-config and kinit as FreeBSD relies on the newer Heimdal version in the
    # port package.
    sysname = os.uname()[0]
    prefix = '/usr/local/bin/' if sysname == 'FreeBSD' else ''
    is_heimdal = sysname in ['Darwin', 'FreeBSD']

    # Debugging purposes, get the Kerberos version. On platforms like OpenSUSE this may not be on the PATH.
    try:
        process = subprocess.Popen(['%skrb5-config' % prefix, '--version'], stdout=subprocess.PIPE)
        stdout, stderr = process.communicate()
        version = to_text(stdout)
    except FileNotFoundError:
        version = 'Unknown (no krb5-config)'

    kinit_args = ['%skinit' % prefix]
    config = {}
    if is_heimdal:
        kinit_args.append('--password-file=STDIN')
        config['logging'] = {'krb5': 'FILE:/dev/stdout'}
    kinit_args.append(to_text(module.params['username'], errors='surrogate_or_strict'))

    with krb5_conf(module, config):
        # Weirdly setting KRB5_CONFIG in the modules environment block does not work unless we pass it in explicitly.
        # Take a copy of the existing environment to make sure the process has the same env vars as ours. Also set
        # KRB5_TRACE to output and debug logs helping to identify problems when calling kinit with MIT.
        kinit_env = os.environ.copy()
        kinit_env['KRB5_TRACE'] = '/dev/stdout'

        process = subprocess.Popen(kinit_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   env=kinit_env)
        stdout, stderr = process.communicate(to_bytes(module.params['password'], errors='surrogate_or_strict') + b'\n')
        rc = process.returncode

    module.exit_json(changed=True, stdout=to_text(stdout), stderr=to_text(stderr), rc=rc, version=version)


if __name__ == '__main__':
    main()
