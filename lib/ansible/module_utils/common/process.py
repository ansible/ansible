# Copyright (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import os

from ansible.module_utils.common.file import is_executable


def get_bin_path(arg, opt_dirs=None):
    """
    Find system executable in PATH. Raises ValueError if the executable is not found.

    :param arg: the executable to find
    :type arg: string
    :param opt_dirs: optional list of directories to search in addition to PATH
    :type opt_dirs: list of strings
    :returns: path to arg (should be absolute path unless PATH or opt_dirs are relative paths)
    :raises: ValueError: if arg is not found

    In addition to PATH and opt_dirs, this function also looks through /sbin, /usr/sbin and /usr/local/sbin. A lot of
    modules, especially for gathering facts, depend on this behaviour.
    """
    paths = []
    sbin_paths = ['/sbin', '/usr/sbin', '/usr/local/sbin']
    opt_dirs = [] if opt_dirs is None else opt_dirs

    # Construct possible paths with precedence
    # passed in paths
    for d in opt_dirs:
        if d is not None and os.path.exists(d):
            paths.append(d)
    # system configured paths
    paths += os.environ.get('PATH', '').split(os.pathsep)

    # existing /sbin dirs, if not there already
    for p in sbin_paths:
        if p not in paths and os.path.exists(p):
            paths.append(p)

    # Search for binary
    bin_path = None
    for d in paths:
        if not d:
            continue
        path = os.path.join(d, arg)
        if os.path.exists(path) and not os.path.isdir(path) and is_executable(path):
            # fist found wins
            bin_path = path
            break

    if bin_path is None:
        raise ValueError('Failed to find required executable "%s" in paths: %s' % (arg, os.pathsep.join(paths)))

    return bin_path
