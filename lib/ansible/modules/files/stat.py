#!/usr/bin/python
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: stat
version_added: "1.3"
short_description: Retrieve file or file system status
description:
     - Retrieves facts for a file similar to the linux/unix 'stat' command.
     - For Windows targets, use the M(win_stat) module instead.
options:
  path:
    description:
      - The full path of the file/object to get the facts of.
    required: true
  follow:
    description:
      - Whether to follow symlinks.
    type: bool
    default: 'no'
  get_md5:
    description:
      - Whether to return the md5 sum of the file.
      - Will return None if not a regular file or if we're
        unable to use md5 (Common for FIPS-140 compliant systems).
      - The default of this option changed from C(yes) to C(no) in Ansible 2.5
        and will be removed altogether in Ansible 2.9.
      - Use C(get_checksum=true) with C(checksum_algorithm=md5) to return an
        md5 hash under the C(checksum) return value.
    type: bool
    default: 'no'
  get_checksum:
    description:
      - Whether to return a checksum of the file (default sha1).
    type: bool
    default: 'yes'
    version_added: "1.8"
  checksum_algorithm:
    description:
      - Algorithm to determine checksum of file. Will throw an error if the
        host is unable to use specified algorithm.
      - The remote host has to support the hashing method specified, C(md5)
        can be unavailable if the host is FIPS-140 compliant.
    choices: [ md5, sha1, sha224, sha256, sha384, sha512 ]
    default: sha1
    aliases: [ checksum, checksum_algo ]
    version_added: "2.0"
  get_mime:
    description:
      - Use file magic and return data about the nature of the file. this uses
        the 'file' utility found on most Linux/Unix systems.
      - This will add both `mime_type` and 'charset' fields to the return, if possible.
      - In 2.3 this option changed from 'mime' to 'get_mime' and the default changed to 'Yes'.
    type: bool
    default: 'yes'
    version_added: "2.1"
    aliases: [ mime, mime_type, mime-type ]
  get_attributes:
    description:
      - Get file attributes using lsattr tool if present.
    type: bool
    default: 'yes'
    version_added: "2.3"
    aliases: [ attr, attributes ]
notes:
     - For Windows targets, use the M(win_stat) module instead.
author: Bruce Pennypacker (@bpennypacker)
'''

EXAMPLES = '''
# Obtain the stats of /etc/foo.conf, and check that the file still belongs
# to 'root'. Fail otherwise.
- stat:
    path: /etc/foo.conf
  register: st
- fail:
    msg: "Whoops! file ownership has changed"
  when: st.stat.pw_name != 'root'

# Determine if a path exists and is a symlink. Note that if the path does
# not exist, and we test sym.stat.islnk, it will fail with an error. So
# therefore, we must test whether it is defined.
# Run this to understand the structure, the skipped ones do not pass the
# check performed by 'when'
- stat:
    path: /path/to/something
  register: sym

- debug:
    msg: "islnk isn't defined (path doesn't exist)"
  when: sym.stat.islnk is not defined

- debug:
    msg: "islnk is defined (path must exist)"
  when: sym.stat.islnk is defined

- debug:
    msg: "Path exists and is a symlink"
  when: sym.stat.islnk is defined and sym.stat.islnk

- debug:
    msg: "Path exists and isn't a symlink"
  when: sym.stat.islnk is defined and sym.stat.islnk == False


# Determine if a path exists and is a directory.  Note that we need to test
# both that p.stat.isdir actually exists, and also that it's set to true.
- stat:
    path: /path/to/something
  register: p
- debug:
    msg: "Path exists and is a directory"
  when: p.stat.isdir is defined and p.stat.isdir

# Don't do md5 checksum
- stat:
    path: /path/to/myhugefile
    get_md5: no

# Use sha256 to calculate checksum
- stat:
    path: /path/to/something
    checksum_algorithm: sha256
