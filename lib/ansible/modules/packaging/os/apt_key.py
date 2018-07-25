#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2012, Jayson Vantuyl <jayson@aggressive.ly>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = '''
---
module: apt_key
author:
- Jayson Vantuyl (@jvantuyl)
version_added: "1.0"
short_description: Add or remove an apt key
description:
    - Add or remove an I(apt) key, optionally downloading it.
notes:
    - Doesn't download the key unless it really needs it.
    - As a sanity check, downloaded key id must match the one specified.
    - Best practice is to specify the key id and the URL.
options:
    id:
        description:
            - The identifier of the key.
            - Including this allows check mode to correctly report the changed state.
            - If specifying a subkey's id be aware that apt-key does not understand how to remove keys via a subkey id.  Specify the primary key's id instead.
            - This parameter is required when C(state) is set to C(absent).
    data:
        description:
            - The keyfile contents to add to the keyring.
    file:
        description:
            - The path to a keyfile on the remote server to add to the keyring.
    keyring:
        description:
            - The full path to specific keyring file in /etc/apt/trusted.gpg.d/
        version_added: "1.3"
    url:
        description:
            - The URL to retrieve key from.
    keyserver:
        description:
            - The keyserver to retrieve key from.
        version_added: "1.6"
    state:
        description:
            - Ensures that the key is present (added) or absent (revoked).
        choices: [ absent, present ]
        default: present
    validate_certs:
        description:
            - If C(no), SSL certificates for the target url will not be validated. This should only be used
              on personally controlled sites using self-signed certificates.
        type: bool
        default: 'yes'
'''

EXAMPLES = '''
- name: Add an apt key by id from a keyserver
  apt_key:
    keyserver: keyserver.ubuntu.com
    id: 36A1D7869245C8950F966E92D8576A8BA88D21E9

- name: Add an Apt signing key, uses whichever key is at the URL
  apt_key:
    url: https://ftp-master.debian.org/keys/archive-key-6.0.asc
    state: present

- name: Add an Apt signing key, will not download if present
  apt_key:
    id: 473041FA
    url: https://ftp-master.debian.org/keys/archive-key-6.0.asc
    state: present

- name: Remove a Apt specific signing key, leading 0x is valid
  apt_key:
    id: 0x473041FA
    state: absent

# Use armored file since utf-8 string is expected. Must be of "PGP PUBLIC KEY BLOCK" type.
- name: Add a key from a file on the Ansible server.
  apt_key:
    data: "{{ lookup('file', 'apt.asc') }}"
    state: present

- name: Add an Apt signing key to a specific keyring file
  apt_key:
    id: 473041FA
    url: https://ftp-master.debian.org/keys/archive-key-6.0.asc
    keyring: /etc/apt/trusted.gpg.d/debian.gpg

- name: Add Apt signing key on remote server to keyring
  apt_key:
    id: 473041FA
    file: /tmp/apt.gpg
    state: present
