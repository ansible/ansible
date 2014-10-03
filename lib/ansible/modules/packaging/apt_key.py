#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2012, Jayson Vantuyl <jayson@aggressive.ly>
#
# This file is part of Ansible
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

DOCUMENTATION = '''
---
module: apt_key
author: Jayson Vantuyl & others
version_added: "1.0"
short_description: Add or remove an apt key
description:
    - Add or remove an I(apt) key, optionally downloading it
notes:
    - doesn't download the key unless it really needs it
    - as a sanity check, downloaded key id must match the one specified
    - best practice is to specify the key id and the url
options:
    id:
        required: false
        default: none
        description:
            - identifier of key
    data:
        required: false
        default: none
        description:
            - keyfile contents
    file:
        required: false
        default: none
        description:
            - keyfile path
    keyring:
        required: false
        default: none
        description:
            - path to specific keyring file in /etc/apt/trusted.gpg.d
        version_added: "1.3"
    url:
        required: false
        default: none
        description:
            - url to retrieve key from.
    keyserver:
        version_added: "1.6"
        required: false
        default: none
        description:
            - keyserver to retrieve key from.
    state:
        required: false
        choices: [ absent, present ]
        default: present
        description:
            - used to specify if key is being added or revoked
    validate_certs:
        description:
            - If C(no), SSL certificates for the target url will not be validated. This should only be used
              on personally controlled sites using self-signed certificates.
        required: false
        default: 'yes'
        choices: ['yes', 'no']

'''

EXAMPLES = '''
# Add an apt key by id from a keyserver
- apt_key: keyserver=keyserver.ubuntu.com id=36A1D7869245C8950F966E92D8576A8BA88D21E9

# Add an Apt signing key, uses whichever key is at the URL
- apt_key: url=https://ftp-master.debian.org/keys/archive-key-6.0.asc state=present

# Add an Apt signing key, will not download if present
- apt_key: id=473041FA url=https://ftp-master.debian.org/keys/archive-key-6.0.asc state=present

# Remove an Apt signing key, uses whichever key is at the URL
- apt_key: url=https://ftp-master.debian.org/keys/archive-key-6.0.asc state=absent

# Remove a Apt specific signing key, leading 0x is valid
- apt_key: id=0x473041FA state=absent

# Add a key from a file on the Ansible server
- apt_key: data="{{ lookup('file', 'apt.gpg') }}" state=present

# Add an Apt signing key to a specific keyring file
- apt_key: id=473041FA url=https://ftp-master.debian.org/keys/archive-key-6.0.asc keyring=/etc/apt/trusted.gpg.d/debian.gpg state=present
'''


# FIXME: standardize into module_common
from traceback import format_exc
from re import compile as re_compile
# FIXME: standardize into module_common
from distutils.spawn import find_executable
from os import environ
from sys import exc_info
import traceback

match_key = re_compile("^gpg:.*key ([0-9a-fA-F]+):.*$")

REQUIRED_EXECUTABLES=['gpg', 'grep', 'apt-key']


def check_missing_binaries(module):
    missing = [e for e in REQUIRED_EXECUTABLES if not find_executable(e)]
    if len(missing):
        module.fail_json(msg="binaries are missing", names=missing)

def all_keys(module, keyring, short_format):
    if keyring:
        cmd = "apt-key --keyring %s adv --list-public-keys --keyid-format=long" % keyring
    else:
        cmd = "apt-key adv --list-public-keys --keyid-format=long"
    (rc, out, err) = module.run_command(cmd)
    results = []
    lines = out.split('\n')
    for line in lines:
        if line.startswith("pub"):
            tokens = line.split()
            code = tokens[1]
            (len_type, real_code) = code.split("/")
            results.append(real_code)
    if short_format:
        results = shorten_key_ids(results)
    return results

def shorten_key_ids(key_id_list):
    """
    Takes a list of key ids, and converts them to the 'short' format,
    by reducing them to their last 8 characters.
    """
    short = []
    for key in key_id_list:
        short.append(key[-8:])
    return short