'''

RETURN = r'''
stat:
    description: dictionary containing all the stat data, some platforms might add additional fields
    returned: success
    type: complex
    contains:
        exists:
            description: if the destination path actually exists or not
            returned: success
            type: boolean
            sample: True
        path:
            description: The full path of the file/object to get the facts of
            returned: success and if path exists
            type: string
            sample: '/path/to/file'
        mode:
            description: Unix permissions of the file in octal
            returned: success, path exists and user can read stats
            type: octal
            sample: 1755
        isdir:
            description: Tells you if the path is a directory
            returned: success, path exists and user can read stats
            type: boolean
            sample: False
        ischr:
            description: Tells you if the path is a character device
            returned: success, path exists and user can read stats
            type: boolean
            sample: False
        isblk:
            description: Tells you if the path is a block device
            returned: success, path exists and user can read stats
            type: boolean
            sample: False
        isreg:
            description: Tells you if the path is a regular file
            returned: success, path exists and user can read stats
            type: boolean
            sample: True
        isfifo:
            description: Tells you if the path is a named pipe
            returned: success, path exists and user can read stats
            type: boolean
            sample: False
        islnk:
            description: Tells you if the path is a symbolic link
            returned: success, path exists and user can read stats
            type: boolean
            sample: False
        issock:
            description: Tells you if the path is a unix domain socket
            returned: success, path exists and user can read stats
            type: boolean
            sample: False
        uid:
            description: Numeric id representing the file owner
            returned: success, path exists and user can read stats
            type: int
            sample: 1003
        gid:
            description: Numeric id representing the group of the owner
            returned: success, path exists and user can read stats
            type: int
            sample: 1003
        size:
            description: Size in bytes for a plain file, amount of data for some special files
            returned: success, path exists and user can read stats
            type: int
            sample: 203
        inode:
            description: Inode number of the path
            returned: success, path exists and user can read stats
            type: int
            sample: 12758
        dev:
            description: Device the inode resides on
            returned: success, path exists and user can read stats
            type: int
            sample: 33
        nlink:
            description: Number of links to the inode (hard links)
            returned: success, path exists and user can read stats
            type: int
            sample: 1
        atime:
            description: Time of last access
            returned: success, path exists and user can read stats
            type: float
            sample: 1424348972.575
        mtime:
            description: Time of last modification
            returned: success, path exists and user can read stats
            type: float
            sample: 1424348972.575
        ctime:
            description: Time of last metadata update or creation (depends on OS)
            returned: success, path exists and user can read stats
            type: float
            sample: 1424348972.575
        wusr:
            description: Tells you if the owner has write permission
            returned: success, path exists and user can read stats
            type: boolean
            sample: True
        rusr:
            description: Tells you if the owner has read permission
            returned: success, path exists and user can read stats
            type: boolean
            sample: True
        xusr:
            description: Tells you if the owner has execute permission
            returned: success, path exists and user can read stats
            type: boolean
            sample: True
        wgrp:
            description: Tells you if the owner's group has write permission
            returned: success, path exists and user can read stats
            type: boolean
            sample: False
        rgrp:
            description: Tells you if the owner's group has read permission
            returned: success, path exists and user can read stats
            type: boolean
            sample: True
        xgrp:
            description: Tells you if the owner's group has execute permission
            returned: success, path exists and user can read stats
            type: boolean
            sample: True
        woth:
            description: Tells you if others have write permission
            returned: success, path exists and user can read stats
            type: boolean
            sample: False
        roth:
            description: Tells you if others have read permission
            returned: success, path exists and user can read stats
            type: boolean
            sample: True
        xoth:
            description: Tells you if others have execute permission
            returned: success, path exists and user can read stats
            type: boolean
            sample: True
        isuid:
            description: Tells you if the invoking user's id matches the owner's id
            returned: success, path exists and user can read stats
            type: boolean
            sample: False
        isgid:
            description: Tells you if the invoking user's group id matches the owner's group id
            returned: success, path exists and user can read stats
            type: boolean
            sample: False
        lnk_source:
            description: Target of the symlink normalized for the remote filesystem
            returned: success, path exists and user can read stats and the path is a symbolic link
            type: string
            sample: /home/foobar/21102015-1445431274-908472971
        lnk_target:
            description: Target of the symlink.  Note that relative paths remain relative
            returned: success, path exists and user can read stats and the path is a symbolic link
            type: string
            sample: ../foobar/21102015-1445431274-908472971
            version_added: 2.4
        md5:
            description: md5 hash of the path; this will be removed in Ansible 2.9 in
                favor of the checksum return value
            returned: success, path exists and user can read stats and path
                supports hashing and md5 is supported
            type: string
            sample: f88fa92d8cf2eeecf4c0a50ccc96d0c0
        checksum:
            description: hash of the path
            returned: success, path exists, user can read stats, path supports
                hashing and supplied checksum algorithm is available
            type: string
            sample: 50ba294cdf28c0d5bcde25708df53346825a429f
        pw_name:
            description: User name of owner
            returned: success, path exists and user can read stats and installed python supports it
            type: string
            sample: httpd
        gr_name:
            description: Group name of owner
            returned: success, path exists and user can read stats and installed python supports it
            type: string
            sample: www-data
        mime_type:
            description: file magic data or mime-type
            returned: success, path exists and user can read stats and
                installed python supports it and the `mime` option was true, will
                return 'unknown' on error.
            type: string
            sample: PDF document, version 1.2
        charset:
            description: file character set or encoding
            returned: success, path exists and user can read stats and
                installed python supports it and the `mime` option was true, will
                return 'unknown' on error.
            type: string
            sample: us-ascii
        readable:
            description: Tells you if the invoking user has the right to read the path
            returned: success, path exists and user can read the path
            type: boolean
            sample: False
            version_added: 2.2
        writeable:
            description: Tells you if the invoking user has the right to write the path
            returned: success, path exists and user can write the path
            type: boolean
            sample: False
            version_added: 2.2
        executable:
            description: Tells you if the invoking user has the execute the path
            returned: success, path exists and user can execute the path
            type: boolean
            sample: False
            version_added: 2.2
        attributes:
            description: list of file attributes
            returned: success, path exists and user can execute the path
            type: list
            sample: [ immutable, extent ]
            version_added: 2.3
