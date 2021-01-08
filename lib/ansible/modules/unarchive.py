#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2013, Dylan Martin <dmartin@seattlecentral.edu>
# Copyright: (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
# Copyright: (c) 2016, Dag Wieers <dag@wieers.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: unarchive
version_added: '1.4'
short_description: Unpacks an archive after (optionally) copying it from the local machine
description:
     - The C(unarchive) module unpacks an archive. It will not unpack a compressed file that does not contain an archive.
     - By default, it will copy the source file from the local system to the target before unpacking.
     - Set C(remote_src=yes) to unpack an archive which already exists on the target.
     - If checksum validation is desired, use M(ansible.builtin.get_url) or M(ansible.builtin.uri) instead to fetch the file and set C(remote_src=yes).
     - For Windows targets, use the M(community.windows.win_unzip) module instead.
options:
  src:
    description:
      - If C(remote_src=no) (default), local path to archive file to copy to the target server; can be absolute or relative. If C(remote_src=yes), path on the
        target server to existing archive file to unpack.
      - If C(remote_src=yes) and C(src) contains C(://), the remote machine will download the file from the URL first. (version_added 2.0). This is only for
        simple cases, for full download support use the M(ansible.builtin.get_url) module.
    type: path
    required: true
  dest:
    description:
      - Remote absolute path where the archive should be unpacked.
    type: path
    required: true
  copy:
    description:
      - If true, the file is copied from local 'master' to the target machine, otherwise, the plugin will look for src archive at the target machine.
      - This option has been deprecated in favor of C(remote_src).
      - This option is mutually exclusive with C(remote_src).
    type: bool
    default: yes
  creates:
    description:
      - If the specified absolute path (file or directory) already exists, this step will B(not) be run.
    type: path
    version_added: "1.6"
  list_files:
    description:
      - If set to True, return the list of files that are contained in the tarball.
    type: bool
    default: no
    version_added: "2.0"
  exclude:
    description:
      - List the directory and file entries that you would like to exclude from the unarchive action.
    type: list
    version_added: "2.1"
  keep_newer:
    description:
      - Do not replace existing files that are newer than files from the archive.
    type: bool
    default: no
    version_added: "2.1"
  extra_opts:
    description:
      - Specify additional options by passing in an array.
      - Each space-separated command-line option should be a new element of the array. See examples.
      - Command-line options with multiple elements must use multiple lines in the array, one for each element.
    type: list
    default: ""
    version_added: "2.1"
  remote_src:
    description:
      - Set to C(yes) to indicate the archived file is already on the remote system and not local to the Ansible controller.
      - This option is mutually exclusive with C(copy).
    type: bool
    default: no
    version_added: "2.2"
  validate_certs:
    description:
      - This only applies if using a https URL as the source of the file.
      - This should only set to C(no) used on personally controlled sites using self-signed certificate.
      - Prior to 2.2 the code worked as if this was set to C(yes).
    type: bool
    default: yes
    version_added: "2.2"
extends_documentation_fragment:
- decrypt
- files
todo:
    - Re-implement tar support using native tarfile module.
    - Re-implement zip support using native zipfile module.
notes:
    - Requires C(zipinfo) and C(gtar)/C(unzip) command on target host.
    - Can handle I(.zip) files using C(unzip) as well as I(.tar), I(.tar.gz), I(.tar.bz2) and I(.tar.xz) files using C(gtar).
    - Does not handle I(.gz) files, I(.bz2) files or I(.xz) files that do not contain a I(.tar) archive.
    - Uses gtar's C(--diff) arg to calculate if changed or not. If this C(arg) is not
      supported, it will always unpack the archive.
    - Existing files/directories in the destination which are not in the archive
      are not touched. This is the same behavior as a normal archive extraction.
    - Existing files/directories in the destination which are not in the archive
      are ignored for purposes of deciding if the archive should be unpacked or not.
    - Supports C(check_mode).
seealso:
- module: community.general.archive
- module: community.general.iso_extract
- module: community.windows.win_unzip
author: Michael DeHaan
'''

EXAMPLES = r'''
- name: Extract foo.tgz into /var/lib/foo
  ansible.builtin.unarchive:
    src: foo.tgz
    dest: /var/lib/foo

- name: Unarchive a file that is already on the remote machine
  ansible.builtin.unarchive:
    src: /tmp/foo.zip
    dest: /usr/local/bin
    remote_src: yes

- name: Unarchive a file that needs to be downloaded (added in 2.0)
  ansible.builtin.unarchive:
    src: https://example.com/example.zip
    dest: /usr/local/bin
    remote_src: yes

- name: Unarchive a file with extra options
  ansible.builtin.unarchive:
    src: /tmp/foo.zip
    dest: /usr/local/bin
    extra_opts:
    - --transform
    - s/^xxx/yyy/
'''

import binascii
import codecs
import datetime
import fnmatch
import grp
import os
import platform
import pwd
import re
import stat
import time
import traceback
from zipfile import ZipFile, BadZipfile

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_file
from ansible.module_utils._text import to_bytes, to_native, to_text

try:  # python 3.3+
    from shlex import quote
except ImportError:  # older python
    from pipes import quote

# String from tar that shows the tar contents are different from the
# filesystem
OWNER_DIFF_RE = re.compile(r': Uid differs$')
GROUP_DIFF_RE = re.compile(r': Gid differs$')
MODE_DIFF_RE = re.compile(r': Mode differs$')
MOD_TIME_DIFF_RE = re.compile(r': Mod time differs$')
# NEWER_DIFF_RE = re.compile(r' is newer or same age.$')
EMPTY_FILE_RE = re.compile(r': : Warning: Cannot stat: No such file or directory$')
MISSING_FILE_RE = re.compile(r': Warning: Cannot stat: No such file or directory$')
ZIP_FILE_MODE_RE = re.compile(r'([r-][w-][SsTtx-]){3}')
INVALID_OWNER_RE = re.compile(r': Invalid owner')
INVALID_GROUP_RE = re.compile(r': Invalid group')


def crc32(path):
    ''' Return a CRC32 checksum of a file '''
    with open(path, 'rb') as f:
        file_content = f.read()
    return binascii.crc32(file_content) & 0xffffffff


def shell_escape(string):
    ''' Quote meta-characters in the args for the unix shell '''
    return re.sub(r'([^A-Za-z0-9_])', r'\\\1', string)


class UnarchiveError(Exception):
    pass


class ZipArchive(object):

    def __init__(self, src, b_dest, file_args, module):
        self.src = src
        self.b_dest = b_dest
        self.file_args = file_args
        self.opts = module.params['extra_opts']
        self.module = module
        self.excludes = module.params['exclude']
        self.includes = []
        self.cmd_path = self.module.get_bin_path('unzip')
        self.zipinfocmd_path = self.module.get_bin_path('zipinfo')
        self._files_in_archive = []
        self._infodict = dict()

    def _permstr_to_octal(self, modestr, umask):
        ''' Convert a Unix permission string (rw-r--r--) into a mode (0644) '''
        revstr = modestr[::-1]
        mode = 0
        for j in range(0, 3):
            for i in range(0, 3):
                if revstr[i + 3 * j] in ['r', 'w', 'x', 's', 't']:
                    mode += 2 ** (i + 3 * j)
        # The unzip utility does not support setting the stST bits
#                if revstr[i + 3 * j] in ['s', 't', 'S', 'T' ]:
#                    mode += 2 ** (9 + j)
        return (mode & ~umask)

    def _legacy_file_list(self):
        unzip_bin = self.module.get_bin_path('unzip')
        if not unzip_bin:
            raise UnarchiveError('Python Zipfile cannot read %s and unzip not found' % self.src)

        rc, out, err = self.module.run_command([unzip_bin, '-v', self.src])
        if rc:
            raise UnarchiveError('Neither python zipfile nor unzip can read %s' % self.src)

        for line in out.splitlines()[3:-2]:
            fields = line.split(None, 7)
            self._files_in_archive.append(fields[7])
            self._infodict[fields[7]] = int(fields[6])

    def _crc32(self, path):
        if self._infodict:
            return self._infodict[path]

        try:
            archive = ZipFile(self.src)
        except BadZipfile as e:
            if e.args[0].lower().startswith('bad magic number'):
                # Python2.4 can't handle zipfiles with > 64K files.  Try using
                # /usr/bin/unzip instead
                self._legacy_file_list()
            else:
                raise
        else:
            try:
                for item in archive.infolist():
                    self._infodict[item.filename] = int(item.CRC)
            except Exception:
                archive.close()
                raise UnarchiveError('Unable to list files in the archive')

        return self._infodict[path]

    @property
    def files_in_archive(self):
        if self._files_in_archive:
            return self._files_in_archive

        self._files_in_archive = []
        try:
            archive = ZipFile(self.src)
        except BadZipfile as e:
            if e.args[0].lower().startswith('bad magic number'):
                # Python2.4 can't handle zipfiles with > 64K files.  Try using
                # /usr/bin/unzip instead
                self._legacy_file_list()
            else:
                raise
        else:
            try:
                for member in archive.namelist():
                    exclude_flag = False
                    if self.excludes:
                        for exclude in self.excludes:
                            if fnmatch.fnmatch(member, exclude):
                                exclude_flag = True
                                break
                    if not exclude_flag:
                        self._files_in_archive.append(to_native(member))
            except Exception:
                archive.close()
                raise UnarchiveError('Unable to list files in the archive')

            archive.close()
        return self._files_in_archive

    def is_unarchived(self):
        # BSD unzip doesn't support zipinfo listings with timestamp.
        cmd = [self.zipinfocmd_path, '-T', '-s', self.src]
        if self.excludes:
            cmd.extend(['-x', ] + self.excludes)
        rc, out, err = self.module.run_command(cmd)

        old_out = out
        diff = ''
        out = ''
        if rc == 0:
            unarchived = True
        else:
            unarchived = False

        # Get some information related to user/group ownership
        umask = os.umask(0)
        os.umask(umask)
        systemtype = platform.system()

        # Get current user and group information
        groups = os.getgroups()
        run_uid = os.getuid()
        run_gid = os.getgid()
        try:
            run_owner = pwd.getpwuid(run_uid).pw_name
        except (TypeError, KeyError):
            run_owner = run_uid
        try:
            run_group = grp.getgrgid(run_gid).gr_name
        except (KeyError, ValueError, OverflowError):
            run_group = run_gid

        # Get future user ownership
        fut_owner = fut_uid = None
        if self.file_args['owner']:
            try:
                tpw = pwd.getpwnam(self.file_args['owner'])
            except KeyError:
                try:
                    tpw = pwd.getpwuid(self.file_args['owner'])
                except (TypeError, KeyError):
                    tpw = pwd.getpwuid(run_uid)
            fut_owner = tpw.pw_name
            fut_uid = tpw.pw_uid
        else:
            try:
                fut_owner = run_owner
            except Exception:
                pass
            fut_uid = run_uid

        # Get future group ownership
        fut_group = fut_gid = None
        if self.file_args['group']:
            try:
                tgr = grp.getgrnam(self.file_args['group'])
            except (ValueError, KeyError):
                try:
                    tgr = grp.getgrgid(self.file_args['group'])
                except (KeyError, ValueError, OverflowError):
                    tgr = grp.getgrgid(run_gid)
            fut_group = tgr.gr_name
            fut_gid = tgr.gr_gid
        else:
            try:
                fut_group = run_group
            except Exception:
                pass
            fut_gid = run_gid

        for line in old_out.splitlines():
            change = False

            pcs = line.split(None, 7)
            if len(pcs) != 8:
                # Too few fields... probably a piece of the header or footer
                continue

            # Check first and seventh field in order to skip header/footer
            if len(pcs[0]) != 7 and len(pcs[0]) != 10:
                continue
            if len(pcs[6]) != 15:
                continue

            # Possible entries:
            #   -rw-rws---  1.9 unx    2802 t- defX 11-Aug-91 13:48 perms.2660
            #   -rw-a--     1.0 hpf    5358 Tl i4:3  4-Dec-91 11:33 longfilename.hpfs
            #   -r--ahs     1.1 fat    4096 b- i4:2 14-Jul-91 12:58 EA DATA. SF
            #   --w-------  1.0 mac   17357 bx i8:2  4-May-92 04:02 unzip.macr
            if pcs[0][0] not in 'dl-?' or not frozenset(pcs[0][1:]).issubset('rwxstah-'):
                continue

            ztype = pcs[0][0]
            permstr = pcs[0][1:]
            version = pcs[1]
            ostype = pcs[2]
            size = int(pcs[3])
            path = to_text(pcs[7], errors='surrogate_or_strict')

            # Skip excluded files
            if path in self.excludes:
                out += 'Path %s is excluded on request\n' % path
                continue

            # Itemized change requires L for symlink
            if path[-1] == '/':
                if ztype != 'd':
                    err += 'Path %s incorrectly tagged as "%s", but is a directory.\n' % (path, ztype)
                ftype = 'd'
            elif ztype == 'l':
                ftype = 'L'
            elif ztype == '-':
                ftype = 'f'
            elif ztype == '?':
                ftype = 'f'

            # Some files may be storing FAT permissions, not Unix permissions
            # For FAT permissions, we will use a base permissions set of 777 if the item is a directory or has the execute bit set.  Otherwise, 666.
            #     This permission will then be modified by the system UMask.
            # BSD always applies the Umask, even to Unix permissions.
            # For Unix style permissions on Linux or Mac, we want to use them directly.
            #     So we set the UMask for this file to zero.  That permission set will then be unchanged when calling _permstr_to_octal

            if len(permstr) == 6:
                if path[-1] == '/':
                    permstr = 'rwxrwxrwx'
                elif permstr == 'rwx---':
                    permstr = 'rwxrwxrwx'
                else:
                    permstr = 'rw-rw-rw-'
                file_umask = umask
            elif 'bsd' in systemtype.lower():
                file_umask = umask
            else:
                file_umask = 0

            # Test string conformity
            if len(permstr) != 9 or not ZIP_FILE_MODE_RE.match(permstr):
                raise UnarchiveError('ZIP info perm format incorrect, %s' % permstr)

            # DEBUG
#            err += "%s%s %10d %s\n" % (ztype, permstr, size, path)

            b_dest = os.path.join(self.b_dest, to_bytes(path, errors='surrogate_or_strict'))
            try:
                st = os.lstat(b_dest)
            except Exception:
                change = True
                self.includes.append(path)
                err += 'Path %s is missing\n' % path
                diff += '>%s++++++.?? %s\n' % (ftype, path)
                continue

            # Compare file types
            if ftype == 'd' and not stat.S_ISDIR(st.st_mode):
                change = True
                self.includes.append(path)
                err += 'File %s already exists, but not as a directory\n' % path
                diff += 'c%s++++++.?? %s\n' % (ftype, path)
                continue

            if ftype == 'f' and not stat.S_ISREG(st.st_mode):
                change = True
                unarchived = False
                self.includes.append(path)
                err += 'Directory %s already exists, but not as a regular file\n' % path
                diff += 'c%s++++++.?? %s\n' % (ftype, path)
                continue

            if ftype == 'L' and not stat.S_ISLNK(st.st_mode):
                change = True
                self.includes.append(path)
                err += 'Directory %s already exists, but not as a symlink\n' % path
                diff += 'c%s++++++.?? %s\n' % (ftype, path)
                continue

            itemized = list('.%s.......??' % ftype)

            # Note: this timestamp calculation has a rounding error
            # somewhere... unzip and this timestamp can be one second off
            # When that happens, we report a change and re-unzip the file
            dt_object = datetime.datetime(*(time.strptime(pcs[6], '%Y%m%d.%H%M%S')[0:6]))
            timestamp = time.mktime(dt_object.timetuple())

            # Compare file timestamps
            if stat.S_ISREG(st.st_mode):
                if self.module.params['keep_newer']:
                    if timestamp > st.st_mtime:
                        change = True
                        self.includes.append(path)
                        err += 'File %s is older, replacing file\n' % path
                        itemized[4] = 't'
                    elif stat.S_ISREG(st.st_mode) and timestamp < st.st_mtime:
                        # Add to excluded files, ignore other changes
                        out += 'File %s is newer, excluding file\n' % path
                        self.excludes.append(path)
                        continue
                else:
                    if timestamp != st.st_mtime:
                        change = True
                        self.includes.append(path)
                        err += 'File %s differs in mtime (%f vs %f)\n' % (path, timestamp, st.st_mtime)
                        itemized[4] = 't'

            # Compare file sizes
            if stat.S_ISREG(st.st_mode) and size != st.st_size:
                change = True
                err += 'File %s differs in size (%d vs %d)\n' % (path, size, st.st_size)
                itemized[3] = 's'

            # Compare file checksums
            if stat.S_ISREG(st.st_mode):
                crc = crc32(b_dest)
                if crc != self._crc32(path):
                    change = True
                    err += 'File %s differs in CRC32 checksum (0x%08x vs 0x%08x)\n' % (path, self._crc32(path), crc)
                    itemized[2] = 'c'

            # Compare file permissions

            # Do not handle permissions of symlinks
            if ftype != 'L':

                # Use the new mode provided with the action, if there is one
                if self.file_args['mode']:
                    if isinstance(self.file_args['mode'], int):
                        mode = self.file_args['mode']
                    else:
                        try:
                            mode = int(self.file_args['mode'], 8)
                        except Exception as e:
                            try:
                                mode = AnsibleModule._symbolic_mode_to_octal(st, self.file_args['mode'])
                            except ValueError as e:
                                self.module.fail_json(path=path, msg="%s" % to_native(e), exception=traceback.format_exc())
                # Only special files require no umask-handling
                elif ztype == '?':
                    mode = self._permstr_to_octal(permstr, 0)
                else:
                    mode = self._permstr_to_octal(permstr, file_umask)

                if mode != stat.S_IMODE(st.st_mode):
                    change = True
                    itemized[5] = 'p'
                    err += 'Path %s differs in permissions (%o vs %o)\n' % (path, mode, stat.S_IMODE(st.st_mode))

            # Compare file user ownership
            owner = uid = None
            try:
                owner = pwd.getpwuid(st.st_uid).pw_name
            except (TypeError, KeyError):
                uid = st.st_uid

            # If we are not root and requested owner is not our user, fail
            if run_uid != 0 and (fut_owner != run_owner or fut_uid != run_uid):
                raise UnarchiveError('Cannot change ownership of %s to %s, as user %s' % (path, fut_owner, run_owner))

            if owner and owner != fut_owner:
                change = True
                err += 'Path %s is owned by user %s, not by user %s as expected\n' % (path, owner, fut_owner)
                itemized[6] = 'o'
            elif uid and uid != fut_uid:
                change = True
                err += 'Path %s is owned by uid %s, not by uid %s as expected\n' % (path, uid, fut_uid)
                itemized[6] = 'o'

            # Compare file group ownership
            group = gid = None
            try:
                group = grp.getgrgid(st.st_gid).gr_name
            except (KeyError, ValueError, OverflowError):
                gid = st.st_gid

            if run_uid != 0 and (fut_group != run_group or fut_gid != run_gid) and fut_gid not in groups:
                raise UnarchiveError('Cannot change group ownership of %s to %s, as user %s' % (path, fut_group, run_owner))

            if group and group != fut_group:
                change = True
                err += 'Path %s is owned by group %s, not by group %s as expected\n' % (path, group, fut_group)
                itemized[6] = 'g'
            elif gid and gid != fut_gid:
                change = True
                err += 'Path %s is owned by gid %s, not by gid %s as expected\n' % (path, gid, fut_gid)
                itemized[6] = 'g'

            # Register changed files and finalize diff output
            if change:
                if path not in self.includes:
                    self.includes.append(path)
                diff += '%s %s\n' % (''.join(itemized), path)

        if self.includes:
            unarchived = False

        # DEBUG
#        out = old_out + out

        return dict(unarchived=unarchived, rc=rc, out=out, err=err, cmd=cmd, diff=diff)

    def unarchive(self):
        cmd = [self.cmd_path, '-o']
        if self.opts:
            cmd.extend(self.opts)
        cmd.append(self.src)
        # NOTE: Including (changed) files as arguments is problematic (limits on command line/arguments)
        # if self.includes:
        # NOTE: Command unzip has this strange behaviour where it expects quoted filenames to also be escaped
        # cmd.extend(map(shell_escape, self.includes))
        if self.excludes:
            cmd.extend(['-x'] + self.excludes)
        cmd.extend(['-d', self.b_dest])
        rc, out, err = self.module.run_command(cmd)
        return dict(cmd=cmd, rc=rc, out=out, err=err)

    def can_handle_archive(self):
        if not self.cmd_path:
            return False, 'Command "unzip" not found.'
        cmd = [self.cmd_path, '-l', self.src]
        rc, out, err = self.module.run_command(cmd)
        if rc == 0:
            return True, None
        return False, 'Command "%s" could not handle archive.' % self.cmd_path


class TgzArchive(object):

    def __init__(self, src, b_dest, file_args, module):
        self.src = src
        self.b_dest = b_dest
        self.file_args = file_args
        self.opts = module.params['extra_opts']
        self.module = module
        if self.module.check_mode:
            self.module.exit_json(skipped=True, msg="remote module (%s) does not support check mode when using gtar" % self.module._name)
        self.excludes = [path.rstrip('/') for path in self.module.params['exclude']]
        # Prefer gtar (GNU tar) as it supports the compression options -z, -j and -J
        self.cmd_path = self.module.get_bin_path('gtar', None)
        if not self.cmd_path:
            # Fallback to tar
            self.cmd_path = self.module.get_bin_path('tar')
        self.zipflag = '-z'
        self._files_in_archive = []

        if self.cmd_path:
            self.tar_type = self._get_tar_type()
        else:
            self.tar_type = None

    def _get_tar_type(self):
        cmd = [self.cmd_path, '--version']
        (rc, out, err) = self.module.run_command(cmd)
        tar_type = None
        if out.startswith('bsdtar'):
            tar_type = 'bsd'
        elif out.startswith('tar') and 'GNU' in out:
            tar_type = 'gnu'
        return tar_type

    @property
    def files_in_archive(self):
        if self._files_in_archive:
            return self._files_in_archive

        cmd = [self.cmd_path, '--list', '-C', self.b_dest]
        if self.zipflag:
            cmd.append(self.zipflag)
        if self.opts:
            cmd.extend(['--show-transformed-names'] + self.opts)
        if self.excludes:
            cmd.extend(['--exclude=' + f for f in self.excludes])
        cmd.extend(['-f', self.src])
        rc, out, err = self.module.run_command(cmd, cwd=self.b_dest, environ_update=dict(LANG='C', LC_ALL='C', LC_MESSAGES='C'))

        if rc != 0:
            raise UnarchiveError('Unable to list files in the archive')

        for filename in out.splitlines():
            # Compensate for locale-related problems in gtar output (octal unicode representation) #11348
            # filename = filename.decode('string_escape')
            filename = to_native(codecs.escape_decode(filename)[0])

            # We don't allow absolute filenames.  If the user wants to unarchive rooted in "/"
            # they need to use "dest: '/'".  This follows the defaults for gtar, pax, etc.
            # Allowing absolute filenames here also causes bugs: https://github.com/ansible/ansible/issues/21397
            if filename.startswith('/'):
                filename = filename[1:]

            exclude_flag = False
            if self.excludes:
                for exclude in self.excludes:
                    if fnmatch.fnmatch(filename, exclude):
                        exclude_flag = True
                        break

            if not exclude_flag:
                self._files_in_archive.append(to_native(filename))

        return self._files_in_archive

    def is_unarchived(self):
        cmd = [self.cmd_path, '--diff', '-C', self.b_dest]
        if self.zipflag:
            cmd.append(self.zipflag)
        if self.opts:
            cmd.extend(['--show-transformed-names'] + self.opts)
        if self.file_args['owner']:
            cmd.append('--owner=' + quote(self.file_args['owner']))
        if self.file_args['group']:
            cmd.append('--group=' + quote(self.file_args['group']))
        if self.module.params['keep_newer']:
            cmd.append('--keep-newer-files')
        if self.excludes:
            cmd.extend(['--exclude=' + f for f in self.excludes])
        cmd.extend(['-f', self.src])
        rc, out, err = self.module.run_command(cmd, cwd=self.b_dest, environ_update=dict(LANG='C', LC_ALL='C', LC_MESSAGES='C'))

        # Check whether the differences are in something that we're
        # setting anyway

        # What is different
        unarchived = True
        old_out = out
        out = ''
        run_uid = os.getuid()
        # When unarchiving as a user, or when owner/group/mode is supplied --diff is insufficient
        # Only way to be sure is to check request with what is on disk (as we do for zip)
        # Leave this up to set_fs_attributes_if_different() instead of inducing a (false) change
        for line in old_out.splitlines() + err.splitlines():
            # FIXME: Remove the bogus lines from error-output as well !
            # Ignore bogus errors on empty filenames (when using --split-component)
            if EMPTY_FILE_RE.search(line):
                continue
            if run_uid == 0 and not self.file_args['owner'] and OWNER_DIFF_RE.search(line):
                out += line + '\n'
            if run_uid == 0 and not self.file_args['group'] and GROUP_DIFF_RE.search(line):
                out += line + '\n'
            if not self.file_args['mode'] and MODE_DIFF_RE.search(line):
                out += line + '\n'
            if MOD_TIME_DIFF_RE.search(line):
                out += line + '\n'
            if MISSING_FILE_RE.search(line):
                out += line + '\n'
            if INVALID_OWNER_RE.search(line):
                out += line + '\n'
            if INVALID_GROUP_RE.search(line):
                out += line + '\n'
        if out:
            unarchived = False
        return dict(unarchived=unarchived, rc=rc, out=out, err=err, cmd=cmd)

    def unarchive(self):
        cmd = [self.cmd_path, '--extract', '-C', self.b_dest]
        if self.zipflag:
            cmd.append(self.zipflag)
        if self.opts:
            cmd.extend(['--show-transformed-names'] + self.opts)
        if self.file_args['owner']:
            cmd.append('--owner=' + quote(self.file_args['owner']))
        if self.file_args['group']:
            cmd.append('--group=' + quote(self.file_args['group']))
        if self.module.params['keep_newer']:
            cmd.append('--keep-newer-files')
        if self.excludes:
            cmd.extend(['--exclude=' + f for f in self.excludes])
        cmd.extend(['-f', self.src])
        rc, out, err = self.module.run_command(cmd, cwd=self.b_dest, environ_update=dict(LANG='C', LC_ALL='C', LC_MESSAGES='C'))
        return dict(cmd=cmd, rc=rc, out=out, err=err)

    def can_handle_archive(self):
        if not self.cmd_path:
            return False, 'Commands "gtar" and "tar" not found.'

        if self.tar_type != 'gnu':
            return False, 'Command "%s" detected as tar type %s. GNU tar required.' % (self.cmd_path, self.tar_type)

        try:
            if self.files_in_archive:
                return True, None
        except UnarchiveError:
            return False, 'Command "%s" could not handle archive.' % self.cmd_path
        # Errors and no files in archive assume that we weren't able to
        # properly unarchive it
        return False, 'Command "%s" found no files in archive. Empty archive files are not supported.' % self.cmd_path


# Class to handle tar files that aren't compressed
class TarArchive(TgzArchive):
    def __init__(self, src, b_dest, file_args, module):
        super(TarArchive, self).__init__(src, b_dest, file_args, module)
        # argument to tar
        self.zipflag = ''


# Class to handle bzip2 compressed tar files
class TarBzipArchive(TgzArchive):
    def __init__(self, src, b_dest, file_args, module):
        super(TarBzipArchive, self).__init__(src, b_dest, file_args, module)
        self.zipflag = '-j'


# Class to handle xz compressed tar files
class TarXzArchive(TgzArchive):
    def __init__(self, src, b_dest, file_args, module):
        super(TarXzArchive, self).__init__(src, b_dest, file_args, module)
        self.zipflag = '-J'


# try handlers in order and return the one that works or bail if none work
def pick_handler(src, dest, file_args, module):
    handlers = [ZipArchive, TgzArchive, TarArchive, TarBzipArchive, TarXzArchive]
    reasons = set()
    for handler in handlers:
        obj = handler(src, dest, file_args, module)
        (can_handle, reason) = obj.can_handle_archive()
        if can_handle:
            return obj
        reasons.add(reason)
    reason_msg = ' '.join(reasons)
    module.fail_json(msg='Failed to find handler for "%s". Make sure the required command to extract the file is installed. %s' % (src, reason_msg))


def main():
    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec=dict(
            src=dict(type='path', required=True),
            dest=dict(type='path', required=True),
            remote_src=dict(type='bool', default=False),
            creates=dict(type='path'),
            list_files=dict(type='bool', default=False),
            keep_newer=dict(type='bool', default=False),
            exclude=dict(type='list', default=[]),
            extra_opts=dict(type='list', default=[]),
            validate_certs=dict(type='bool', default=True),
        ),
        add_file_common_args=True,
        # check-mode only works for zip files, we cover that later
        supports_check_mode=True,
    )

    src = module.params['src']
    dest = module.params['dest']
    b_dest = to_bytes(dest, errors='surrogate_or_strict')
    remote_src = module.params['remote_src']
    file_args = module.load_file_common_arguments(module.params)

    # did tar file arrive?
    if not os.path.exists(src):
        if not remote_src:
            module.fail_json(msg="Source '%s' failed to transfer" % src)
        # If remote_src=true, and src= contains ://, try and download the file to a temp directory.
        elif '://' in src:
            src = fetch_file(module, src)
        else:
            module.fail_json(msg="Source '%s' does not exist" % src)
    if not os.access(src, os.R_OK):
        module.fail_json(msg="Source '%s' not readable" % src)

    # skip working with 0 size archives
    try:
        if os.path.getsize(src) == 0:
            module.fail_json(msg="Invalid archive '%s', the file is 0 bytes" % src)
    except Exception as e:
        module.fail_json(msg="Source '%s' not readable, %s" % (src, to_native(e)))

    # is dest OK to receive tar file?
    if not os.path.isdir(b_dest):
        module.fail_json(msg="Destination '%s' is not a directory" % dest)

    handler = pick_handler(src, b_dest, file_args, module)

    res_args = dict(handler=handler.__class__.__name__, dest=dest, src=src)

    # do we need to do unpack?
    check_results = handler.is_unarchived()

    # DEBUG
    # res_args['check_results'] = check_results

    if module.check_mode:
        res_args['changed'] = not check_results['unarchived']
    elif check_results['unarchived']:
        res_args['changed'] = False
    else:
        # do the unpack
        try:
            res_args['extract_results'] = handler.unarchive()
            if res_args['extract_results']['rc'] != 0:
                module.fail_json(msg="failed to unpack %s to %s" % (src, dest), **res_args)
        except IOError:
            module.fail_json(msg="failed to unpack %s to %s" % (src, dest), **res_args)
        else:
            res_args['changed'] = True

    # Get diff if required
    if check_results.get('diff', False):
        res_args['diff'] = {'prepared': check_results['diff']}

    # Run only if we found differences (idempotence) or diff was missing
    if res_args.get('diff', True) and not module.check_mode:
        # do we need to change perms?
        for filename in handler.files_in_archive:
            file_args['path'] = os.path.join(b_dest, to_bytes(filename, errors='surrogate_or_strict'))

            try:
                res_args['changed'] = module.set_fs_attributes_if_different(file_args, res_args['changed'], expand=False)
            except (IOError, OSError) as e:
                module.fail_json(msg="Unexpected error when accessing exploded file: %s" % to_native(e), **res_args)

    if module.params['list_files']:
        res_args['files'] = handler.files_in_archive

    module.exit_json(**res_args)


if __name__ == '__main__':
    main()
