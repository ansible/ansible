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
    aliases: []
  follow:
    description:
      - Whether to follow symlinks
    required: false
    default: no
    aliases: []
  get_md5:
    description:
      - Whether to return the md5 sum of the file.  Will return None if we're unable to use md5 (Common for FIPS-140 compliant systems)
    required: false
    default: yes
    aliases: []
  get_checksum:
    description:
      - Whether to return a checksum of the file (currently sha1)
    required: false
    default: yes
    aliases: []
    version_added: "1.8"
author: Bruce Pennypacker
'''

EXAMPLES = '''
# Obtain the stats of /etc/foo.conf, and check that the file still belongs
# to 'root'. Fail otherwise.
- stat: path=/etc/foo.conf
  register: st
- fail: msg="Whoops! file ownership has changed"
  when: st.stat.pw_name != 'root'

# Determine if a path exists and is a directory.  Note that we need to test
# both that p.stat.isdir actually exists, and also that it's set to true.
- stat: path=/path/to/something
  register: p
- debug: msg="Path exists and is a directory"
  when: p.stat.isdir is defined and p.stat.isdir

# Don't do md5 checksum
- stat: path=/path/to/myhugefile get_md5=no
'''

import os
import sys
from stat import *
import pwd

def main():
    module = AnsibleModule(
        argument_spec = dict(
            path = dict(required=True),
            follow = dict(default='no', type='bool'),
            get_md5 = dict(default='yes', type='bool'),
            get_checksum = dict(default='yes', type='bool')
        ),
        supports_check_mode = True
    )

    path = module.params.get('path')
    path = os.path.expanduser(path)
    follow = module.params.get('follow')
    get_md5 = module.params.get('get_md5')
    get_checksum = module.params.get('get_checksum')

    try:
        if follow:
            st = os.stat(path)
        else:
            st = os.lstat(path)
    except OSError, e:
        if e.errno == errno.ENOENT:
            d = { 'exists' : False }
            module.exit_json(changed=False, stat=d)

        module.fail_json(msg = e.strerror)

    mode = st.st_mode

    # back to ansible
    d = {
        'exists'   : True,
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
        d['checksum']       = module.sha1(path)


    try:
        pw = pwd.getpwuid(st.st_uid)

        d['pw_name']   = pw.pw_name
    except:
        pass


    module.exit_json(changed=False, stat=d)

# import module snippets
from ansible.module_utils.basic import *

main()
