#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2013, André Paramés <git@andreparames.com>
# Based on the Git module by Michael DeHaan <michael.dehaan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = u'''
---
module: bzr
author:
- André Paramés (@andreparames)
version_added: "1.1"
short_description: Deploy software (or files) from bzr branches
description:
    - Manage I(bzr) branches to deploy files or software.
options:
    name:
        description:
            - SSH or HTTP protocol address of the parent branch.
        aliases: [ parent ]
        required: yes
    dest:
        description:
            - Absolute path of where the branch should be cloned to.
        required: yes
    version:
        description:
            - What version of the branch to clone.  This can be the
              bzr revno or revid.
        default: head
    force:
        description:
            - If C(yes), any modified files in the working
              tree will be discarded.  Before 1.9 the default
              value was C(yes).
        type: bool
        default: 'no'
    executable:
        description:
            - Path to bzr executable to use. If not supplied,
              the normal mechanism for resolving binary paths will be used.
        version_added: '1.4'
'''

EXAMPLES = '''
# Example bzr checkout from Ansible Playbooks
- bzr:
    name: bzr+ssh://foosball.example.org/path/to/branch
    dest: /srv/checkout
    version: 22
'''

import os
import re

from ansible.module_utils.basic import AnsibleModule


class Bzr(object):
    def __init__(self, module, parent, dest, version, bzr_path):
        self.module = module
        self.parent = parent
        self.dest = dest
        self.version = version
        self.bzr_path = bzr_path

    def _command(self, args_list, cwd=None, **kwargs):
        (rc, out, err) = self.module.run_command([self.bzr_path] + args_list, cwd=cwd, **kwargs)
        return (rc, out, err)

    def get_version(self):
        '''samples the version of the bzr branch'''

        cmd = "%s revno" % self.bzr_path
        rc, stdout, stderr = self.module.run_command(cmd, cwd=self.dest)
        revno = stdout.strip()
        return revno

    def clone(self):
        '''makes a new bzr branch if it does not already exist'''
        dest_dirname = os.path.dirname(self.dest)
        try:
            os.makedirs(dest_dirname)
        except:
            pass
        if self.version.lower() != 'head':
            args_list = ["branch", "-r", self.version, self.parent, self.dest]
        else:
            args_list = ["branch", self.parent, self.dest]
        return self._command(args_list, check_rc=True, cwd=dest_dirname)

    def has_local_mods(self):

        cmd = "%s status -S" % self.bzr_path
        rc, stdout, stderr = self.module.run_command(cmd, cwd=self.dest)
        lines = stdout.splitlines()

        lines = filter(lambda c: not re.search('^\\?\\?.*$', c), lines)
        return len(lines) > 0

    def reset(self, force):
        '''
        Resets the index and working tree to head.
        Discards any changes to tracked files in the working
        tree since that commit.
        '''
        if not force and self.has_local_mods():
            self.module.fail_json(msg="Local modifications exist in branch (force=no).")
        return self._command(["revert"], check_rc=True, cwd=self.dest)

    def fetch(self):
        '''updates branch from remote sources'''
        if self.version.lower() != 'head':
            (rc, out, err) = self._command(["pull", "-r", self.version], cwd=self.dest)
        else:
            (rc, out, err) = self._command(["pull"], cwd=self.dest)
        if rc != 0:
            self.module.fail_json(msg="Failed to pull")
        return (rc, out, err)

    def switch_version(self):
        '''once pulled, switch to a particular revno or revid'''
        if self.version.lower() != 'head':
            args_list = ["revert", "-r", self.version]
        else:
            args_list = ["revert"]
        return self._command(args_list, check_rc=True, cwd=self.dest)


# ===========================================

def main():
    module = AnsibleModule(
        argument_spec=dict(
            dest=dict(type='path', required=True),
            name=dict(type='str', required=True, aliases=['parent']),
            version=dict(type='str', default='head'),
            force=dict(type='bool', default='no'),
            executable=dict(type='str'),
        )
    )

    dest = module.params['dest']
    parent = module.params['name']
    version = module.params['version']
    force = module.params['force']
    bzr_path = module.params['executable'] or module.get_bin_path('bzr', True)

    bzrconfig = os.path.join(dest, '.bzr', 'branch', 'branch.conf')

    rc, out, err = (0, None, None)

    bzr = Bzr(module, parent, dest, version, bzr_path)

    # if there is no bzr configuration, do a branch operation
    # else pull and switch the version
    before = None
    local_mods = False
    if not os.path.exists(bzrconfig):
        (rc, out, err) = bzr.clone()

    else:
        # else do a pull
        local_mods = bzr.has_local_mods()
        before = bzr.get_version()
        (rc, out, err) = bzr.reset(force)
        if rc != 0:
            module.fail_json(msg=err)
        (rc, out, err) = bzr.fetch()
        if rc != 0:
            module.fail_json(msg=err)

    # switch to version specified regardless of whether
    # we cloned or pulled
    (rc, out, err) = bzr.switch_version()

    # determine if we changed anything
    after = bzr.get_version()
    changed = False

    if before != after or local_mods:
        changed = True

    module.exit_json(changed=changed, before=before, after=after)


if __name__ == '__main__':
    main()
