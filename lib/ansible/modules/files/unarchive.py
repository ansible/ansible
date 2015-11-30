#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2013, Dylan Martin <dmartin@seattlecentral.edu>
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
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
short_description: Unpacks an archive after (optionally) copying it from the local machine.
extends_documentation_fragment: files
description:
     - The M(unarchive) module unpacks an archive. By default, it will copy the source file from the local system to the target before unpacking - set copy=no to unpack an archive which already exists on the target..
options:
  src:
    description:
      - If copy=yes (default), local path to archive file to copy to the target server; can be absolute or relative. If copy=no, path on the target server to existing archive file to unpack.
      - If copy=no and src contains ://, the remote machine will download the file from the url first. (version_added 2.0)
    required: true
    default: null
  dest:
    description:
      - Remote absolute path where the archive should be unpacked
    required: true
    default: null
  copy:
    description:
      - "If true, the file is copied from local 'master' to the target machine, otherwise, the plugin will look for src archive at the target machine."
    required: false
    choices: [ "yes", "no" ]
    default: "yes"
  creates:
    description:
      - a filename, when it already exists, this step will B(not) be run.
    required: no
    default: null
    version_added: "1.6"
  list_files:
    description:
      - If set to True, return the list of files that are contained in the tarball.
    required: false
    choices: [ "yes", "no" ]
    default: "no"
    version_added: "2.0"
author: "Dylan Martin (@pileofrogs)"
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