def download_key(module, url):
    # FIXME: move get_url code to common, allow for in-memory D/L, support proxies
    # and reuse here
    if url is None:
        module.fail_json(msg="needed a URL but was not specified")

    try:
        rsp, info = fetch_url(module, url)
        if info['status'] != 200:
            module.fail_json(msg="Failed to download key at %s: %s" % (url, info['msg']))

        return rsp.read()
    except Exception:
        module.fail_json(msg="error getting key id from url: %s" % url, traceback=format_exc())

def import_key(module, keyserver, key_id):
    cmd = "apt-key adv --keyserver %s --recv %s" % (keyserver, key_id)
    (rc, out, err) = module.run_command(cmd, check_rc=True)
    return True

def add_key(module, keyfile, keyring, data=None):
    if data is not None:
        if keyring:
            cmd = "apt-key --keyring %s add -" % keyring
        else:
            cmd = "apt-key add -"
        (rc, out, err) = module.run_command(cmd, data=data, check_rc=True, binary_data=True)
    else:
        if keyring:
            cmd = "apt-key --keyring %s add %s" % (keyring, keyfile)
        else:
            cmd = "apt-key add %s" % (keyfile)
        (rc, out, err) = module.run_command(cmd, check_rc=True)
    return True

def remove_key(module, key_id, keyring):
    # FIXME: use module.run_command, fail at point of error and don't discard useful stdin/stdout
    if keyring:
        cmd = 'apt-key --keyring %s del %s' % (keyring, key_id)
    else:
        cmd = 'apt-key del %s' % key_id
    (rc, out, err) = module.run_command(cmd, check_rc=True)
    return True

def main():
    module = AnsibleModule(
        argument_spec=dict(
            id=dict(required=False, default=None),
            url=dict(required=False),
            data=dict(required=False),
            file=dict(required=False),
            key=dict(required=False),
            keyring=dict(required=False),
            validate_certs=dict(default='yes', type='bool'),
            keyserver=dict(required=False),
            state=dict(required=False, choices=['present', 'absent'], default='present')
        ),
        supports_check_mode=True
    )

    key_id          = module.params['id']
    url             = module.params['url']
    data            = module.params['data']
    filename        = module.params['file']
    keyring         = module.params['keyring']
    state           = module.params['state']
    keyserver       = module.params['keyserver']
    changed         = False

    if key_id:
        try:
            _ = int(key_id, 16)
            if key_id.startswith('0x'):
                key_id = key_id[2:]
            key_id = key_id.upper()
        except ValueError:
            module.fail_json(msg="Invalid key_id", id=key_id)

    # FIXME: I think we have a common facility for this, if not, want
    check_missing_binaries(module)

    short_format = (key_id is not None and len(key_id) == 8)
    keys = all_keys(module, keyring, short_format)
    return_values = {}

    if state == 'present':
        if key_id and key_id in keys:
            module.exit_json(changed=False)
        else:
            if not filename and not data and not keyserver:
                data = download_key(module, url)
            if key_id and key_id in keys:
                module.exit_json(changed=False)
            else:
                if module.check_mode:
                    module.exit_json(changed=True)
                if filename:
                    add_key(module, filename, keyring)
                elif keyserver:
                    import_key(module, keyserver, key_id)
                else:
                    add_key(module, "-", keyring, data)
                changed=False
                keys2 = all_keys(module, keyring, short_format)
                if len(keys) != len(keys2):
                    changed=True
                if key_id and not key_id[-16:] in keys2:
                    module.fail_json(msg="key does not seem to have been added", id=key_id)
                module.exit_json(changed=changed)
    elif state == 'absent':
        if not key_id:
            module.fail_json(msg="key is required")
        if key_id in keys:
            if module.check_mode:
                module.exit_json(changed=True)
            if remove_key(module, key_id, keyring):
                changed=True
            else:
                # FIXME: module.fail_json  or exit-json immediately at point of failure
                module.fail_json(msg="error removing key_id", **return_values)

    module.exit_json(changed=changed, **return_values)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
main()