'''

import errno
import grp
import os
import pwd
import stat

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes


def format_output(module, path, st):
    mode = st.st_mode

    # back to ansible
    output = dict(
        exists=True,
        path=path,
        mode="%04o" % stat.S_IMODE(mode),
        isdir=stat.S_ISDIR(mode),
        ischr=stat.S_ISCHR(mode),
        isblk=stat.S_ISBLK(mode),
        isreg=stat.S_ISREG(mode),
        isfifo=stat.S_ISFIFO(mode),
        islnk=stat.S_ISLNK(mode),
        issock=stat.S_ISSOCK(mode),
        uid=st.st_uid,
        gid=st.st_gid,
        size=st.st_size,
        inode=st.st_ino,
        dev=st.st_dev,
        nlink=st.st_nlink,
        atime=st.st_atime,
        mtime=st.st_mtime,
        ctime=st.st_ctime,
        wusr=bool(mode & stat.S_IWUSR),
        rusr=bool(mode & stat.S_IRUSR),
        xusr=bool(mode & stat.S_IXUSR),
        wgrp=bool(mode & stat.S_IWGRP),
        rgrp=bool(mode & stat.S_IRGRP),
        xgrp=bool(mode & stat.S_IXGRP),
        woth=bool(mode & stat.S_IWOTH),
        roth=bool(mode & stat.S_IROTH),
        xoth=bool(mode & stat.S_IXOTH),
        isuid=bool(mode & stat.S_ISUID),
        isgid=bool(mode & stat.S_ISGID),
    )

    # Platform dependent flags:
    for other in [
            # Some Linux
            ('st_blocks', 'blocks'),
            ('st_blksize', 'block_size'),
            ('st_rdev', 'device_type'),
            ('st_flags', 'flags'),
            # Some Berkley based
            ('st_gen', 'generation'),
            ('st_birthtime', 'birthtime'),
            # RISCOS
            ('st_ftype', 'file_type'),
            ('st_attrs', 'attrs'),
            ('st_obtype', 'object_type'),
            # OS X
            ('st_rsize', 'real_size'),
            ('st_creator', 'creator'),
            ('st_type', 'file_type'),
    ]:
        if hasattr(st, other[0]):
            output[other[1]] = getattr(st, other[0])

    return output


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(required=True, type='path'),
            follow=dict(type='bool', default='no'),
            get_md5=dict(type='bool'),
            get_checksum=dict(type='bool', default='yes'),
            get_mime=dict(type='bool', default='yes', aliases=['mime', 'mime_type', 'mime-type']),
            get_attributes=dict(type='bool', default='yes', aliases=['attr', 'attributes']),
            checksum_algorithm=dict(type='str', default='sha1',
                                    choices=['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512'],
                                    aliases=['checksum', 'checksum_algo']),
        ),
        supports_check_mode=True,
    )

    path = module.params.get('path')
    b_path = to_bytes(path, errors='surrogate_or_strict')
    follow = module.params.get('follow')
    get_mime = module.params.get('get_mime')
    get_attr = module.params.get('get_attributes')
    get_md5 = module.params.get('get_md5')

    # get_md5 will be an undocumented option in 2.9 to be removed at a later
    # date if possible (3.0+)
    if get_md5:
        module.deprecate("get_md5 has been deprecated along with the md5 return value, use "
                         "get_checksum=True and checksum_algorithm=md5 instead", 2.9)
    else:
        get_md5 = False
    get_checksum = module.params.get('get_checksum')
    checksum_algorithm = module.params.get('checksum_algorithm')

    # main stat data
    try:
        if follow:
            st = os.stat(b_path)
        else:
            st = os.lstat(b_path)
    except OSError as e:
        if e.errno == errno.ENOENT:
            output = {'exists': False}
            module.exit_json(changed=False, stat=output)

        module.fail_json(msg=e.strerror)

    # process base results
    output = format_output(module, path, st)

    # resolved permissions
    for perm in [('readable', os.R_OK), ('writeable', os.W_OK), ('executable', os.X_OK)]:
        output[perm[0]] = os.access(b_path, perm[1])

    # symlink info
    if output.get('islnk'):
        output['lnk_source'] = os.path.realpath(b_path)
        output['lnk_target'] = os.readlink(b_path)

    try:  # user data
        pw = pwd.getpwuid(st.st_uid)
        output['pw_name'] = pw.pw_name
    except:
        pass

    try:  # group data
        grp_info = grp.getgrgid(st.st_gid)
        output['gr_name'] = grp_info.gr_name
    except:
        pass

    # checksums
    if output.get('isreg') and output.get('readable'):
        if get_md5:
            # Will fail on FIPS-140 compliant systems
            try:
                output['md5'] = module.md5(b_path)
            except ValueError:
                output['md5'] = None

        if get_checksum:
            output['checksum'] = module.digest_from_file(b_path, checksum_algorithm)

    # try to get mime data if requested
    if get_mime:
        output['mimetype'] = output['charset'] = 'unknown'
        mimecmd = module.get_bin_path('file')
        if mimecmd:
            mimecmd = [mimecmd, '-i', b_path]
            try:
                rc, out, err = module.run_command(mimecmd)
                if rc == 0:
                    mimetype, charset = out.split(':')[1].split(';')
                    output['mimetype'] = mimetype.strip()
                    output['charset'] = charset.split('=')[1].strip()
            except:
                pass

    # try to get attr data
    if get_attr:
        output['version'] = None
        output['attributes'] = []
        output['attr_flags'] = ''
        out = module.get_file_attributes(b_path)
        for x in ('version', 'attributes', 'attr_flags'):
            if x in out:
                output[x] = out[x]

    module.exit_json(changed=False, stat=output)


if __name__ == '__main__':
    main()
