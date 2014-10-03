#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2013, Dylan Martin <dmartin@seattlecentral.edu>
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
module: unarchive
version_added: 1.4
short_description: Copies an archive to a remote location and unpack it
extends_documentation_fragment: files
description:
     - The M(unarchive) module copies an archive file from the local machine to a remote and unpacks it.
options:
  src:
    description:
      - Local path to archive file to copy to the remote server; can be absolute or relative.
    required: true
    default: null
  dest:
    description:
      - Remote absolute path where the archive should be unpacked
    required: true
    default: null
  copy:
    description:
      - "if true, the file is copied from the 'master' to the target machine, otherwise, the plugin will look for src archive at the target machine."
    required: false
    choices: [ "yes", "no" ]
    default: "yes"
  creates:
    description:
      - a filename, when it already exists, this step will B(not) be run.
    required: no
    default: null
    version_added: "1.6"
author: Dylan Martin
todo:
    - detect changed/unchanged for .zip files
    - handle common unarchive args, like preserve owner/timestamp etc...
notes:
    - requires C(tar)/C(unzip) command on target host
    - can handle I(gzip), I(bzip2) and I(xz) compressed as well as uncompressed tar files
    - detects type of archive automatically
    - uses tar's C(--diff arg) to calculate if changed or not. If this C(arg) is not
      supported, it will always unpack the archive
    - does not detect if a .zip file is different from destination - always unzips
    - existing files/directories in the destination which are not in the archive
      are not touched.  This is the same behavior as a normal archive extraction
    - existing files/directories in the destination which are not in the archive
      are ignored for purposes of deciding if the archive should be unpacked or not
'''

EXAMPLES = '''
# Example from Ansible Playbooks
- unarchive: src=foo.tgz dest=/var/lib/foo

# Unarchive a file that is already on the remote machine
- unarchive: src=/tmp/foo.zip dest=/usr/local/bin copy=no
'''

import os


# class to handle .zip files
class ZipFile(object):
    
    def __init__(self, src, dest, module):
        self.src = src
        self.dest = dest
        self.module = module
        self.cmd_path = self.module.get_bin_path('unzip')

    def is_unarchived(self):
        return dict(unarchived=False)

    def unarchive(self):
        cmd = '%s -o "%s" -d "%s"' % (self.cmd_path, self.src, self.dest)
        rc, out, err = self.module.run_command(cmd)
        return dict(cmd=cmd, rc=rc, out=out, err=err)

    def can_handle_archive(self):
        if not self.cmd_path:
            return False
        cmd = '%s -l "%s"' % (self.cmd_path, self.src)
        rc, out, err = self.module.run_command(cmd)
        if rc == 0:
            return True
        return False


# class to handle gzipped tar files
class TgzFile(object):
    
    def __init__(self, src, dest, module):
        self.src = src
        self.dest = dest
        self.module = module
        self.cmd_path = self.module.get_bin_path('tar')
        self.zipflag = 'z'

    def is_unarchived(self):
        cmd = '%s -v -C "%s" --diff -%sf "%s"' % (self.cmd_path, self.dest, self.zipflag, self.src)
        rc, out, err = self.module.run_command(cmd)
        unarchived = (rc == 0)
        return dict(unarchived=unarchived, rc=rc, out=out, err=err, cmd=cmd)

    def unarchive(self):
        cmd = '%s -x%sf "%s"' % (self.cmd_path, self.zipflag, self.src)
        rc, out, err = self.module.run_command(cmd, cwd=self.dest)
        return dict(cmd=cmd, rc=rc, out=out, err=err)

    def can_handle_archive(self):
        if not self.cmd_path:
            return False
        cmd = '%s -t%sf "%s"' % (self.cmd_path, self.zipflag, self.src)
        rc, out, err = self.module.run_command(cmd)
        if rc == 0:
            if len(out.splitlines(True)) > 0:
                return True
        return False


# class to handle tar files that aren't compressed
class TarFile(TgzFile):
    def __init__(self, src, dest, module):
        self.src = src
        self.dest = dest
        self.module = module
        self.cmd_path = self.module.get_bin_path('tar')
        self.zipflag = ''


# class to handle bzip2 compressed tar files
class TarBzip(TgzFile):
    def __init__(self, src, dest, module):
        self.src = src
        self.dest = dest
        self.module = module
        self.cmd_path = self.module.get_bin_path('tar')
        self.zipflag = 'j'


# class to handle xz compressed tar files
class TarXz(TgzFile):
    def __init__(self, src, dest, module):
        self.src = src
        self.dest = dest
        self.module = module
        self.cmd_path = self.module.get_bin_path('tar')
        self.zipflag = 'J'


# try handlers in order and return the one that works or bail if none work
def pick_handler(src, dest, module):
    handlers = [TgzFile, ZipFile, TarFile, TarBzip, TarXz]
    for handler in handlers:
        obj = handler(src, dest, module)
        if obj.can_handle_archive():
            return obj
    module.fail_json(msg='Failed to find handler to unarchive. Make sure the required command to extract the file is installed.')


def main():
    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec = dict(
            src               = dict(required=True),
            original_basename = dict(required=False), # used to handle 'dest is a directory' via template, a slight hack
            dest              = dict(required=True),
            copy              = dict(default=True, type='bool'),
            creates           = dict(required=False),
        ),
        add_file_common_args=True,
    )

    src    = os.path.expanduser(module.params['src'])
    dest   = os.path.expanduser(module.params['dest'])
    copy   = module.params['copy']

    # did tar file arrive?
    if not os.path.exists(src):
        if copy:
            module.fail_json(msg="Source '%s' failed to transfer" % src)
        else:
            module.fail_json(msg="Source '%s' does not exist" % src)
    if not os.access(src, os.R_OK):
        module.fail_json(msg="Source '%s' not readable" % src)

    # is dest OK to receive tar file?
    if not os.path.isdir(dest):
        module.fail_json(msg="Destination '%s' is not a directory" % dest)
    if not os.access(dest, os.W_OK):
        module.fail_json(msg="Destination '%s' not writable" % dest)

    handler = pick_handler(src, dest, module)

    res_args = dict(handler=handler.__class__.__name__, dest=dest, src=src)

    # do we need to do unpack?
    res_args['check_results'] = handler.is_unarchived()
    if res_args['check_results']['unarchived']:
        res_args['changed'] = False
        module.exit_json(**res_args)

    # do the unpack
    try:
        res_args['extract_results'] = handler.unarchive()
        if res_args['extract_results']['rc'] != 0:
            module.fail_json(msg="failed to unpack %s to %s" % (src, dest), **res_args)
    except IOError:
        module.fail_json(msg="failed to unpack %s to %s" % (src, dest))

    res_args['changed'] = True

    module.exit_json(**res_args)

# import module snippets
from ansible.module_utils.basic import *
main()
