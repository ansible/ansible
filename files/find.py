#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Ruggero Marchei <ruggero.marchei@daemonzone.net>
# (c) 2015, Brian Coca <bcoca@ansible.com>
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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>


import os
import stat
import fnmatch
import time
import re

DOCUMENTATION = '''
---
module: find
author: Brian Coca (based on Ruggero Marchei's Tidy)
version_added: "2.0"
short_description: return a list of files based on specific criteria
requirements: []
description:
    - Return a list files based on specific criteria. Multiple criteria are AND'd together.
options:
    age:
        required: false
        default: null
        description:
            - Select files whose age is equal to or greater than the specified time.
              Use a negative age to find files equal to or less than the specified time.
              You can choose seconds, minutes, hours, days, or weeks by specifying the
              first letter of any of those words (e.g., "1w").
    patterns:
        required: false
        default: '*'
        description:
            - One or more (shell or regex) patterns, which type is controled by C(use_regex) option.
            - The patterns restrict the list of files to be returned to those whose basenames match at
              least one of the patterns specified. Multiple patterns can be specified using a list.
        aliases: ['pattern']
    contains:
        required: false
        default: null
        description:
            - One or more re patterns which should be matched against the file content
    paths:
        required: true
        aliases: [ "name", "path" ]
        description:
            - List of paths to the file or directory to search. All paths must be fully qualified.
    file_type:
        required: false
        description:
            - Type of file to select
        choices: [ "file", "directory" ]
        default: "file"
    recurse:
        required: false
        default: "no"
        choices: [ "yes", "no" ]
        description:
            - If target is a directory, recursively descend into the directory looking for files.
    size:
        required: false
        default: null
        description:
            - Select files whose size is equal to or greater than the specified size.
              Use a negative size to find files equal to or less than the specified size.
              Unqualified values are in bytes, but b, k, m, g, and t can be appended to specify
              bytes, kilobytes, megabytes, gigabytes, and terabytes, respectively.
              Size is not evaluated for directories.
    age_stamp:
        required: false
        default: "mtime"
        choices: [ "atime", "mtime", "ctime" ]
        description:
            - Choose the file property against which we compare age. Default is mtime.
    hidden:
        required: false
        default: "False"
        choices: [ True, False ]
        description:
            - Set this to true to include hidden files, otherwise they'll be ignored.
    follow:
        required: false
        default: "False"
        choices: [ True, False ]
        description:
            - Set this to true to follow symlinks in path for systems with python 2.6+
    get_checksum:
        required: false
        default: "False"
        choices: [ True, False ]
        description:
            - Set this to true to retrieve a file's sha1 checksum
    use_regex:
        required: false
        default: "False"
        choices: [ True, False ]
        description:
            - If false the patterns are file globs (shell) if true they are python regexes
'''


EXAMPLES = '''
# Recursively find /tmp files older than 2 days
- find: paths="/tmp" age="2d" recurse=yes

# Recursively find /tmp files older than 4 weeks and equal or greater than 1 megabyte
- find: paths="/tmp" age="4w" size="1m" recurse=yes

# Recursively find /var/tmp files with last access time greater than 3600 seconds
- find: paths="/var/tmp" age="3600" age_stamp=atime recurse=yes

# find /var/log files equal or greater than 10 megabytes ending with .old or .log.gz
- find: paths="/var/tmp" patterns="*.old,*.log.gz" size="10m"

# find /var/log files equal or greater than 10 megabytes ending with .old or .log.gz via regex
- find: paths="/var/tmp" patterns="^.*?\.(?:old|log\.gz)$" size="10m" use_regex=True
'''

RETURN = '''
files:
    description: all matches found with the specified criteria (see stat module for full output of each dictionary)
    returned: success
    type: list of dictionaries
    sample: [
        { path="/var/tmp/test1",
          mode=0644,
          ...,
          checksum=16fac7be61a6e4591a33ef4b729c5c3302307523
        },
        { path="/var/tmp/test2",
          ...
        },
        ]
matched:
    description: number of matches
    returned: success
    type: string
    sample: 14
examined:
    description: number of filesystem objects looked at
    returned: success
    type: string
    sample: 34
'''

def pfilter(f, patterns=None, use_regex=False):
    '''filter using glob patterns'''

    if patterns is None:
        return True

    if use_regex:
        for p in patterns:
            r =  re.compile(p)
            if r.match(f):
                return True
    else:

        for p in patterns:
            if fnmatch.fnmatch(f, p):
                return True

    return False


def agefilter(st, now, age, timestamp):
    '''filter files older than age'''
    if age is None or \
      (age >= 0 and now - st.__getattribute__("st_%s" % timestamp) >= abs(age)) or \
      (age < 0 and now - st.__getattribute__("st_%s" % timestamp) <= abs(age)):

        return True
    return False


def sizefilter(st, size):
    '''filter files greater than size'''
    if size is None or \
       (size >= 0 and st.st_size >= abs(size)) or \
       (size < 0 and st.st_size <= abs(size)):

        return True

    return False

def contentfilter(fsname, pattern):
    '''filter files which contain the given expression'''
    if pattern is None: return True

    try:
       f = open(fsname)
       prog = re.compile(pattern)
       for line in f:
           if prog.match (line):
               f.close()
               return True

       f.close() 
    except:
       pass

    return False

