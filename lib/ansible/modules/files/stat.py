#!/usr/bin/python
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
module: stat
version_added: "1.3"
short_description: retrieve file or file system status
description:
     - Retrieves facts for a file similar to the linux/unix 'stat' command.
options:
  path:
    description:
      - The full path of the file/object to get the facts of
    required: true
    default: null
  follow:
    description:
      - Whether to follow symlinks
    required: false
    default: no
  get_md5:
    description:
      - Whether to return the md5 sum of the file.  Will return None if we're unable to use md5 (Common for FIPS-140 compliant systems)
    required: false
    default: yes
  get_checksum:
    description:
      - Whether to return a checksum of the file (default sha1)
    required: false
    default: yes
    version_added: "1.8"
  checksum_algorithm:
    description:
      - Algorithm to determine checksum of file. Will throw an error if the host is unable to use specified algorithm.
    required: false
    choices: [ 'sha1', 'sha224', 'sha256', 'sha384', 'sha512' ]
    default: sha1
    aliases: [ 'checksum_algo', 'checksum' ]
    version_added: "2.0"
  mime:
    description:
      - Use file magic and return data about the nature of the file. this uses the 'file' utility found on most Linux/Unix systems.
      - This will add both `mime_type` and 'charset' fields to the return, if possible.
    required: false
    choices: [ Yes, No ]
    default: No
    version_added: "2.1"
    aliases: [ 'mime_type', 'mime-type' ]
author: "Bruce Pennypacker (@bpennypacker)"
'''

EXAMPLES = '''
# Obtain the stats of /etc/foo.conf, and check that the file still belongs
# to 'root'. Fail otherwise.
- stat: path=/etc/foo.conf
  register: st
- fail: msg="Whoops! file ownership has changed"
  when: st.stat.pw_name != 'root'

# Determine if a path exists and is a symlink. Note that if the path does
# not exist, and we test sym.stat.islnk, it will fail with an error. So
# therefore, we must test whether it is defined.
# Run this to understand the structure, the skipped ones do not pass the
# check performed by 'when'
- stat: path=/path/to/something
  register: sym
- debug: msg="islnk isn't defined (path doesn't exist)"
  when: sym.stat.islnk is not defined
- debug: msg="islnk is defined (path must exist)"
  when: sym.stat.islnk is defined
- debug: msg="Path exists and is a symlink"
  when: sym.stat.islnk is defined and sym.stat.islnk
- debug: msg="Path exists and isn't a symlink"
  when: sym.stat.islnk is defined and sym.stat.islnk == False


# Determine if a path exists and is a directory.  Note that we need to test
# both that p.stat.isdir actually exists, and also that it's set to true.
- stat: path=/path/to/something
  register: p
- debug: msg="Path exists and is a directory"
  when: p.stat.isdir is defined and p.stat.isdir

# Don't do md5 checksum
- stat: path=/path/to/myhugefile get_md5=no

# Use sha256 to calculate checksum
- stat: path=/path/to/something checksum_algorithm=sha256
'''

RETURN = '''
stat:
    description: dictionary containing all the stat data
    returned: success
    type: dictionary
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
            description: Size in bytes for a plain file, ammount of data for some special files
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
            description: Original path
            returned: success, path exists and user can read stats and the path is a symbolic link
            type: string
            sample: /home/foobar/21102015-1445431274-908472971
        md5:
            description: md5 hash of the path
            returned: success, path exists and user can read stats and path supports hashing and md5 is supported
            type: string
            sample: f88fa92d8cf2eeecf4c0a50ccc96d0c0
        checksum_algorithm:
            description: hash of the path
            returned: success, path exists, user can read stats, path supports hashing and supplied checksum algorithm is available
            type: string
            sample: 50ba294cdf28c0d5bcde25708df53346825a429f
            aliases: ['checksum', 'checksum_algo']
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
            returned: success, path exists and user can read stats and installed python supports it and the `mime` option was true, will return 'unknown' on error.
            type: string
            sample: PDF document, version 1.2
        charset:
            description: file character set or encoding
            returned: success, path exists and user can read stats and installed python supports it and the `mime` option was true, will return 'unknown' on error.
            type: string
            sample: us-ascii