# Unarchive a file that needs to be downloaded (added in 2.0)
- unarchive: src=https://example.com/example.zip dest=/usr/local/bin copy=no
'''

import re
import os
from zipfile import ZipFile

# String from tar that shows the tar contents are different from the
# filesystem
DIFFERENCE_RE = re.compile(r': (.*) differs$')
# When downloading an archive, how much of the archive to download before
# saving to a tempfile (64k)
BUFSIZE = 65536

class UnarchiveError(Exception):
    pass

# class to handle .zip files
class ZipArchive(object):

    def __init__(self, src, dest, module):
        self.src = src
        self.dest = dest
        self.module = module
        self.cmd_path = self.module.get_bin_path('unzip')
        self._files_in_archive = []

    @property
    def files_in_archive(self, force_refresh=False):
        if self._files_in_archive and not force_refresh:
            return self._files_in_archive

        archive = ZipFile(self.src)
        try:
            self._files_in_archive = archive.namelist()
        except:
            raise UnarchiveError('Unable to list files in the archive')

        return self._files_in_archive

    def is_unarchived(self, mode, owner, group):
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
class TgzArchive(object):

    def __init__(self, src, dest, module):
        self.src = src
        self.dest = dest
        self.module = module
        # Prefer gtar (GNU tar) as it supports the compression options -zjJ
        self.cmd_path = self.module.get_bin_path('gtar', None)
        if not self.cmd_path:
            # Fallback to tar
            self.cmd_path = self.module.get_bin_path('tar')
        self.zipflag = 'z'
        self._files_in_archive = []

    @property
    def files_in_archive(self, force_refresh=False):
        if self._files_in_archive and not force_refresh:
            return self._files_in_archive

        cmd = '%s -t%sf "%s"' % (self.cmd_path, self.zipflag, self.src)
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            raise UnarchiveError('Unable to list files in the archive')

        for filename in out.splitlines():
            if filename:
                self._files_in_archive.append(filename)
        return self._files_in_archive

    def is_unarchived(self, mode, owner, group):
        cmd = '%s -C "%s" --diff -%sf "%s"' % (self.cmd_path, self.dest, self.zipflag, self.src)
        rc, out, err = self.module.run_command(cmd)
        unarchived = (rc == 0)
        if not unarchived:
            # Check whether the differences are in something that we're
            # setting anyway

            # What will be set
            to_be_set = set()
            for perm in (('Mode', mode), ('Gid', group), ('Uid', owner)):
                if perm[1] is not None:
                    to_be_set.add(perm[0])

            # What is different
            changes = set()
            if err:
                # Assume changes if anything returned on stderr
                # * Missing files are known to trigger this
                return dict(unarchived=unarchived, rc=rc, out=out, err=err, cmd=cmd)
            for line in out.splitlines():
                match = DIFFERENCE_RE.search(line)
                if not match:
                    # Unknown tar output. Assume we have changes
                    return dict(unarchived=unarchived, rc=rc, out=out, err=err, cmd=cmd)
                changes.add(match.groups()[0])

            if changes and changes.issubset(to_be_set):
                unarchived = True
        return dict(unarchived=unarchived, rc=rc, out=out, err=err, cmd=cmd)

    def unarchive(self):
        cmd = '%s -x%sf "%s"' % (self.cmd_path, self.zipflag, self.src)
        rc, out, err = self.module.run_command(cmd, cwd=self.dest)
        return dict(cmd=cmd, rc=rc, out=out, err=err)

    def can_handle_archive(self):
        if not self.cmd_path:
            return False

        try:
            if self.files_in_archive:
                return True
        except UnarchiveError:
            pass
        # Errors and no files in archive assume that we weren't able to
        # properly unarchive it
        return False


# class to handle tar files that aren't compressed
class TarArchive(TgzArchive):
    def __init__(self, src, dest, module):
        super(TarArchive, self).__init__(src, dest, module)
        self.zipflag = ''


# class to handle bzip2 compressed tar files
class TarBzipArchive(TgzArchive):
    def __init__(self, src, dest, module):
        super(TarBzipArchive, self).__init__(src, dest, module)
        self.zipflag = 'j'


# class to handle xz compressed tar files
class TarXzArchive(TgzArchive):
    def __init__(self, src, dest, module):
        super(TarXzArchive, self).__init__(src, dest, module)
        self.zipflag = 'J'


# try handlers in order and return the one that works or bail if none work
def pick_handler(src, dest, module):
    handlers = [TgzArchive, ZipArchive, TarArchive, TarBzipArchive, TarXzArchive]
    for handler in handlers:
        obj = handler(src, dest, module)
        if obj.can_handle_archive():
            return obj
    module.fail_json(msg='Failed to find handler for "%s". Make sure the required command to extract the file is installed.' % src)


def main():
    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec = dict(
            src               = dict(required=True),
            original_basename = dict(required=False), # used to handle 'dest is a directory' via template, a slight hack
            dest              = dict(required=True),
            copy              = dict(default=True, type='bool'),
            creates           = dict(required=False),
            list_files          = dict(required=False, default=False, type='bool'),
        ),
        add_file_common_args=True,
    )

    src    = os.path.expanduser(module.params['src'])
    dest   = os.path.expanduser(module.params['dest'])
    copy   = module.params['copy']
    file_args = module.load_file_common_arguments(module.params)

    # did tar file arrive?
    if not os.path.exists(src):
        if copy:
            module.fail_json(msg="Source '%s' failed to transfer" % src)
        # If copy=false, and src= contains ://, try and download the file to a temp directory.
        elif '://' in src:
            tempdir = os.path.dirname(__file__)
            package = os.path.join(tempdir, str(src.rsplit('/', 1)[1]))
            try:
                rsp, info = fetch_url(module, src)
                f = open(package, 'w')
                # Read 1kb at a time to save on ram
                while True:
                    data = rsp.read(BUFSIZE)

                    if data == "":
                        break # End of file, break while loop

                    f.write(data)
                f.close()
                src = package
            except Exception, e:
                module.fail_json(msg="Failure downloading %s, %s" % (src, e))
        else:
            module.fail_json(msg="Source '%s' does not exist" % src)
    if not os.access(src, os.R_OK):
        module.fail_json(msg="Source '%s' not readable" % src)

    # skip working with 0 size archives
    try:
        if os.path.getsize(src) == 0:
            module.fail_json(msg="Invalid archive '%s', the file is 0 bytes" % src)
    except Exception, e:
        module.fail_json(msg="Source '%s' not readable" % src)

    # is dest OK to receive tar file?
    if not os.path.isdir(dest):
        module.fail_json(msg="Destination '%s' is not a directory" % dest)

    handler = pick_handler(src, dest, module)

    res_args = dict(handler=handler.__class__.__name__, dest=dest, src=src)

    # do we need to do unpack?
    res_args['check_results'] = handler.is_unarchived(file_args['mode'],
            file_args['owner'], file_args['group'])
    if res_args['check_results']['unarchived']:
        res_args['changed'] = False
    else:
        # do the unpack
        try:
            res_args['extract_results'] = handler.unarchive()
            if res_args['extract_results']['rc'] != 0:
                module.fail_json(msg="failed to unpack %s to %s" % (src, dest), **res_args)
        except IOError:
            module.fail_json(msg="failed to unpack %s to %s" % (src, dest))
        else:
            res_args['changed'] = True

    # do we need to change perms?
    for filename in handler.files_in_archive:
        file_args['path'] = os.path.join(dest, filename)
        try:
            res_args['changed'] = module.set_fs_attributes_if_different(file_args, res_args['changed'])
        except (IOError, OSError), e:
            module.fail_json(msg="Unexpected error when accessing exploded file: %s" % str(e))

    if module.params['list_files']:
        res_args['files'] = handler.files_in_archive

    module.exit_json(**res_args)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
if __name__ == '__main__':
    main()
