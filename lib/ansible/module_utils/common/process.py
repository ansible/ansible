# Copyright (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import os

from ansible.module_utils.common.file import is_executable
from ansible.module_utils.common.warnings import deprecate


def get_bin_path(arg, opt_dirs=None, required=None):
    '''
    Find system executable in PATH. Raises ValueError if the executable is not found.
    Optional arguments:
       - required:  [Deprecated] Before 2.10, if executable is not found and required is true it raises an Exception.
                    In 2.10 and later, an Exception is always raised. This parameter will be removed in 2.21.
       - opt_dirs:  optional list of directories to search in addition to PATH
    In addition to PATH and opt_dirs, this function also looks through /sbin, /usr/sbin and /usr/local/sbin. A lot of
    modules, especially for gathering facts, depend on this behaviour.
    If found return full path, otherwise raise ValueError.
    '''
    if required is not None:
        deprecate(
            msg="The `required` parameter in `get_bin_path` API is deprecated.",
            version="2.21",
            collection_name="ansible.builtin",
        )

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
    if bin_path is None:
        raise ValueError('Failed to find required executable "%s" in paths: %s' % (arg, os.pathsep.join(paths)))

    return bin_path
