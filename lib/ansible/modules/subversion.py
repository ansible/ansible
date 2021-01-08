#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
---
module: subversion
short_description: Deploys a subversion repository
description:
   - Deploy given repository URL / revision to dest. If dest exists, update to the specified revision, otherwise perform a checkout.
version_added: "0.7"
author:
- Dane Summers (@dsummersl) <njharman@gmail.com>
notes:
   - This module does not handle externals.
   - Supports C(check_mode).
options:
  repo:
    description:
      - The subversion URL to the repository.
    required: true
    aliases: [ name, repository ]
  dest:
    description:
      - Absolute path where the repository should be deployed.
    required: true
  revision:
    description:
      - Specific revision to checkout.
    default: HEAD
    aliases: [ version ]
  force:
    description:
      - If C(yes), modified files will be discarded. If C(no), module will fail if it encounters modified files.
        Prior to 1.9 the default was C(yes).
    type: bool
    default: "no"
  in_place:
    description:
      - If the directory exists, then the working copy will be checked-out over-the-top using
        svn checkout --force; if force is specified then existing files with different content are reverted.
    type: bool
    default: "no"
    version_added: "2.6"
  username:
    description:
      - C(--username) parameter passed to svn.
  password:
    description:
      - C(--password) parameter passed to svn when svn is less than version 1.10.0. This is not secure and
        the password will be leaked to argv.
      - C(--password-from-stdin) parameter when svn is greater or equal to version 1.10.0.
  executable:
    description:
      - Path to svn executable to use. If not supplied,
        the normal mechanism for resolving binary paths will be used.
    version_added: "1.4"
  checkout:
    description:
     - If C(no), do not check out the repository if it does not exist locally.
    type: bool
    default: "yes"
    version_added: "2.3"
  update:
    description:
     - If C(no), do not retrieve new revisions from the origin repository.
    type: bool
    default: "yes"
    version_added: "2.3"
  export:
    description:
      - If C(yes), do export instead of checkout/update.
    type: bool
    default: "no"
    version_added: "1.6"
  switch:
    description:
      - If C(no), do not call svn switch before update.
    default: "yes"
    version_added: "2.0"
    type: bool

requirements:
    - subversion (the command line tool with C(svn) entrypoint)
'''

EXAMPLES = '''
- name: Checkout subversion repository to specified folder
  ansible.builtin.subversion:
    repo: svn+ssh://an.example.org/path/to/repo
    dest: /src/checkout

- name: Export subversion directory to folder
  ansible.builtin.subversion:
    repo: svn+ssh://an.example.org/path/to/repo
    dest: /src/export
    export: yes

- name: Get information about the repository whether or not it has already been cloned locally
  ansible.builtin.subversion:
    repo: svn+ssh://an.example.org/path/to/repo
    dest: /src/checkout
    checkout: no
    update: no
'''

RETURN = r'''#'''

import os
import re

from distutils.version import LooseVersion

from ansible.module_utils.basic import AnsibleModule


class Subversion(object):
    def __init__(self, module, dest, repo, revision, username, password, svn_path):
        self.module = module
        self.dest = dest
        self.repo = repo
        self.revision = revision
        self.username = username
        self.password = password
        self.svn_path = svn_path

    def has_option_password_from_stdin(self):
        rc, version, err = self.module.run_command([self.svn_path, '--version', '--quiet'], check_rc=True)
        return LooseVersion(version) >= LooseVersion('1.10.0')

    def _exec(self, args, check_rc=True):
        '''Execute a subversion command, and return output. If check_rc is False, returns the return code instead of the output.'''
        bits = [
            self.svn_path,
            '--non-interactive',
            '--trust-server-cert',
            '--no-auth-cache',
        ]
        stdin_data = None
        if self.username:
            bits.extend(["--username", self.username])
        if self.password:
            if self.has_option_password_from_stdin():
                bits.append("--password-from-stdin")
                stdin_data = self.password
            else:
                self.module.warn("The authentication provided will be used on the svn command line and is not secure. "
                                 "To securely pass credentials, upgrade svn to version 1.10.0 or greater.")
                bits.extend(["--password", self.password])
        bits.extend(args)
        rc, out, err = self.module.run_command(bits, check_rc, data=stdin_data)

        if check_rc:
            return out.splitlines()
        else:
            return rc

    def is_svn_repo(self):
        '''Checks if path is a SVN Repo.'''
        rc = self._exec(["info", self.dest], check_rc=False)
        return rc == 0

    def checkout(self, force=False):
        '''Creates new svn working directory if it does not already exist.'''
        cmd = ["checkout"]
        if force:
            cmd.append("--force")
        cmd.extend(["-r", self.revision, self.repo, self.dest])
        self._exec(cmd)

    def export(self, force=False):
        '''Export svn repo to directory'''
        cmd = ["export"]
        if force:
            cmd.append("--force")
        cmd.extend(["-r", self.revision, self.repo, self.dest])

        self._exec(cmd)

    def switch(self):
        '''Change working directory's repo.'''
        # switch to ensure we are pointing at correct repo.
        # it also updates!
        output = self._exec(["switch", "--revision", self.revision, self.repo, self.dest])
        for line in output:
            if re.search(r'^[ABDUCGE]\s', line):
                return True
        return False

    def update(self):
        '''Update existing svn working directory.'''
        output = self._exec(["update", "-r", self.revision, self.dest])

        for line in output:
            if re.search(r'^[ABDUCGE]\s', line):
                return True
        return False

    def revert(self):
        '''Revert svn working directory.'''
        output = self._exec(["revert", "-R", self.dest])
        for line in output:
            if re.search(r'^Reverted ', line) is None:
                return True
        return False

    def get_revision(self):
        '''Revision and URL of subversion working directory.'''
        text = '\n'.join(self._exec(["info", self.dest]))
        rev = re.search(r'^Revision:.*$', text, re.MULTILINE).group(0)
        url = re.search(r'^URL:.*$', text, re.MULTILINE).group(0)
        return rev, url

    def get_remote_revision(self):
        '''Revision and URL of subversion working directory.'''
        text = '\n'.join(self._exec(["info", self.repo]))
        rev = re.search(r'^Revision:.*$', text, re.MULTILINE).group(0)
        return rev

    def has_local_mods(self):
        '''True if revisioned files have been added or modified. Unrevisioned files are ignored.'''
        lines = self._exec(["status", "--quiet", "--ignore-externals", self.dest])
        # The --quiet option will return only modified files.
        # Match only revisioned files, i.e. ignore status '?'.
        regex = re.compile(r'^[^?X]')
        # Has local mods if more than 0 modified revisioned files.
        return len(list(filter(regex.match, lines))) > 0

    def needs_update(self):
        curr, url = self.get_revision()
        out2 = '\n'.join(self._exec(["info", "-r", self.revision, self.dest]))
        head = re.search(r'^Revision:.*$', out2, re.MULTILINE).group(0)
        rev1 = int(curr.split(':')[1].strip())
        rev2 = int(head.split(':')[1].strip())
        change = False
        if rev1 < rev2:
            change = True
        return change, curr, head