'''

import os
import sys
from stat import *
import pwd
import grp

def main():
    module = AnsibleModule(
        argument_spec = dict(
            path = dict(required=True, type='path'),
            follow = dict(default='no', type='bool'),
            get_md5 = dict(default='yes', type='bool'),
            get_checksum = dict(default='yes', type='bool'),
            checksum_algorithm = dict(default='sha1', type='str', choices=['sha1', 'sha224', 'sha256', 'sha384', 'sha512'], aliases=['checksum_algo', 'checksum']),
            mime = dict(default=False, type='bool', aliases=['mime_type', 'mime-type']),
        ),
        supports_check_mode = True
    )

    path = module.params.get('path')
    follow = module.params.get('follow')
    get_md5 = module.params.get('get_md5')
    get_checksum = module.params.get('get_checksum')
    checksum_algorithm = module.params.get('checksum_algorithm')

    try:
        if follow:
            st = os.stat(path)
        else:
            st = os.lstat(path)
    except OSError:
        e = get_exception()
        if e.errno == errno.ENOENT:
            d = { 'exists' : False }
            module.exit_json(changed=False, stat=d)

        module.fail_json(msg = e.strerror)

    mode = st.st_mode

    # back to ansible
    d = {
        'exists'   : True,
        'path'     : path,
        'mode'    : "%04o" % S_IMODE(mode),
        'isdir'    : S_ISDIR(mode),
        'ischr'    : S_ISCHR(mode),
        'isblk'    : S_ISBLK(mode),
        'isreg'    : S_ISREG(mode),
        'isfifo'   : S_ISFIFO(mode),
        'islnk'    : S_ISLNK(mode),
        'issock'   : S_ISSOCK(mode),
        'uid'      : st.st_uid,
        'gid'      : st.st_gid,
        'size'     : st.st_size,
        'inode'    : st.st_ino,
        'dev'      : st.st_dev,
        'nlink'    : st.st_nlink,
        'atime'    : st.st_atime,
        'mtime'    : st.st_mtime,
        'ctime'    : st.st_ctime,
        'wusr'     : bool(mode & stat.S_IWUSR),
        'rusr'     : bool(mode & stat.S_IRUSR),
        'xusr'     : bool(mode & stat.S_IXUSR),
        'wgrp'     : bool(mode & stat.S_IWGRP),
        'rgrp'     : bool(mode & stat.S_IRGRP),
        'xgrp'     : bool(mode & stat.S_IXGRP),
        'woth'     : bool(mode & stat.S_IWOTH),
        'roth'     : bool(mode & stat.S_IROTH),
        'xoth'     : bool(mode & stat.S_IXOTH),
        'isuid'    : bool(mode & stat.S_ISUID),
        'isgid'    : bool(mode & stat.S_ISGID),
        }

    if S_ISLNK(mode):
        d['lnk_source'] = os.path.realpath(path)

    if S_ISREG(mode) and get_md5 and os.access(path,os.R_OK):
        # Will fail on FIPS-140 compliant systems
        try:
            d['md5']       = module.md5(path)
        except ValueError:
            d['md5']       = None

    if S_ISREG(mode) and get_checksum and os.access(path,os.R_OK):
        d['checksum']      = module.digest_from_file(path, checksum_algorithm)

    try:
        pw = pwd.getpwuid(st.st_uid)

        d['pw_name']   = pw.pw_name

        grp_info = grp.getgrgid(st.st_gid)
        d['gr_name'] = grp_info.gr_name
    except:
        pass

    if module.params.get('mime'):
        d['mime_type'] = 'unknown'
        d['charset'] = 'unknown'

        filecmd = [module.get_bin_path('file', True),'-i', path]
        try:
            rc, out, err = module.run_command(filecmd)
            if rc == 0:
                mtype, chset = out.split(':')[1].split(';')
                d['mime_type'] = mtype.strip()
                d['charset'] = chset.split('=')[1].strip()
        except:
            pass

    module.exit_json(changed=False, stat=d)

# import module snippets
from ansible.module_utils.basic import *

main()
