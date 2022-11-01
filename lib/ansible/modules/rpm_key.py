# -*- coding: utf-8 -*-

# Ansible module to import third party repo keys to your rpm db
# Copyright: (c) 2013, Héctor Acosta <hector.acosta@gazzang.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: rpm_key
author:
  - Hector Acosta (@hacosta) <hector.acosta@gazzang.com>
short_description: Adds or removes a gpg key from the rpm db
description:
  - Adds or removes (rpm --import) a gpg key to your rpm database.
version_added: "1.3"
options:
    key:
      description:
        - Key that will be modified. Can be a url, a file on the managed node, or a keyid if the key
          already exists in the database.
      type: str
      required: true
    state:
      description:
        - If the key will be imported or removed from the rpm db.
      type: str
      default: present
      choices: [ absent, present ]
    validate_certs:
      description:
        - If C(false) and the C(key) is a url starting with https, SSL certificates will not be validated.
        - This should only be used on personally controlled sites using self-signed certificates.
      type: bool
      default: 'yes'
    fingerprint:
      description:
        - The long-form fingerprint of the key being imported.
        - This will be used to verify the specified key.
      type: str
      version_added: 2.9
extends_documentation_fragment:
    - action_common_attributes
attributes:
    check_mode:
        support: full
    diff_mode:
        support: none
    platform:
        platforms: rhel
'''

EXAMPLES = '''
- name: Import a key from a url
  ansible.builtin.rpm_key:
    state: present
    key: http://apt.sw.be/RPM-GPG-KEY.dag.txt

- name: Import a key from a file
  ansible.builtin.rpm_key:
    state: present
    key: /path/to/key.gpg

- name: Ensure a key is not present in the db
  ansible.builtin.rpm_key:
    state: absent
    key: DEADB33F

- name: Verify the key, using a fingerprint, before import
  ansible.builtin.rpm_key:
    key: /path/to/RPM-GPG-KEY.dag.txt
    fingerprint: EBC6 E12C 62B1 C734 026B  2122 A20E 5214 6B8D 79E6
'''

RETURN = r'''#'''

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
        fingerprint = module.params['fingerprint']
        if fingerprint:
            fingerprint = fingerprint.replace(' ', '').upper()

        self.gpg = self.module.get_bin_path('gpg')
        if not self.gpg:
            self.gpg = self.module.get_bin_path('gpg2', required=True)

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
                if fingerprint:
                    has_fingerprint = self.getfingerprint(keyfile)
                    if fingerprint != has_fingerprint:
                        self.module.fail_json(
                            msg="The specified fingerprint, '%s', does not match the key fingerprint '%s'" % (fingerprint, has_fingerprint)
                        )
                self.import_key(keyfile)
                if should_cleanup_keyfile:
                    self.module.cleanup(keyfile)
                module.exit_json(changed=True)
        else:
            if self.is_key_imported(keyid):
                self.drop_key(keyid)
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
        self.module.add_cleanup_file(tmpname)
        tmpfile = os.fdopen(tmpfd, "w+b")
        tmpfile.write(key)
        tmpfile.close()
        return tmpname

    def normalize_keyid(self, keyid):
        """Ensure a keyid doesn't have a leading 0x, has leading or trailing whitespace, and make sure is uppercase"""
        ret = keyid.strip().upper()
        if ret.startswith('0x'):
            return ret[2:]
        elif ret.startswith('0X'):
            return ret[2:]
        else:
            return ret

    def getkeyid(self, keyfile):
        stdout, stderr = self.execute_command([self.gpg, '--no-tty', '--batch', '--with-colons', '--fixed-list-mode', keyfile])
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith('pub:'):
                return line.split(':')[4]

        self.module.fail_json(msg="Unexpected gpg output")

    def getfingerprint(self, keyfile):
        stdout, stderr = self.execute_command([
            self.gpg, '--no-tty', '--batch', '--with-colons',
            '--fixed-list-mode', '--with-fingerprint', keyfile
        ])
        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith('fpr:'):
                # As mentioned here,
                #
                # https://git.gnupg.org/cgi-bin/gitweb.cgi?p=gnupg.git;a=blob_plain;f=doc/DETAILS
                #
                # The description of the `fpr` field says
                #
                # "fpr :: Fingerprint (fingerprint is in field 10)"
                #
                return line.split(':')[9]

        self.module.fail_json(msg="Unexpected gpg output")

    def is_keyid(self, keystr):
        """Verifies if a key, as provided by the user is a keyid"""
        return re.match('(0x)?[0-9a-f]{8}', keystr, flags=re.IGNORECASE)

    def execute_command(self, cmd):
        rc, stdout, stderr = self.module.run_command(cmd, use_unsafe_shell=True)
        if rc != 0:
            self.module.fail_json(msg=stderr)
        return stdout, stderr

    def is_key_imported(self, keyid):
        cmd = self.rpm + ' -q  gpg-pubkey'
        rc, stdout, stderr = self.module.run_command(cmd)
        if rc != 0:  # No key is installed on system
            return False
        cmd += ' --qf "%{description}" | ' + self.gpg + ' --no-tty --batch --with-colons --fixed-list-mode -'
        stdout, stderr = self.execute_command(cmd)
        for line in stdout.splitlines():
            if keyid in line.split(':')[4]:
                return True
        return False

    def import_key(self, keyfile):
        if not self.module.check_mode:
            self.execute_command([self.rpm, '--import', keyfile])

    def drop_key(self, keyid):
        if not self.module.check_mode:
            self.execute_command([self.rpm, '--erase', '--allmatches', "gpg-pubkey-%s" % keyid[-8:].lower()])


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['absent', 'present']),
            key=dict(type='str', required=True, no_log=False),
            fingerprint=dict(type='str'),
            validate_certs=dict(type='bool', default=True),
        ),
        supports_check_mode=True,
    )

    RpmKey(module)


if __name__ == '__main__':
    main()