def main():
    module = AnsibleModule(
        argument_spec=dict(
            dest=dict(type='path'),
            repo=dict(type='str', required=True, aliases=['name', 'repository']),
            revision=dict(type='str', default='HEAD', aliases=['rev', 'version']),
            force=dict(type='bool', default=False),
            username=dict(type='str'),
            password=dict(type='str', no_log=True),
            executable=dict(type='path'),
            export=dict(type='bool', default=False),
            checkout=dict(type='bool', default=True),
            update=dict(type='bool', default=True),
            switch=dict(type='bool', default=True),
            in_place=dict(type='bool', default=False),
        ),
        supports_check_mode=True,
    )

    dest = module.params['dest']
    repo = module.params['repo']
    revision = module.params['revision']
    force = module.params['force']
    username = module.params['username']
    password = module.params['password']
    svn_path = module.params['executable'] or module.get_bin_path('svn', True)
    export = module.params['export']
    switch = module.params['switch']
    checkout = module.params['checkout']
    update = module.params['update']
    in_place = module.params['in_place']

    # We screenscrape a huge amount of svn commands so use C locale anytime we
    # call run_command()
    module.run_command_environ_update = dict(LANG='C', LC_MESSAGES='C')

    if not dest and (checkout or update or export):
        module.fail_json(msg="the destination directory must be specified unless checkout=no, update=no, and export=no")

    svn = Subversion(module, dest, repo, revision, username, password, svn_path)

    if not export and not update and not checkout:
        module.exit_json(changed=False, after=svn.get_remote_revision())
    if export or not os.path.exists(dest):
        before = None
        local_mods = False
        if module.check_mode:
            module.exit_json(changed=True)
        elif not export and not checkout:
            module.exit_json(changed=False)
        if not export and checkout:
            svn.checkout()
            files_changed = True
        else:
            svn.export(force=force)
            files_changed = True
    elif svn.is_svn_repo():
        # Order matters. Need to get local mods before switch to avoid false
        # positives. Need to switch before revert to ensure we are reverting to
        # correct repo.
        if not update:
            module.exit_json(changed=False)
        if module.check_mode:
            if svn.has_local_mods() and not force:
                module.fail_json(msg="ERROR: modified files exist in the repository.")
            check, before, after = svn.needs_update()
            module.exit_json(changed=check, before=before, after=after)
        files_changed = False
        before = svn.get_revision()
        local_mods = svn.has_local_mods()
        if switch:
            files_changed = svn.switch() or files_changed
        if local_mods:
            if force:
                files_changed = svn.revert() or files_changed
            else:
                module.fail_json(msg="ERROR: modified files exist in the repository.")
        files_changed = svn.update() or files_changed
    elif in_place:
        before = None
        svn.checkout(force=True)
        files_changed = True
        local_mods = svn.has_local_mods()
        if local_mods and force:
            svn.revert()
    else:
        module.fail_json(msg="ERROR: %s folder already exists, but its not a subversion repository." % (dest,))

    if export:
        module.exit_json(changed=True)
    else:
        after = svn.get_revision()
        changed = files_changed or local_mods
        module.exit_json(changed=changed, before=before, after=after)


if __name__ == '__main__':
    main()