def statinfo(st):
    return {
        'mode'     : "%04o" % stat.S_IMODE(st.st_mode),
        'isdir'    : stat.S_ISDIR(st.st_mode),
        'ischr'    : stat.S_ISCHR(st.st_mode),
        'isblk'    : stat.S_ISBLK(st.st_mode),
        'isreg'    : stat.S_ISREG(st.st_mode),
        'isfifo'   : stat.S_ISFIFO(st.st_mode),
        'islnk'    : stat.S_ISLNK(st.st_mode),
        'issock'   : stat.S_ISSOCK(st.st_mode),
        'uid'      : st.st_uid,
        'gid'      : st.st_gid,
        'size'     : st.st_size,
        'inode'    : st.st_ino,
        'dev'      : st.st_dev,
        'nlink'    : st.st_nlink,
        'atime'    : st.st_atime,
        'mtime'    : st.st_mtime,
        'ctime'    : st.st_ctime,
        'wusr'     : bool(st.st_mode & stat.S_IWUSR),
        'rusr'     : bool(st.st_mode & stat.S_IRUSR),
        'xusr'     : bool(st.st_mode & stat.S_IXUSR),
        'wgrp'     : bool(st.st_mode & stat.S_IWGRP),
        'rgrp'     : bool(st.st_mode & stat.S_IRGRP),
        'xgrp'     : bool(st.st_mode & stat.S_IXGRP),
        'woth'     : bool(st.st_mode & stat.S_IWOTH),
        'roth'     : bool(st.st_mode & stat.S_IROTH),
        'xoth'     : bool(st.st_mode & stat.S_IXOTH),
        'isuid'    : bool(st.st_mode & stat.S_ISUID),
        'isgid'    : bool(st.st_mode & stat.S_ISGID),
    }


def main():
    module = AnsibleModule(
        argument_spec = dict(
            paths         = dict(required=True, aliases=['name','path'], type='list'),
            patterns      = dict(default=['*'], type='list', aliases=['pattern']),
            contains      = dict(default=None, type='str'),
            file_type     = dict(default="file", choices=['file', 'directory'], type='str'),
            age           = dict(default=None, type='str'),
            age_stamp     = dict(default="mtime", choices=['atime','mtime','ctime'], type='str'),
            size          = dict(default=None, type='str'),
            recurse       = dict(default='no', type='bool'),
            hidden        = dict(default="False", type='bool'),
            follow        = dict(default="False", type='bool'),
            get_checksum  = dict(default="False", type='bool'),
            use_regex     = dict(default="False", type='bool'),
        ),
        supports_check_mode=True,
    )

    params = module.params

    filelist = []

    if params['age'] is None:
        age = None
    else:
        # convert age to seconds:
        m = re.match("^(-?\d+)(s|m|h|d|w)?$", params['age'].lower())
        seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
        if m:
            age = int(m.group(1)) * seconds_per_unit.get(m.group(2), 1)
        else:
            module.fail_json(age=params['age'], msg="failed to process age")

    if params['size'] is None:
        size = None
    else:
        # convert size to bytes:
        m = re.match("^(-?\d+)(b|k|m|g|t)?$", params['size'].lower())
        bytes_per_unit = {"b": 1, "k": 1024, "m": 1024**2, "g": 1024**3, "t": 1024**4}
        if m:
            size = int(m.group(1)) * bytes_per_unit.get(m.group(2), 1)
        else:
            module.fail_json(size=params['size'], msg="failed to process size")

    now = time.time()
    msg = ''
    looked = 0
    for npath in params['paths']:
        if os.path.isdir(npath):

            ''' ignore followlinks for python version < 2.6 '''
            for root,dirs,files in (sys.version_info < (2,6,0) and os.walk(npath)) or \
                                    os.walk( npath, followlinks=params['follow']):
                looked = looked + len(files) + len(dirs)
                for fsobj in (files + dirs):
                    fsname=os.path.normpath(os.path.join(root, fsobj))

                    if os.path.basename(fsname).startswith('.') and not params['hidden']:
                       continue

                    try:
                        st = os.stat(fsname)
                    except:
                        msg+="%s was skipped as it does not seem to be a valid file or it cannot be accessed\n" % fsname
                        continue

                    r = {'path': fsname}
                    if stat.S_ISDIR(st.st_mode) and params['file_type'] == 'directory':
                        if pfilter(fsobj, params['patterns'], params['use_regex']) and agefilter(st, now, age, params['age_stamp']):

                            r.update(statinfo(st))
                            filelist.append(r)

                    elif stat.S_ISREG(st.st_mode) and params['file_type'] == 'file':
                        if pfilter(fsobj, params['patterns'], params['use_regex']) and \
                           agefilter(st, now, age, params['age_stamp']) and \
                           sizefilter(st, size) and \
                           contentfilter(fsname, params['contains']):

                            r.update(statinfo(st))
                            if params['get_checksum']:
                                r['checksum'] = module.sha1(fsname)
                            filelist.append(r)

                if not params['recurse']:
                    break
        else:
            msg+="%s was skipped as it does not seem to be a valid directory or it cannot be accessed\n" % npath

    matched = len(filelist)
    module.exit_json(files=filelist, changed=False, msg=msg, matched=matched, examined=looked)

# import module snippets
from ansible.module_utils.basic import *
main()

