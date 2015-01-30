#!/usr/bin/python
#-*- coding: utf-8 -*-

# (c) 2013, Yeukhon Wong <yeukhon@acm.org>
# (c) 2014, Nate Coraor <nate@bx.psu.edu>
#
# This module was originally inspired by Brad Olson's ansible-module-mercurial
# <https://github.com/bradobro/ansible-module-mercurial>. This module tends
# to follow the git module implementation.
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

import ConfigParser

DOCUMENTATION = '''
---
module: hg
short_description: Manages Mercurial (hg) repositories.
description:
    - Manages Mercurial (hg) repositories. Supports SSH, HTTP/S and local address.
version_added: "1.0"
author: Yeukhon Wong
options:
    repo:
        description:
            - The repository address.
        required: true
        default: null
        aliases: [ name ]
    dest:
        description:
            - Absolute path of where the repository should be cloned to.
        required: true
        default: null
    revision:
        description:
            - Equivalent C(-r) option in hg command which could be the changeset, revision number,
              branch name or even tag.
        required: false
        default: null
        aliases: [ version ]
    force:
        description:
            - Discards uncommitted changes. Runs C(hg update -C).  Prior to
              1.9, the default was `yes`.
        required: false
        default: "no"
        choices: [ "yes", "no" ]
    purge:
        description:
            - Deletes untracked files. Runs C(hg purge).
        required: false
        default: "no"
        choices: [ "yes", "no" ]
    executable:
        required: false
        default: null
        version_added: "1.4"
        description:
            - Path to hg executable to use. If not supplied,
              the normal mechanism for resolving binary paths will be used.
notes:
    - "If the task seems to be hanging, first verify remote host is in C(known_hosts).
      SSH will prompt user to authorize the first contact with a remote host.  To avoid this prompt, 
      one solution is to add the remote host public key in C(/etc/ssh/ssh_known_hosts) before calling 
      the hg module, with the following command: ssh-keyscan remote_host.com >> /etc/ssh/ssh_known_hosts."
requirements: [ ]
'''

EXAMPLES = '''
# Ensure the current working copy is inside the stable branch and deletes untracked files if any.
- hg: repo=https://bitbucket.org/user/repo1 dest=/home/user/repo1 revision=stable purge=yes
'''

class Hg(object):

    def __init__(self, module, dest, repo, revision, hg_path):
        self.module = module
        self.dest = dest
        self.repo = repo
        self.revision = revision
        self.hg_path = hg_path

    def _command(self, args_list):
        (rc, out, err) = self.module.run_command([self.hg_path] + args_list)
        return (rc, out, err)

    def _list_untracked(self):
        args = ['purge', '--config', 'extensions.purge=', '-R', self.dest, '--print']
        return self._command(args)

    def get_revision(self):
        """
        hg id -b -i -t returns a string in the format:
           "<changeset>[+] <branch_name> <tag>"
        This format lists the state of the current working copy,
        and indicates whether there are uncommitted changes by the
        plus sign. Otherwise, the sign is omitted.

        Read the full description via hg id --help
        """
        (rc, out, err) = self._command(['id', '-b', '-i', '-t', '-R', self.dest])
        if rc != 0:
            self.module.fail_json(msg=err)
        else:
            return out.strip('\n')

    def has_local_mods(self):
        now = self.get_revision()
        if '+' in now:
            return True
        else:
            return False

    def discard(self):
        before = self.has_local_mods()
        if not before:
            return False

        args = ['update', '-C', '-R', self.dest]
        if self.revision is not None:
            args = args + ['-r', self.revision]
        (rc, out, err) = self._command(args)
        if rc != 0:
            self.module.fail_json(msg=err)

        after = self.has_local_mods()
        if before != after and not after:   # no more local modification
            return True

    def purge(self):
        # before purge, find out if there are any untracked files
        (rc1, out1, err1) = self._list_untracked()
        if rc1 != 0:
            self.module.fail_json(msg=err1)

        # there are some untrackd files
        if out1 != '':
            args = ['purge', '--config', 'extensions.purge=', '-R', self.dest]
            (rc2, out2, err2) = self._command(args)
            if rc2 != 0:
                self.module.fail_json(msg=err2)
            return True
        else:
            return False

    def cleanup(self, force, purge):
        discarded = False
        purged = False

        if force:
            discarded = self.discard()
        if purge:
            purged = self.purge()
        if discarded or purged:
            return True
        else:
            return False

    def pull(self):
        return self._command(
            ['pull', '-R', self.dest, self.repo])

    def update(self):
        if self.revision is not None:
            return self._command(['update', '-r', self.revision, '-R', self.dest])
        return self._command(['update', '-R', self.dest])

    def clone(self):
        if self.revision is not None:
            return self._command(['clone', self.repo, self.dest, '-r', self.revision])
        return self._command(['clone', self.repo, self.dest])

    @property
    def at_revision(self):
        """
        There is no point in pulling from a potentially down/slow remote site
        if the desired changeset is already the current changeset.
        """
        if self.revision is None or len(self.revision) < 7:
            # Assume it's a rev number, tag, or branch
            return False
        (rc, out, err) = self._command(['--debug', 'id', '-i', '-R', self.dest])
        if rc != 0:
            self.module.fail_json(msg=err)
        if out.startswith(self.revision):
            return True
        return False

# ===========================================

def main():
    module = AnsibleModule(
        argument_spec = dict(
            repo = dict(required=True, aliases=['name']),
            dest = dict(required=True),
            revision = dict(default=None, aliases=['version']),
            force = dict(default='no', type='bool'),
            purge = dict(default='no', type='bool'),
            executable = dict(default=None),
        ),
    )
    repo = module.params['repo']
    dest = os.path.expanduser(module.params['dest'])
    revision = module.params['revision']
    force = module.params['force']
    purge = module.params['purge']
    hg_path = module.params['executable'] or module.get_bin_path('hg', True)
    hgrc = os.path.join(dest, '.hg/hgrc')

    # initial states
    before = ''
    changed = False
    cleaned = False

    hg = Hg(module, dest, repo, revision, hg_path)

    # If there is no hgrc file, then assume repo is absent
    # and perform clone. Otherwise, perform pull and update.
    if not os.path.exists(hgrc):
        (rc, out, err) = hg.clone()
        if rc != 0:
            module.fail_json(msg=err)
    elif hg.at_revision:
        # no update needed, don't pull
        before = hg.get_revision()

        # but force and purge if desired
        cleaned = hg.cleanup(force, purge)
    else:
        # get the current state before doing pulling
        before = hg.get_revision()

        # can perform force and purge
        cleaned = hg.cleanup(force, purge)

        (rc, out, err) = hg.pull()
        if rc != 0:
            module.fail_json(msg=err)

        (rc, out, err) = hg.update()
        if rc != 0:
            module.fail_json(msg=err)

    after = hg.get_revision()
    if before != after or cleaned:
        changed = True
    module.exit_json(before=before, after=after, changed=changed, cleaned=cleaned)

# import module snippets
from ansible.module_utils.basic import *
main()
