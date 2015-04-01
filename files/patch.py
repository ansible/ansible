#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Luis Alberto Perez Lazaro <luisperlazaro@gmail.com>
# (c) 2015, Jakub Jirutka <jakub@jirutka.cz>
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
module: patch
author: Luis Alberto Perez Lazaro, Jakub Jirutka
version_added: 1.9
description:
    - Apply patch files using the GNU patch tool.
short_description: Apply patch files using the GNU patch tool.
options:
  basedir:
    description:
      - Path of a base directory in which the patch file will be applied.
        May be ommitted when C(dest) option is specified, otherwise required.
    required: false
  dest:
    description:
      - Path of the file on the remote machine to be patched.
      - The names of the files to be patched are usually taken from the patch
        file, but if there's just one file to be patched it can specified with
        this option.
    required: false
    aliases: [ "originalfile" ]
  src:
    description:
      - Path of the patch file as accepted by the GNU patch tool. If
        C(remote_src) is False, the patch source file is looked up from the
        module's "files" directory.
    required: true
    aliases: [ "patchfile" ]
  remote_src:
    description:
      - If False, it will search for src at originating/master machine, if True it will
        go to the remote/target machine for the src. Default is False.
    choices: [ "True", "False" ]
    required: false
    default: "False"
  strip:
    description:
      - Number that indicates the smallest prefix containing leading slashes
        that will be stripped from each file name found in the patch file.
        For more information see the strip parameter of the GNU patch tool.
    required: false
    type: "int"
    default: "0"
note:
  - This module requires GNU I(patch) utility to be installed on the remote host.
'''

EXAMPLES = '''
- name: apply patch to one file
  patch: >
    src=/tmp/index.html.patch
    dest=/var/www/index.html

- name: apply patch to multiple files under basedir
  patch: >
    src=/tmp/customize.patch
    basedir=/var/www
    strip=1
'''

import os
from os import path, R_OK, W_OK


class PatchError(Exception):
    pass


def is_already_applied(patch_func, patch_file, basedir, dest_file=None, strip=0):
    opts = ['--quiet', '--reverse', '--forward', '--dry-run',
            "--strip=%s" % strip, "--directory='%s'" % basedir,
            "--input='%s'" % patch_file]
    if dest_file:
        opts.append("'%s'" % dest_file)

    (rc, _, _) = patch_func(opts)
    return rc == 0


def apply_patch(patch_func, patch_file, basedir, dest_file=None, strip=0, dry_run=False):
    opts = ['--quiet', '--forward', '--batch', '--reject-file=-',
            "--strip=%s" % strip, "--directory='%s'" % basedir,
            "--input='%s'" % patch_file]
    if dry_run:
        opts.append('--dry-run')
    if dest_file:
        opts.append("'%s'" % dest_file)

    (rc, out, err) = patch_func(opts)
    if rc != 0:
        msg = out if not err else err
        raise PatchError(msg)


def main():
    module = AnsibleModule(
        argument_spec={
            'src':     {'required': True, 'aliases': ['patchfile']},
            'dest':    {'aliases': ['originalfile']},
            'basedir': {},
            'strip':   {'default': 0, 'type': 'int'},
            'remote_src': {'default': False, 'type': 'bool'},
        },
        required_one_of=[['dest', 'basedir']],
        supports_check_mode=True
    )

    # Create type object as namespace for module params
    p = type('Params', (), module.params)

    if not os.access(p.src, R_OK):
        module.fail_json(msg="src %s doesn't exist or not readable" % (p.src))

    if p.dest and not os.access(p.dest, W_OK):
        module.fail_json(msg="dest %s doesn't exist or not writable" % (p.dest))

    if p.basedir and not path.exists(p.basedir):
        module.fail_json(msg="basedir %s doesn't exist" % (p.basedir))

    if not p.basedir:
        p.basedir = path.dirname(p.dest)

    patch_bin = module.get_bin_path('patch')
    if patch_bin is None:
        module.fail_json(msg="patch command not found")
    patch_func = lambda opts: module.run_command("%s %s" % (patch_bin, ' '.join(opts)))

    # patch need an absolute file name
    p.src = os.path.abspath(p.src)
    
    changed = False
    if not is_already_applied(patch_func, p.src, p.basedir, dest_file=p.dest, strip=p.strip):
        try:
            apply_patch(patch_func, p.src, p.basedir, dest_file=p.dest, strip=p.strip,
                        dry_run=module.check_mode)
            changed = True
        except PatchError, e:
            module.fail_json(msg=str(e))

    module.exit_json(changed=changed)

# import module snippets
from ansible.module_utils.basic import *
main()
