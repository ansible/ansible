#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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
module: subversion
short_description: Deploys a subversion repository.
description:
   - Deploy given repository URL / revision to dest. If dest exists, update to the specified revision, otherwise perform a checkout.
version_added: "0.7"
author: Dane Summers, njharman@gmail.com
notes:
   - Requires I(svn) to be installed on the client.
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
  export:
    required: false
    default: "no"
    choices: [ "yes", "no" ]
    version_added: "1.6"
    description:
      - If C(yes), do export instead of checkout/update.
'''

EXAMPLES = '''
# Checkout subversion repository to specified folder.
- subversion: repo=svn+ssh://an.example.org/path/to/repo dest=/src/checkout

# Export subversion directory to folder
- subversion: repo=svn+ssh://an.example.org/path/to/repo dest=/src/export export=True
'''

import re
import tempfile


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

    def _exec(self, args):
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
        rc, out, err = self.module.run_command(bits, check_rc=True)
        return out.splitlines()

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

    def has_local_mods(self):
        '''True if revisioned files have been added or modified. Unrevisioned files are ignored.'''
        lines = self._exec(["status", self.dest])
        # Match only revisioned files, i.e. ignore status '?'.
        regex = re.compile(r'^[^?]')
        # Has local mods if more than 0 modifed revisioned files.
        return len(filter(regex.match, lines)) > 0

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
            dest=dict(required=True),
            repo=dict(required=True, aliases=['name', 'repository']),
            revision=dict(default='HEAD', aliases=['rev', 'version']),
            force=dict(default='no', type='bool'),
            username=dict(required=False),
            password=dict(required=False),
            executable=dict(default=None),
            export=dict(default=False, required=False, type='bool'),
        ),
        supports_check_mode=True
    )

    dest = os.path.expanduser(module.params['dest'])
    repo = module.params['repo']
    revision = module.params['revision']
    force = module.params['force']
    username = module.params['username']
    password = module.params['password']
    svn_path = module.params['executable'] or module.get_bin_path('svn', True)
    export = module.params['export']

    os.environ['LANG'] = 'C'
    svn = Subversion(module, dest, repo, revision, username, password, svn_path)

    if export or not os.path.exists(dest):
        before = None
        local_mods = False
        if module.check_mode:
            module.exit_json(changed=True)
        if not export:
            svn.checkout()
        else:
            svn.export(force=force)
    elif os.path.exists("%s/.svn" % (dest, )):
        # Order matters. Need to get local mods before switch to avoid false
        # positives. Need to switch before revert to ensure we are reverting to
        # correct repo.
        if module.check_mode:
            check, before, after = svn.needs_update()
            module.exit_json(changed=check, before=before, after=after)
        before = svn.get_revision()
        local_mods = svn.has_local_mods()
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

# import module snippets
from ansible.module_utils.basic import *
main()