'''


# FIXME: standardize into module_common
from traceback import format_exc

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url


apt_key_bin = None


def find_needed_binaries(module):
    global apt_key_bin

    apt_key_bin = module.get_bin_path('apt-key', required=True)

    # FIXME: Is there a reason that gpg and grep are checked?  Is it just
    # cruft or does the apt .deb package not require them (and if they're not
    # installed, /usr/bin/apt-key fails?)
    module.get_bin_path('gpg', required=True)
    module.get_bin_path('grep', required=True)


def parse_key_id(key_id):
    """validate the key_id and break it into segments

    :arg key_id: The key_id as supplied by the user.  A valid key_id will be
        8, 16, or more hexadecimal chars with an optional leading ``0x``.
    :returns: The portion of key_id suitable for apt-key del, the portion
        suitable for comparisons with --list-public-keys, and the portion that
        can be used with --recv-key.  If key_id is long enough, these will be
        the last 8 characters of key_id, the last 16 characters, and all of
        key_id.  If key_id is not long enough, some of the values will be the
        same.

    * apt-key del <= 1.10 has a bug with key_id != 8 chars
    * apt-key adv --list-public-keys prints 16 chars
    * apt-key adv --recv-key can take more chars

    """
    # Make sure the key_id is valid hexadecimal
    int(key_id, 16)

    key_id = key_id.upper()
    if key_id.startswith('0X'):
        key_id = key_id[2:]

    key_id_len = len(key_id)
    if (key_id_len != 8 and key_id_len != 16) and key_id_len <= 16:
        raise ValueError('key_id must be 8, 16, or 16+ hexadecimal characters in length')

    short_key_id = key_id[-8:]

    fingerprint = key_id
    if key_id_len > 16:
        fingerprint = key_id[-16:]

    return short_key_id, fingerprint, key_id


def all_keys(module, keyring, short_format):
    if keyring:
        cmd = "%s --keyring %s adv --list-public-keys --keyid-format=long" % (apt_key_bin, keyring)
    else:
        cmd = "%s adv --list-public-keys --keyid-format=long" % apt_key_bin
    (rc, out, err) = module.run_command(cmd)
    results = []
    lines = to_native(out).split('\n')
    for line in lines:
        if (line.startswith("pub") or line.startswith("sub")) and "expired" not in line:
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


def import_key(module, keyring, keyserver, key_id):
    if keyring:
        cmd = "%s --keyring %s adv --keyserver %s --recv %s" % (apt_key_bin, keyring, keyserver, key_id)
    else:
        cmd = "%s adv --keyserver %s --recv %s" % (apt_key_bin, keyserver, key_id)
    for retry in range(5):
        lang_env = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')
        (rc, out, err) = module.run_command(cmd, environ_update=lang_env)
        if rc == 0:
            break
    else:
        # Out of retries
        if rc == 2 and 'not found on keyserver' in out:
            msg = 'Key %s not found on keyserver %s' % (key_id, keyserver)
            module.fail_json(cmd=cmd, msg=msg)
        else:
            msg = "Error fetching key %s from keyserver: %s" % (key_id, keyserver)
            module.fail_json(cmd=cmd, msg=msg, rc=rc, stdout=out, stderr=err)
    return True


def add_key(module, keyfile, keyring, data=None):
    if data is not None:
        if keyring:
            cmd = "%s --keyring %s add -" % (apt_key_bin, keyring)
        else:
            cmd = "%s add -" % apt_key_bin
        (rc, out, err) = module.run_command(cmd, data=data, check_rc=True, binary_data=True)
    else:
        if keyring:
            cmd = "%s --keyring %s add %s" % (apt_key_bin, keyring, keyfile)
        else:
            cmd = "%s add %s" % (apt_key_bin, keyfile)
        (rc, out, err) = module.run_command(cmd, check_rc=True)
    return True


def remove_key(module, key_id, keyring):
    # FIXME: use module.run_command, fail at point of error and don't discard useful stdin/stdout
    if keyring:
        cmd = '%s --keyring %s del %s' % (apt_key_bin, keyring, key_id)
    else:
        cmd = '%s del %s' % (apt_key_bin, key_id)
    (rc, out, err) = module.run_command(cmd, check_rc=True)
    return True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            id=dict(type='str'),
            url=dict(type='str'),
            data=dict(type='str'),
            file=dict(type='path'),
            key=dict(type='str'),
            keyring=dict(type='path'),
            validate_certs=dict(type='bool', default=True),
            keyserver=dict(type='str'),
            state=dict(type='str', default='present', choices=['absent', 'present']),
        ),
        supports_check_mode=True,
        mutually_exclusive=(('data', 'filename', 'keyserver', 'url'),),
    )

    key_id = module.params['id']
    url = module.params['url']
    data = module.params['data']
    filename = module.params['file']
    keyring = module.params['keyring']
    state = module.params['state']
    keyserver = module.params['keyserver']
    changed = False

    fingerprint = short_key_id = key_id
    short_format = False
    if key_id:
        try:
            short_key_id, fingerprint, key_id = parse_key_id(key_id)
        except ValueError:
            module.fail_json(msg='Invalid key_id', id=key_id)

        if len(fingerprint) == 8:
            short_format = True

    find_needed_binaries(module)

    keys = all_keys(module, keyring, short_format)
    return_values = {}

    if state == 'present':
        if fingerprint and fingerprint in keys:
            module.exit_json(changed=False)
        elif fingerprint and fingerprint not in keys and module.check_mode:
            # TODO: Someday we could go further -- write keys out to
            # a temporary file and then extract the key id from there via gpg
            # to decide if the key is installed or not.
            module.exit_json(changed=True)
        else:
            if not filename and not data and not keyserver:
                data = download_key(module, url)

            if filename:
                add_key(module, filename, keyring)
            elif keyserver:
                import_key(module, keyring, keyserver, key_id)
            else:
                add_key(module, "-", keyring, data)

            changed = False
            keys2 = all_keys(module, keyring, short_format)
            if len(keys) != len(keys2):
                changed = True

            if fingerprint and fingerprint not in keys2:
                module.fail_json(msg="key does not seem to have been added", id=key_id)
            module.exit_json(changed=changed)

    elif state == 'absent':
        if not key_id:
            module.fail_json(msg="key is required")
        if fingerprint in keys:
            if module.check_mode:
                module.exit_json(changed=True)

            # we use the "short" id: key_id[-8:], short_format=True
            # it's a workaround for https://bugs.launchpad.net/ubuntu/+source/apt/+bug/1481871
            if remove_key(module, short_key_id, keyring):
                keys = all_keys(module, keyring, short_format)
                if fingerprint in keys:
                    module.fail_json(msg="apt-key del did not return an error but the key was not removed (check that the id is correct and *not* a subkey)",
                                     id=key_id)
                changed = True
            else:
                # FIXME: module.fail_json or exit-json immediately at point of failure
                module.fail_json(msg="error removing key_id", **return_values)

    module.exit_json(changed=changed, **return_values)


if __name__ == '__main__':
    main()
