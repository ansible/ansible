# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Ruggero Marchei <ruggero.marchei@daemonzone.net>
# Copyright: (c) 2015, Brian Coca <bcoca@ansible.com>
# Copyright: (c) 2016-2017, Konstantin Shalygin <k0ste@k0ste.ru>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = r"""
---
module: find
author: Brian Coca (@bcoca)
version_added: "2.0"
short_description: Return a list of files based on specific criteria
description:
    - Return a list of files based on specific criteria. Multiple criteria are AND'd together.
    - For Windows targets, use the M(ansible.windows.win_find) module instead.
    - This module does not use the C(find) command, it is a much simpler and slower Python implementation.
      It is intended for small and simple uses. Those that need the extra power or speed and have expertise
      with the UNIX command, should use it directly.
options:
    age:
        description:
            - Select files whose age is equal to or greater than the specified time.
            - Use a negative age to find files equal to or less than the specified time.
            - You can choose seconds, minutes, hours, days, or weeks by specifying the
              first letter of any of those words (e.g., "1w").
        type: str
    get_checksum:
        default: false
    checksum_algorithm:
        version_added: "2.19"
    patterns:
        default: []
        description:
            - One or more (shell or regex) patterns, which type is controlled by O(use_regex) option.
            - The patterns restrict the list of files to be returned to those whose basenames match at
              least one of the patterns specified. Multiple patterns can be specified using a list.
            - The pattern is matched against the file base name, excluding the directory.
            - When using regexen, the pattern MUST match the ENTIRE file name, not just parts of it. So
              if you are looking to match all files ending in .default, you'd need to use C(.*\.default)
              as a regexp and not just C(\.default).
            - This parameter expects a list, which can be either comma separated or YAML. If any of the
              patterns contain a comma, make sure to put them in a list to avoid splitting the patterns
              in undesirable ways.
            - Defaults to V(*) when O(use_regex=False), or V(.*) when O(use_regex=True).
        type: list
        aliases: [ pattern ]
        elements: str
    excludes:
        description:
            - One or more (shell or regex) patterns, which type is controlled by O(use_regex) option.
            - Items whose basenames match an O(excludes) pattern are culled from O(patterns) matches.
              Multiple patterns can be specified using a list.
        type: list
        aliases: [ exclude ]
        version_added: "2.5"
        elements: str
    contains:
        description:
            - A regular expression or pattern which should be matched against the file content.
            - If O(read_whole_file=false) it matches against the beginning of the line (uses
              V(re.match(\))). If O(read_whole_file=true), it searches anywhere for that pattern
              (uses V(re.search(\))).
            - Works only when O(file_type) is V(file).
        type: str
    read_whole_file:
        description:
            - When doing a C(contains) search, determines whether the whole file should be read into
              memory or if the regex should be applied to the file line-by-line.
            - Setting this to C(true) can have performance and memory implications for large files.
            - This uses V(re.search(\)) instead of V(re.match(\)).
        type: bool
        default: false
        version_added: "2.11"
    paths:
        description:
            - List of paths of directories to search. All paths must be fully qualified.
            - From ansible-core 2.18 and onwards, the data type has changed from C(str) to C(path).
        type: list
        required: true
        aliases: [ name, path ]
        elements: path
    file_type:
        description:
            - Type of file to select.
            - The V(link) and V(any) choices were added in Ansible 2.3.
        type: str
        choices: [ any, directory, file, link ]
        default: file
    recurse:
        description:
            - If target is a directory, recursively descend into the directory looking for files.
        type: bool
        default: no
    size:
        description:
            - Select files whose size is equal to or greater than the specified size.
            - Use a negative size to find files equal to or less than the specified size.
            - Unqualified values are in bytes but b, k, m, g, and t can be appended to specify
              bytes, kilobytes, megabytes, gigabytes, and terabytes, respectively.
            - Size is not evaluated for directories.
        type: str
    age_stamp:
        description:
            - Choose the file property against which we compare age.
        type: str
        choices: [ atime, ctime, mtime ]
        default: mtime
    hidden:
        description:
            - Set this to V(true) to include hidden files, otherwise they will be ignored.
        type: bool
        default: no
    mode:
        description:
            - Choose objects matching a specified permission. This value is
              restricted to modes that can be applied using the python
              C(os.chmod) function.
            - The mode can be provided as an octal such as V("0644") or
              as symbolic such as V(u=rw,g=r,o=r).
        type: raw
        version_added: '2.16'
    exact_mode:
        description:
            - Restrict mode matching to exact matches only, and not as a
              minimum set of permissions to match.
        type: bool
        default: true
        version_added: '2.16'
    follow:
        description:
            - Set this to V(true) to follow symlinks in path for systems with python 2.6+.
        type: bool
        default: no
    use_regex:
        description:
            - If V(false), the patterns are file globs (shell).
            - If V(true), they are python regexes.
        type: bool
        default: no
    depth:
        description:
            - Set the maximum number of levels to descend into.
            - Setting O(recurse=false) will override this value, which is effectively depth 1.
            - Default is unlimited depth.
        type: int
        version_added: "2.6"
    encoding:
        description:
            - When doing a O(contains) search, determine the encoding of the files to be searched.
        type: str
        version_added: "2.17"
    limit:
        description:
            - Limit the maximum number of matching paths returned. After finding this many, the find action will stop looking.
            - Matches are made from the top, down (i.e. shallowest directory first).
            - If not set, or set to v(null), it will do unlimited matches.
            - Default is unlimited matches.
        type: int
        version_added: "2.18"
