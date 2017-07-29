#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: subversion
short_description: Deploys a subversion repository.
description:
   - Deploy given repository URL / revision to dest. If dest exists, update to the specified revision, otherwise perform a checkout.
version_added: "0.7"
author: "Dane Summers (@dsummersl) <njharman@gmail.com>"
notes:
   - Requires I(svn) to be installed on the client.
   - This module does not handle externals
requirements: []
options:
  repo:
    description:
      - The subversion URL to the repository.
    required: true
    aliases: [ name, repository ]
    default: null
  dest:
    description:
      - Absolute path where the repository should be deployed.
    required: true
    default: null
  revision:
    description:
      - Specific revision to checkout.
    required: false
    default: HEAD
    aliases: [ version ]
  force:
    description:
      - If C(yes), modified files will be discarded. If C(no), module will fail if it encounters modified files.
        Prior to 1.9 the default was `yes`.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  username:
    description:
      - --username parameter passed to svn.
    required: false
    default: null
  password:
    description:
      - --password parameter passed to svn.
    required: false
    default: null
  executable:
    required: false
    default: null
    version_added: "1.4"
    description:
      - Path to svn executable to use. If not supplied,
        the normal mechanism for resolving binary paths will be used.
  checkout:
    required: false
    default: "yes"
    choices: [ "yes", "no" ]
    version_added: "2.3"
    description:
     - If no, do not check out the repository if it does not exist locally
  update:
    required: false
    default: "yes"
    choices: [ "yes", "no" ]
    version_added: "2.3"
    description:
     - If no, do not retrieve new revisions from the origin repository
  export:
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    version_added: "1.6"
    description:
      - If C(yes), do export instead of checkout/update.
  switch:
    required: false
    default: "yes"
    choices: [ "yes", "no" ]
    version_added: "2.0"
    description:
      - If C(no), do not call svn switch before update.
'''

EXAMPLES = '''
# Checkout subversion repository to specified folder.
- subversion:
    repo: svn+ssh://an.example.org/path/to/repo
    dest: /src/checkout

# Export subversion directory to folder
- subversion:
    repo: svn+ssh://an.example.org/path/to/repo
    dest: /src/export

# Example just get information about the repository whether or not it has
# already been cloned locally.
- subversion:
    repo: svn+ssh://an.example.org/path/to/repo
    dest: /srv/checkout
    checkout: no
    update: no
'''

import os
import re

from ansible.module_utils.basic import AnsibleModule


class Subversion(object):
    def __init__(
            self, module, dest, repo, revision, username, password, svn_path):
        self.module = module
        self.dest = dest
        self.repo = repo
        self.revision = revision
        self.username = username
        self.password = password
        self.svn_path = svn_path

    def _exec(self, args, check_rc=True):
        '''Execute a subversion command, and return output. If check_rc is False, returns the return code instead of the output.'''
        bits = [
            self.svn_path,
            '--non-interactive',
            '--trust-server-cert',
            '--no-auth-cache',
        ]
        if self.username:
            bits.extend(["--username", self.username])
        if self.password:
            bits.extend(["--password", self.password])
        bits.extend(args)
        rc, out, err = self.module.run_command(bits, check_rc)
        if check_rc:
            return out.splitlines()
        else:
            return rc

    def is_svn_repo(self):
        '''Checks if path is a SVN Repo.'''
        rc = self._exec(["info", self.dest], check_rc=False)
        return rc == 0

    def checkout(self):
        '''Creates new svn working directory if it does not already exist.'''
        self._exec(["checkout", "-r", self.revision, self.repo, self.dest])

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
        self._exec(["switch", self.repo, self.dest])

    def update(self):
        '''Update existing svn working directory.'''
        self._exec(["update", "-r", self.revision, self.dest])

    def revert(self):
        '''Revert svn working directory.'''
        self._exec(["revert", "-R", self.dest])

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
        lines = self._exec(["status", "--quiet", "--ignore-externals",  self.dest])
        # The --quiet option will return only modified files.
        # Match only revisioned files, i.e. ignore status '?'.
        regex = re.compile(r'^[^?X]')
        # Has local mods if more than 0 modified revisioned files.
        return len(list(filter(regex.match, lines))) > 0

    def needs_update(self):
        curr, url = self.get_revision()
        out2 = '\n'.join(self._exec(["info", "-r", "HEAD", self.dest]))
        head = re.search(r'^Revision:.*$', out2, re.MULTILINE).group(0)
        rev1 = int(curr.split(':')[1].strip())
        rev2 = int(head.split(':')[1].strip())
        change = False
        if rev1 < rev2:
            change = True
        return change, curr, head


# ===========================================

def main():
    module = AnsibleModule(
        argument_spec=dict(
            dest=dict(type='path'),
            repo=dict(required=True, aliases=['name', 'repository']),
            revision=dict(default='HEAD', aliases=['rev', 'version']),
            force=dict(default='no', type='bool'),
            username=dict(required=False),
            password=dict(required=False, no_log=True),
            executable=dict(default=None, type='path'),
            export=dict(default=False, required=False, type='bool'),
            checkout=dict(default=True, required=False, type='bool'),
            update=dict(default=True, required=False, type='bool'),
            switch=dict(default=True, required=False, type='bool'),
        ),
        supports_check_mode=True
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
        else:
            svn.export(force=force)
    elif svn.is_svn_repo():
        # Order matters. Need to get local mods before switch to avoid false
        # positives. Need to switch before revert to ensure we are reverting to
        # correct repo.
        if module.check_mode or not update:
            if svn.has_local_mods() and not force:
                module.fail_json(msg="ERROR: modified files exist in the repository.")
            check, before, after = svn.needs_update()
            module.exit_json(changed=check, before=before, after=after)
        before = svn.get_revision()
        local_mods = svn.has_local_mods()
        if switch:
            svn.switch()
        if local_mods:
            if force:
                svn.revert()
            else:
                module.fail_json(msg="ERROR: modified files exist in the repository.")
        svn.update()
    else:
        module.fail_json(msg="ERROR: %s folder already exists, but its not a subversion repository." % (dest, ))

    if export:
        module.exit_json(changed=True)
    else:
        after = svn.get_revision()
        changed = before != after or local_mods
        module.exit_json(changed=changed, before=before, after=after)


if __name__ == '__main__':
    main()
