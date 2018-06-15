#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Luis Alberto Perez Lazaro <luisperlazaro@gmail.com>
# Copyright: (c) 2015, Jakub Jirutka <jakub@jirutka.cz>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: patch
author:
    - Jakub Jirutka (@jirutka)
    - Luis Alberto Perez Lazaro (@luisperlaz)
version_added: '1.9'
description:
    - Apply patch files using the GNU patch tool.
short_description: Apply patch files using the GNU patch tool
options:
  basedir:
    description:
      - Path of a base directory in which the patch file will be applied.
        May be omitted when C(dest) option is specified, otherwise required.
  dest:
    description:
      - Path of the file on the remote machine to be patched.
      - The names of the files to be patched are usually taken from the patch
        file, but if there's just one file to be patched it can specified with
        this option.
    aliases: [ originalfile ]
  src:
    description:
      - Path of the patch file as accepted by the GNU patch tool. If
        C(remote_src) is 'no', the patch source file is looked up from the
        module's I(files) directory.
    required: true
    aliases: [ patchfile ]
  state:
    version_added: "2.6"
    description:
      - Whether the patch should be applied or reverted.
    choices: [ absent, present ]
    default: present
  remote_src:
    description:
      - If C(no), it will search for src at originating/master machine, if C(yes) it will
        go to the remote/target machine for the C(src).
    type: bool
    default: 'no'
  strip:
    description:
      - Number that indicates the smallest prefix containing leading slashes
        that will be stripped from each file name found in the patch file.
        For more information see the strip parameter of the GNU patch tool.
    default: 0
  backup:
    version_added: "2.0"
    description:
      - Passes C(--backup --version-control=numbered) to patch,
        producing numbered backup copies.
    type: bool
    default: 'no'
  binary:
    version_added: "2.0"
    description:
      - Setting to C(yes) will disable patch's heuristic for transforming CRLF
        line endings into LF. Line endings of src and dest must match. If set to
        C(no), C(patch) will replace CRLF in C(src) files on POSIX.
    type: bool
    default: 'no'
notes:
  - This module requires GNU I(patch) utility to be installed on the remote host.
'''

EXAMPLES = r'''
- name: Apply patch to one file
  patch:
    src: /tmp/index.html.patch
    dest: /var/www/index.html

- name: Apply patch to multiple files under basedir
  patch:
    src: /tmp/customize.patch
    basedir: /var/www
    strip: 1

- name: Revert patch to one file
  patch:
    src: /tmp/index.html.patch
    dest: /var/www/index.html
    state: absent
'''

import os
from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


class PatchError(Exception):
    pass


def is_already_applied(patch_func, patch_file, basedir, dest_file=None, binary=False, strip=0, state='present'):
    opts = ['--quiet', '--forward', '--dry-run',
            "--strip=%s" % strip, "--directory='%s'" % basedir,
            "--input='%s'" % patch_file]
    if binary:
        opts.append('--binary')
    if dest_file:
        opts.append("'%s'" % dest_file)
    if state == 'present':
        opts.append('--reverse')

    (rc, _, _) = patch_func(opts)
    return rc == 0


def apply_patch(patch_func, patch_file, basedir, dest_file=None, binary=False, strip=0, dry_run=False, backup=False, state='present'):
    opts = ['--quiet', '--forward', '--batch', '--reject-file=-',
            "--strip=%s" % strip, "--directory='%s'" % basedir,
            "--input='%s'" % patch_file]
    if dry_run:
        opts.append('--dry-run')
    if binary:
        opts.append('--binary')
    if dest_file:
        opts.append("'%s'" % dest_file)
    if backup:
        opts.append('--backup --version-control=numbered')
    if state == 'absent':
        opts.append('--reverse')

    (rc, out, err) = patch_func(opts)
    if rc != 0:
        msg = err or out
        raise PatchError(msg)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            src=dict(type='path', required=True, aliases=['patchfile']),
            dest=dict(type='path', aliases=['originalfile']),
            basedir=dict(type='path'),
            strip=dict(type='int', default=0),
            remote_src=dict(type='bool', default=False),
            # NB: for 'backup' parameter, semantics is slightly different from standard
            #     since patch will create numbered copies, not strftime("%Y-%m-%d@%H:%M:%S~")
            backup=dict(type='bool', default=False),
            binary=dict(type='bool', default=False),
            state=dict(type='str', default='present', choices=['absent', 'present']),
        ),
        required_one_of=[['dest', 'basedir']],
        supports_check_mode=True,
    )

    # Create type object as namespace for module params
    p = type('Params', (), module.params)

    if not os.access(p.src, os.R_OK):
        module.fail_json(msg="src %s doesn't exist or not readable" % (p.src))

    if p.dest and not os.access(p.dest, os.W_OK):
        module.fail_json(msg="dest %s doesn't exist or not writable" % (p.dest))

    if p.basedir and not os.path.exists(p.basedir):
        module.fail_json(msg="basedir %s doesn't exist" % (p.basedir))

    if not p.basedir:
        p.basedir = os.path.dirname(p.dest)

    patch_bin = module.get_bin_path('patch')
    if patch_bin is None:
        module.fail_json(msg="patch command not found")

    def patch_func(opts):
        return module.run_command('%s %s' % (patch_bin, ' '.join(opts)))

    # patch need an absolute file name
    p.src = os.path.abspath(p.src)

    changed = False
    if not is_already_applied(patch_func, p.src, p.basedir, dest_file=p.dest, binary=p.binary, strip=p.strip, state=p.state):
        try:
            apply_patch(patch_func, p.src, p.basedir, dest_file=p.dest, binary=p.binary, strip=p.strip,
                        dry_run=module.check_mode, backup=p.backup, state=p.state)
            changed = True
        except PatchError as e:
            module.fail_json(msg=to_native(e), exception=format_exc())

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