extends_documentation_fragment: [action_common_attributes, checksum_common]
attributes:
    check_mode:
        details: since this action does not modify the target it just executes normally during check mode
        support: full
    diff_mode:
        support: none
    platform:
        platforms: posix
seealso:
- module: ansible.windows.win_find
"""


EXAMPLES = r"""
- name: Recursively find /tmp files older than 2 days
  ansible.builtin.find:
    paths: /tmp
    age: 2d
    recurse: yes

- name: Recursively find /tmp files older than 4 weeks and equal or greater than 1 megabyte
  ansible.builtin.find:
    paths: /tmp
    age: 4w
    size: 1m
    recurse: yes

- name: Recursively find /var/tmp files with last access time greater than 3600 seconds
  ansible.builtin.find:
    paths: /var/tmp
    age: 3600
    age_stamp: atime
    recurse: yes

- name: Find /var/log files equal or greater than 10 megabytes ending with .old or .log.gz
  ansible.builtin.find:
    paths: /var/log
    patterns: '*.old,*.log.gz'
    size: 10m

# Note that YAML double quotes require escaping backslashes but yaml single quotes do not.
- name: Find /var/log files equal or greater than 10 megabytes ending with .old or .log.gz via regex
  ansible.builtin.find:
    paths: /var/log
    patterns: "^.*?\\.(?:old|log\\.gz)$"
    size: 10m
    use_regex: yes

- name: Find /var/log all directories, exclude nginx and mysql
  ansible.builtin.find:
    paths: /var/log
    recurse: no
    file_type: directory
    excludes: 'nginx,mysql'

# When using patterns that contain a comma, make sure they are formatted as lists to avoid splitting the pattern
- name: Use a single pattern that contains a comma formatted as a list
  ansible.builtin.find:
    paths: /var/log
    file_type: file
    use_regex: yes
    patterns: ['^_[0-9]{2,4}_.*.log$']

- name: Use multiple patterns that contain a comma formatted as a YAML list
  ansible.builtin.find:
    paths: /var/log
    file_type: file
    use_regex: yes
    patterns:
      - '^_[0-9]{2,4}_.*.log$'
      - '^[a-z]{1,5}_.*log$'

- name: Find file containing "wally" without necessarily reading all files
  ansible.builtin.find:
    paths: /var/log
    file_type: file
    contains: wally
    read_whole_file: true
    patterns: "^.*\\.log$"
    use_regex: true
    recurse: true
    limit: 1
"""

RETURN = r"""
files:
    description: All matches found with the specified criteria (see stat module for full output of each dictionary)
    returned: success
    type: list
    sample: [
        { path: "/var/tmp/test1",
          mode: "0644",
          "...": "...",
          checksum: 16fac7be61a6e4591a33ef4b729c5c3302307523
        },
        { path: "/var/tmp/test2",
          "...": "..."
        },
        ]
