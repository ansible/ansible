# Copyright (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.module_utils.common.file import is_executable


def get_bin_path(arg, required=False, opt_dirs=None):
    '''
    find system executable in PATH.
    Optional arguments:
       - required:  if executable is not found and required is true it produces an Exception
       - opt_dirs:  optional list of directories to search in addition to PATH
    if found return full path; otherwise return None
    '''
    opt_dirs = [] if opt_dirs is None else opt_dirs

    sbin_paths = ['/sbin', '/usr/sbin', '/usr/local/sbin']
    paths = []
    for d in opt_dirs:
        if d is not None and os.path.exists(d):
            paths.append(d)
    paths += os.environ.get('PATH', '').split(os.pathsep)
    bin_path = None
    # mangle PATH to include /sbin dirs
    for p in sbin_paths:
        if p not in paths and os.path.exists(p):
            paths.append(p)
    for d in paths:
        if not d:
            continue
        path = os.path.join(d, arg)
        if os.path.exists(path) and not os.path.isdir(path) and is_executable(path):
            bin_path = path
            break
    if required and bin_path is None:
        raise ValueError('Failed to find required executable %s in paths: %s' % (arg, os.pathsep.join(paths)))

    return bin_path
