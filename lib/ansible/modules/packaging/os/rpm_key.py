#!/usr/bin/python
# -*- coding: utf-8 -*-

# Ansible module to import third party repo keys to your rpm db
# (c) 2013, Héctor Acosta <hector.acosta@gazzang.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: rpm_key
author: "Hector Acosta (@hacosta) <hector.acosta@gazzang.com>"
short_description: Adds or removes a gpg key from the rpm db
description:
    - Adds or removes (rpm --import) a gpg key to your rpm database.
version_added: "1.3"
options:
    key:
      required: true
      default: null
      aliases: []
      description:
          - Key that will be modified. Can be a url, a file, or a keyid if the key already exists in the database.
    state:
      required: false
      default: "present"
      choices: [present, absent]
      description:
          - If the key will be imported or removed from the rpm db.
    validate_certs:
      description:
          - If C(no) and the C(key) is a url starting with https, SSL certificates will not be validated. This should only be used
            on personally controlled sites using self-signed certificates.
      required: false
      default: 'yes'
      choices: ['yes', 'no']

'''

EXAMPLES = '''
# Example action to import a key from a url
- rpm_key:
    state: present
    key: http://apt.sw.be/RPM-GPG-KEY.dag.txt

# Example action to import a key from a file
- rpm_key:
    state: present
    key: /path/to/key.gpg

# Example action to ensure a key is not present in the db
- rpm_key:
    state: absent
    key: DEADB33F
'''
import re
import os.path
import tempfile

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native


def is_pubkey(string):
    """Verifies if string is a pubkey"""
    pgp_regex = ".*?(-----BEGIN PGP PUBLIC KEY BLOCK-----.*?-----END PGP PUBLIC KEY BLOCK-----).*"
    return bool(re.match(pgp_regex, to_native(string, errors='surrogate_or_strict'), re.DOTALL))


class RpmKey(object):

    def __init__(self, module):
        # If the key is a url, we need to check if it's present to be idempotent,
        # to do that, we need to check the keyid, which we can get from the armor.
        keyfile = None
        should_cleanup_keyfile = False
        self.module = module
        self.rpm = self.module.get_bin_path('rpm', True)
        state = module.params['state']
        key = module.params['key']

        if '://' in key:
            keyfile = self.fetch_key(key)
            keyid = self.getkeyid(keyfile)
            should_cleanup_keyfile = True
        elif self.is_keyid(key):
            keyid = key
        elif os.path.isfile(key):
            keyfile = key
            keyid = self.getkeyid(keyfile)
        else:
            self.module.fail_json(msg="Not a valid key %s" % key)
        keyid = self.normalize_keyid(keyid)

        if state == 'present':
            if self.is_key_imported(keyid):
                module.exit_json(changed=False)
            else:
                if not keyfile:
                    self.module.fail_json(msg="When importing a key, a valid file must be given")
                self.import_key(keyfile, dryrun=module.check_mode)
                if should_cleanup_keyfile:
                    self.module.cleanup(keyfile)
                module.exit_json(changed=True)
        else:
            if self.is_key_imported(keyid):
                self.drop_key(keyid, dryrun=module.check_mode)
                module.exit_json(changed=True)
            else:
                module.exit_json(changed=False)

    def fetch_key(self, url):
        """Downloads a key from url, returns a valid path to a gpg key"""
        rsp, info = fetch_url(self.module, url)
        if info['status'] != 200:
            self.module.fail_json(msg="failed to fetch key at %s , error was: %s" % (url, info['msg']))

        key = rsp.read()
        if not is_pubkey(key):
            self.module.fail_json(msg="Not a public key: %s" % url)
        tmpfd, tmpname = tempfile.mkstemp()
        tmpfile = os.fdopen(tmpfd, "w+b")
        tmpfile.write(key)
        tmpfile.close()
        return tmpname

    def normalize_keyid(self, keyid):
        """Ensure a keyid doesn't have a leading 0x, has leading or trailing whitespace, and make sure is lowercase"""
        ret = keyid.strip().lower()
        if ret.startswith('0x'):
            return ret[2:]
        elif ret.startswith('0X'):
            return ret[2:]
        else:
            return ret

    def getkeyid(self, keyfile):

        gpg = self.module.get_bin_path('gpg')
        if not gpg:
            gpg = self.module.get_bin_path('gpg2')

        if not gpg:
            self.module.fail_json(msg="rpm_key requires a command line gpg or gpg2, none found")

        stdout, stderr = self.execute_command([gpg, '--no-tty', '--batch', '--with-colons', '--fixed-list-mode', '--list-packets', keyfile])
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith(':signature packet:'):
                # We want just the last 8 characters of the keyid
                keyid = line.split()[-1].strip()[8:]
                return keyid
        self.module.fail_json(msg="Unexpected gpg output")

    def is_keyid(self, keystr):
        """Verifies if a key, as provided by the user is a keyid"""
        return re.match('(0x)?[0-9a-f]{8}', keystr, flags=re.IGNORECASE)

    def execute_command(self, cmd):
        rc, stdout, stderr = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg=stderr)
        return stdout, stderr

    def is_key_imported(self, keyid):
        stdout, stderr = self.execute_command([self.rpm, '-qa', 'gpg-pubkey'])
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            match = re.match('gpg-pubkey-([0-9a-f]+)-([0-9a-f]+)', line)
            if not match:
                self.module.fail_json(msg="rpm returned unexpected output [%s]" % line)
            else:
                if keyid == match.group(1):
                    return True
        return False

    def import_key(self, keyfile, dryrun=False):
        if not dryrun:
            self.execute_command([self.rpm, '--import', keyfile])

    def drop_key(self, key, dryrun=False):
        if not dryrun:
            self.execute_command([self.rpm, '--erase', '--allmatches', "gpg-pubkey-%s" % key])


def main():
    module = AnsibleModule(
        argument_spec = dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            key=dict(required=True, type='str'),
            validate_certs=dict(default='yes', type='bool'),
            ),
        supports_check_mode=True
        )

    RpmKey(module)


if __name__ == '__main__':
    main()