matched:
    description: Number of matches
    returned: success
    type: int
    sample: 14
examined:
    description: Number of filesystem objects looked at
    returned: success
    type: int
    sample: 34
skipped_paths:
    description: skipped paths and reasons they were skipped
    returned: success
    type: dict
    sample: {"/laskdfj": "'/laskdfj' is not a directory"}
    version_added: '2.12'
"""

import errno
import fnmatch
import grp
import os
import pwd
import re
import stat
import time

from ansible.module_utils.common.text.converters import to_text, to_native
from ansible.module_utils.basic import AnsibleModule


class _Object:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def pfilter(f, patterns=None, excludes=None, use_regex=False):
    """filter using glob patterns"""
    if not patterns and not excludes:
        return True

    if use_regex:
        if patterns and not excludes:
            for p in patterns:
                r = re.compile(p)
                if r.match(f):
                    return True

        elif patterns and excludes:
            for p in patterns:
                r = re.compile(p)
                if r.match(f):
                    for e in excludes:
                        r = re.compile(e)
                        if r.match(f):
                            return False
                    return True

    else:
        if patterns and not excludes:
            for p in patterns:
                if fnmatch.fnmatch(f, p):
                    return True

        elif patterns and excludes:
            for p in patterns:
                if fnmatch.fnmatch(f, p):
                    for e in excludes:
                        if fnmatch.fnmatch(f, e):
                            return False
                    return True

    return False


def agefilter(st, now, age, timestamp):
    """filter files older than age"""
    if age is None:
        return True
    elif age >= 0 and now - getattr(st, "st_%s" % timestamp) >= abs(age):
        return True
    elif age < 0 and now - getattr(st, "st_%s" % timestamp) <= abs(age):
        return True
    return False


def sizefilter(st, size):
    """filter files greater than size"""
    if size is None:
        return True
    elif size >= 0 and st.st_size >= abs(size):
        return True
    elif size < 0 and st.st_size <= abs(size):
        return True
    return False


def contentfilter(fsname, pattern, encoding, read_whole_file=False):
    """
    Filter files which contain the given expression
    :arg fsname: Filename to scan for lines matching a pattern
    :arg pattern: Pattern to look for inside of line
    :arg encoding: Encoding of the file to be scanned
    :arg read_whole_file: If true, the whole file is read into memory before the regex is applied against it. Otherwise, the regex is applied line-by-line.
    :rtype: bool
    :returns: True if one of the lines in fsname matches the pattern. Otherwise False
    """
    if pattern is None:
        return True

    prog = re.compile(pattern)

    try:
        with open(fsname, encoding=encoding) as f:
            if read_whole_file:
                return bool(prog.search(f.read()))

            for line in f:
                if prog.match(line):
                    return True

    except LookupError as e:
        raise e
    except UnicodeDecodeError as e:
        if encoding is None:
            encoding = 'None (default determined by the Python built-in function "open")'
        msg = f'Failed to read the file {fsname} due to an encoding error. current encoding: {encoding}'
        raise Exception(msg) from e
    except Exception:
        pass

    return False


def mode_filter(st, mode, exact, module):
    if not mode:
        return True

    st_mode = stat.S_IMODE(st.st_mode)

    try:
        mode = int(mode, 8)
    except ValueError:
        mode = module._symbolic_mode_to_octal(_Object(st_mode=0), mode)

    mode = stat.S_IMODE(mode)

    if exact:
        return st_mode == mode

    return bool(st_mode & mode)


def statinfo(st):
    pw_name = ""
    gr_name = ""

    try:  # user data
        pw_name = pwd.getpwuid(st.st_uid).pw_name
    except Exception:
        pass

    try:  # group data
        gr_name = grp.getgrgid(st.st_gid).gr_name
    except Exception:
        pass

    return {
        'mode': "%04o" % stat.S_IMODE(st.st_mode),
        'isdir': stat.S_ISDIR(st.st_mode),
        'ischr': stat.S_ISCHR(st.st_mode),
        'isblk': stat.S_ISBLK(st.st_mode),
        'isreg': stat.S_ISREG(st.st_mode),
        'isfifo': stat.S_ISFIFO(st.st_mode),
        'islnk': stat.S_ISLNK(st.st_mode),
        'issock': stat.S_ISSOCK(st.st_mode),
        'uid': st.st_uid,
        'gid': st.st_gid,
        'size': st.st_size,
        'inode': st.st_ino,
        'dev': st.st_dev,
        'nlink': st.st_nlink,
        'atime': st.st_atime,
        'mtime': st.st_mtime,
        'ctime': st.st_ctime,
        'gr_name': gr_name,
        'pw_name': pw_name,
        'wusr': bool(st.st_mode & stat.S_IWUSR),
        'rusr': bool(st.st_mode & stat.S_IRUSR),
        'xusr': bool(st.st_mode & stat.S_IXUSR),
        'wgrp': bool(st.st_mode & stat.S_IWGRP),
        'rgrp': bool(st.st_mode & stat.S_IRGRP),
        'xgrp': bool(st.st_mode & stat.S_IXGRP),
        'woth': bool(st.st_mode & stat.S_IWOTH),
        'roth': bool(st.st_mode & stat.S_IROTH),
        'xoth': bool(st.st_mode & stat.S_IXOTH),
        'isuid': bool(st.st_mode & stat.S_ISUID),
        'isgid': bool(st.st_mode & stat.S_ISGID),
    }


def main():
    module = AnsibleModule(
        argument_spec=dict(
            paths=dict(type='list', required=True, aliases=['name', 'path'], elements='path'),
            patterns=dict(type='list', default=[], aliases=['pattern'], elements='str'),
            excludes=dict(type='list', aliases=['exclude'], elements='str'),
            contains=dict(type='str'),
            read_whole_file=dict(type='bool', default=False),
            file_type=dict(type='str', default="file", choices=['any', 'directory', 'file', 'link']),
            age=dict(type='str'),
            age_stamp=dict(type='str', default="mtime", choices=['atime', 'ctime', 'mtime']),
            size=dict(type='str'),
            recurse=dict(type='bool', default=False),
            hidden=dict(type='bool', default=False),
            follow=dict(type='bool', default=False),
            get_checksum=dict(type='bool', default=False),
            checksum_algorithm=dict(type='str', default='sha1',
                                    choices=['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512'],
                                    aliases=['checksum', 'checksum_algo']),
            use_regex=dict(type='bool', default=False),
            depth=dict(type='int'),
            mode=dict(type='raw'),
            exact_mode=dict(type='bool', default=True),
            encoding=dict(type='str'),
            limit=dict(type='int')
        ),
        supports_check_mode=True,
    )

    params = module.params

    if params['mode'] and not isinstance(params['mode'], str):
        module.fail_json(
            msg="argument 'mode' is not a string and conversion is not allowed, value is of type %s" % params['mode'].__class__.__name__
        )

    # Set the default match pattern to either a match-all glob or
    # regex depending on use_regex being set.  This makes sure if you
    # set excludes: without a pattern pfilter gets something it can
    # handle.
    if not params['patterns']:
        if params['use_regex']:
            params['patterns'] = ['.*']
        else:
            params['patterns'] = ['*']

    filelist = []
    skipped = {}

    def handle_walk_errors(e):
        if e.errno in (errno.EPERM, errno.EACCES, errno.ENOENT):
            skipped[e.filename] = to_text(e)
            return
        raise e

    if params['age'] is None:
        age = None
    else:
        # convert age to seconds:
        m = re.match(r"^(-?\d+)(s|m|h|d|w)?$", params['age'].lower())
        seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
        if m:
            age = int(m.group(1)) * seconds_per_unit.get(m.group(2), 1)
        else:
            module.fail_json(age=params['age'], msg="failed to process age")

    if params['size'] is None:
        size = None
    else:
        # convert size to bytes:
        m = re.match(r"^(-?\d+)(b|k|m|g|t)?$", params['size'].lower())
        bytes_per_unit = {"b": 1, "k": 1024, "m": 1024**2, "g": 1024**3, "t": 1024**4}
        if m:
            size = int(m.group(1)) * bytes_per_unit.get(m.group(2), 1)
        else:
            module.fail_json(size=params['size'], msg="failed to process size")

    if params['limit'] is not None and params['limit'] <= 0:
        module.fail_json(msg="limit cannot be %d (use None for unlimited)" % params['limit'])

    now = time.time()
    msg = 'All paths examined'
    looked = 0
    has_warnings = False
    for npath in params['paths']:
        try:
            if not os.path.isdir(npath):
                raise Exception("'%s' is not a directory" % to_native(npath))

            # Setting `topdown=True` to explicitly guarantee matches are made from the shallowest directory first
            for root, dirs, files in os.walk(npath, onerror=handle_walk_errors, followlinks=params['follow'], topdown=True):
                looked = looked + len(files) + len(dirs)
                for fsobj in (files + dirs):
                    fsname = os.path.normpath(os.path.join(root, fsobj))
                    if params['depth']:
                        wpath = npath.rstrip(os.path.sep) + os.path.sep
                        depth = int(fsname.count(os.path.sep)) - int(wpath.count(os.path.sep)) + 1
                        if depth > params['depth']:
                            # Empty the list used by os.walk to avoid traversing deeper unnecessarily
                            del dirs[:]
                            continue
                    if os.path.basename(fsname).startswith('.') and not params['hidden']:
                        continue

                    try:
                        st = os.lstat(fsname)
                    except OSError as ex:
                        module.error_as_warning(f"Skipped entry {fsname!r} due to access issue.", exception=ex)
                        skipped[fsname] = str(ex)
                        has_warnings = True
                        continue

                    r = {'path': fsname}
                    if params['file_type'] == 'any':
                        if (pfilter(fsobj, params['patterns'], params['excludes'], params['use_regex']) and
                                agefilter(st, now, age, params['age_stamp']) and
                                mode_filter(st, params['mode'], params['exact_mode'], module)):

                            r.update(statinfo(st))
                            if stat.S_ISREG(st.st_mode) and params['get_checksum']:
                                r['checksum'] = module.digest_from_file(fsname, params['checksum_algorithm'])

                            if stat.S_ISREG(st.st_mode):
                                if sizefilter(st, size):
                                    filelist.append(r)
                            else:
                                filelist.append(r)

                    elif stat.S_ISDIR(st.st_mode) and params['file_type'] == 'directory':
                        if (pfilter(fsobj, params['patterns'], params['excludes'], params['use_regex']) and
                                agefilter(st, now, age, params['age_stamp']) and
                                mode_filter(st, params['mode'], params['exact_mode'], module)):

                            r.update(statinfo(st))
                            filelist.append(r)

                    elif stat.S_ISREG(st.st_mode) and params['file_type'] == 'file':
                        if (pfilter(fsobj, params['patterns'], params['excludes'], params['use_regex']) and
                                agefilter(st, now, age, params['age_stamp']) and
                                sizefilter(st, size) and
                                contentfilter(fsname, params['contains'], params['encoding'], params['read_whole_file']) and
                                mode_filter(st, params['mode'], params['exact_mode'], module)):

                            r.update(statinfo(st))
                            if params['get_checksum']:
                                r['checksum'] = module.digest_from_file(fsname, params['checksum_algorithm'])
                            filelist.append(r)

                    elif stat.S_ISLNK(st.st_mode) and params['file_type'] == 'link':
                        if (pfilter(fsobj, params['patterns'], params['excludes'], params['use_regex']) and
                                agefilter(st, now, age, params['age_stamp']) and
                                mode_filter(st, params['mode'], params['exact_mode'], module)):

                            r.update(statinfo(st))
                            filelist.append(r)

                    if len(filelist) == params["limit"]:
                        # Breaks out of directory files loop only
                        msg = "Limit of matches reached"
                        break

                if not params['recurse'] or len(filelist) == params["limit"]:
                    break
        except Exception as e:
            skipped[npath] = to_text(e)
            module.warn("Skipped '%s' path due to this access issue: %s\n" % (to_text(npath), skipped[npath]))
            has_warnings = True

    if has_warnings:
        msg = 'Not all paths examined, check warnings for details'
    matched = len(filelist)
    module.exit_json(files=filelist, changed=False, msg=msg, matched=matched, examined=looked, skipped_paths=skipped)


if __name__ == '__main__':
    main()
